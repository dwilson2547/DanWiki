from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, validate, ValidationError
from slugify import slugify
from app.models import db, User, Wiki, Page, PageRevision
from app.tasks import enqueue_page_embedding
import logging

logger = logging.getLogger(__name__)

pages_bp = Blueprint('pages', __name__, url_prefix='/api/wikis/<int:wiki_id>/pages')


class PageSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=1, max=300))
    content = fields.Str(load_default='')
    summary = fields.Str(validate=validate.Length(max=500))
    parent_id = fields.Int(allow_none=True)
    is_published = fields.Bool(load_default=True)
    sort_order = fields.Int(load_default=0)
    slug = fields.Str(validate=validate.Length(max=320))


class PageUpdateSchema(Schema):
    title = fields.Str(validate=validate.Length(min=1, max=300))
    content = fields.Str()
    summary = fields.Str(validate=validate.Length(max=500))
    parent_id = fields.Int(allow_none=True)
    is_published = fields.Bool()
    sort_order = fields.Int()
    slug = fields.Str(validate=validate.Length(max=320))
    change_summary = fields.Str(validate=validate.Length(max=500))


page_schema = PageSchema()
page_update_schema = PageUpdateSchema()


def generate_unique_slug(wiki_id: int, base_title: str, parent_id: int = None, exclude_page_id: int = None) -> str:
    """Generate a unique slug for a page within a wiki.
    
    Note: Slugs must be unique across the entire wiki, not just within the same parent,
    due to the database constraint on (wiki_id, slug).
    
    Args:
        wiki_id: The wiki ID
        base_title: The title to generate slug from
        parent_id: Optional parent page ID (not used for uniqueness check, kept for API compatibility)
        exclude_page_id: Optional page ID to exclude from uniqueness check (for updates)
    
    Returns:
        A unique slug string
    """
    base_slug = slugify(base_title)
    slug = base_slug
    counter = 1
    
    # Check if slug already exists anywhere in this wiki
    while True:
        query = Page.query.filter_by(wiki_id=wiki_id, slug=slug)
        if exclude_page_id:
            query = query.filter(Page.id != exclude_page_id)
        
        if not query.first():
            break
            
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    return slug


def check_wiki_access(wiki_id: int, user_id: int, require_edit: bool = False) -> tuple[Wiki | None, str | None]:
    """Check if user has access to a wiki. Returns (wiki, error_message)."""
    wiki = Wiki.query.get(wiki_id)
    if not wiki:
        return None, 'Wiki not found'
    
    user = User.query.get(user_id)
    if not user:
        return None, 'User not found'
    
    # Owner always has access
    if wiki.owner_id == user_id:
        return wiki, None
    
    # System admin always has access
    if user.is_admin:
        return wiki, None
    
    role = user.get_wiki_role(wiki_id)
    
    if wiki.is_public and not require_edit:
        return wiki, None
    
    if not role:
        return None, 'Access denied'
    
    if require_edit and role == 'viewer':
        return None, 'Permission denied'
    
    return wiki, None


@pages_bp.route('', methods=['GET'])
@jwt_required()
def list_pages(wiki_id):
    """List all pages in a wiki, optionally as a tree structure."""
    current_user_id = int(get_jwt_identity())
    wiki, error = check_wiki_access(wiki_id, current_user_id)
    
    if error:
        status = 404 if 'not found' in error else 403
        return jsonify({'error': error}), status
    
    structure = request.args.get('structure', 'flat')  # flat or tree
    
    if structure == 'tree':
        # Return hierarchical structure starting from root pages
        root_pages = wiki.get_root_pages().all()
        return jsonify({
            'pages': [p.to_dict(include_children=True) for p in root_pages],
            'count': wiki.pages.count()
        }), 200
    else:
        # Return flat list
        pages = wiki.pages.order_by(Page.title).all()
        return jsonify({
            'pages': [p.to_dict() for p in pages],
            'count': len(pages)
        }), 200


@pages_bp.route('', methods=['POST'])
@jwt_required()
def create_page(wiki_id):
    """Create a new page in a wiki."""
    current_user_id = int(get_jwt_identity())
    wiki, error = check_wiki_access(wiki_id, current_user_id, require_edit=True)
    
    if error:
        status = 404 if 'not found' in error else 403
        return jsonify({'error': error}), status
    
    try:
        data = page_schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
    
    # Validate parent_id if provided
    parent_id = data.get('parent_id')
    if parent_id:
        parent = Page.query.filter_by(id=parent_id, wiki_id=wiki_id).first()
        if not parent:
            return jsonify({'error': 'Parent page not found in this wiki'}), 404
    
    # Generate unique slug (use provided slug if given, otherwise generate from title)
    base_title = data.get('slug') or data['title']
    slug = generate_unique_slug(wiki_id, base_title, parent_id)
    
    page = Page(
        title=data['title'],
        slug=slug,
        content=data.get('content', ''),
        summary=data.get('summary'),
        parent_id=parent_id,
        is_published=data.get('is_published', True),
        sort_order=data.get('sort_order', 0),
        wiki_id=wiki_id,
        created_by_id=current_user_id,
        last_modified_by_id=current_user_id,
        embeddings_status='pending'  # Initialize embedding status
    )
    
    db.session.add(page)
    db.session.commit()
    
    # Enqueue embedding generation task
    try:
        job = enqueue_page_embedding(page.id)
        logger.info(f"Enqueued embedding task for page {page.id}, job: {job.id}")
    except Exception as e:
        logger.error(f"Failed to enqueue embedding task for page {page.id}: {e}")
        # Don't fail the request if task queue fails
    
    return jsonify({
        'message': 'Page created successfully',
        'page': page.to_dict(include_content=True)
    }), 201


@pages_bp.route('/<int:page_id>', methods=['GET'])
@jwt_required()
def get_page(wiki_id, page_id):
    """Get a specific page."""
    current_user_id = int(get_jwt_identity())
    wiki, error = check_wiki_access(wiki_id, current_user_id)
    
    if error:
        status = 404 if 'not found' in error else 403
        return jsonify({'error': error}), status
    
    page = Page.query.filter_by(id=page_id, wiki_id=wiki_id).first()
    if not page:
        return jsonify({'error': 'Page not found'}), 404
    
    include_children = request.args.get('include_children', 'false').lower() == 'true'
    return jsonify({'page': page.to_dict(include_content=True, include_children=include_children)}), 200


@pages_bp.route('/by-path/<path:page_path>', methods=['GET'])
@jwt_required()
def get_page_by_path(wiki_id, page_path):
    """Get a page by its path (e.g., 'parent-slug/child-slug')."""
    current_user_id = int(get_jwt_identity())
    wiki, error = check_wiki_access(wiki_id, current_user_id)
    
    if error:
        status = 404 if 'not found' in error else 403
        return jsonify({'error': error}), status
    
    slugs = page_path.split('/')
    current_parent_id = None
    page = None
    
    for slug in slugs:
        page = Page.query.filter_by(
            wiki_id=wiki_id,
            slug=slug,
            parent_id=current_parent_id
        ).first()
        if not page:
            return jsonify({'error': f'Page not found at path: {page_path}'}), 404
        current_parent_id = page.id
    
    include_children = request.args.get('include_children', 'false').lower() == 'true'
    return jsonify({'page': page.to_dict(include_content=True, include_children=include_children)}), 200


@pages_bp.route('/<int:page_id>', methods=['PATCH'])
@jwt_required()
def update_page(wiki_id, page_id):
    """Update a page."""
    current_user_id = int(get_jwt_identity())
    wiki, error = check_wiki_access(wiki_id, current_user_id, require_edit=True)
    
    if error:
        status = 404 if 'not found' in error else 403
        return jsonify({'error': error}), status
    
    page = Page.query.filter_by(id=page_id, wiki_id=wiki_id).first()
    if not page:
        return jsonify({'error': 'Page not found'}), 404
    
    try:
        data = page_update_schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
    
    # Create revision before updating (if content changed)
    if 'content' in data and data['content'] != page.content:
        # Get next revision number
        last_revision = PageRevision.query.filter_by(page_id=page_id)\
            .order_by(PageRevision.revision_number.desc()).first()
        next_revision = (last_revision.revision_number + 1) if last_revision else 1
        
        revision = PageRevision(
            page_id=page_id,
            title=page.title,
            content=page.content,
            revision_number=next_revision,
            created_by_id=current_user_id,
            change_summary=data.get('change_summary', 'Content updated')
        )
        db.session.add(revision)
    
    # Update fields
    if 'title' in data:
        page.title = data['title']
    if 'content' in data:
        page.content = data['content']
    if 'summary' in data:
        page.summary = data['summary']
    if 'is_published' in data:
        page.is_published = data['is_published']
    if 'sort_order' in data:
        page.sort_order = data['sort_order']
    if 'slug' in data:
        # Generate unique slug if the requested one conflicts
        new_slug = generate_unique_slug(wiki_id, data['slug'], page.parent_id, exclude_page_id=page_id)
        page.slug = new_slug
    
    # Handle parent change
    if 'parent_id' in data:
        new_parent_id = data['parent_id']
        if new_parent_id:
            # Validate parent exists in this wiki
            parent = Page.query.filter_by(id=new_parent_id, wiki_id=wiki_id).first()
            if not parent:
                return jsonify({'error': 'Parent page not found'}), 404
            # Check for circular reference
            try:
                page.move_to_parent(parent)
            except ValueError as e:
                return jsonify({'error': str(e)}), 400
        else:
            page.parent_id = None
    
    page.last_modified_by_id = current_user_id
    
    # Track if content changed to decide whether to regenerate embeddings
    content_changed = 'content' in data or 'title' in data
    
    db.session.commit()
    
    # Enqueue embedding regeneration if content changed
    if content_changed:
        try:
            page.embeddings_status = 'pending'
            db.session.commit()
            job = enqueue_page_embedding(page.id, force_regenerate=True)
            logger.info(f"Enqueued embedding regeneration for page {page.id}, job: {job.id}")
        except Exception as e:
            logger.error(f"Failed to enqueue embedding task for page {page.id}: {e}")
            # Don't fail the request if task queue fails
    
    return jsonify({'page': page.to_dict(include_content=True)}), 200


@pages_bp.route('/<int:page_id>', methods=['DELETE'])
@jwt_required()
def delete_page(wiki_id, page_id):
    """Delete a page and all its children."""
    current_user_id = int(get_jwt_identity())
    wiki, error = check_wiki_access(wiki_id, current_user_id, require_edit=True)
    
    if error:
        status = 404 if 'not found' in error else 403
        return jsonify({'error': error}), status
    
    page = Page.query.filter_by(id=page_id, wiki_id=wiki_id).first()
    if not page:
        return jsonify({'error': 'Page not found'}), 404
    
    # Count descendants that will be deleted
    descendants = page.get_descendants()
    total_deleted = len(descendants) + 1
    
    db.session.delete(page)
    db.session.commit()
    
    return jsonify({
        'message': f'Page and {len(descendants)} child pages deleted',
        'deleted_count': total_deleted
    }), 200


@pages_bp.route('/<int:page_id>/move', methods=['POST'])
@jwt_required()
def move_page(wiki_id, page_id):
    """Move a page to a new parent."""
    current_user_id = int(get_jwt_identity())
    wiki, error = check_wiki_access(wiki_id, current_user_id, require_edit=True)
    
    if error:
        status = 404 if 'not found' in error else 403
        return jsonify({'error': error}), status
    
    page = Page.query.filter_by(id=page_id, wiki_id=wiki_id).first()
    if not page:
        return jsonify({'error': 'Page not found'}), 404
    
    data = request.get_json()
    new_parent_id = data.get('parent_id')  # null for root level
    
    if new_parent_id:
        new_parent = Page.query.filter_by(id=new_parent_id, wiki_id=wiki_id).first()
        if not new_parent:
            return jsonify({'error': 'New parent page not found'}), 404
        try:
            page.move_to_parent(new_parent)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
    else:
        page.parent_id = None
    
    # Update sort order if provided
    if 'sort_order' in data:
        page.sort_order = data['sort_order']
    
    page.last_modified_by_id = current_user_id
    db.session.commit()
    
    return jsonify({'page': page.to_dict()}), 200


@pages_bp.route('/<int:page_id>/children', methods=['GET'])
@jwt_required()
def get_page_children(wiki_id, page_id):
    """Get direct children of a page."""
    current_user_id = int(get_jwt_identity())
    wiki, error = check_wiki_access(wiki_id, current_user_id)
    
    if error:
        status = 404 if 'not found' in error else 403
        return jsonify({'error': error}), status
    
    page = Page.query.filter_by(id=page_id, wiki_id=wiki_id).first()
    if not page:
        return jsonify({'error': 'Page not found'}), 404
    
    children = page.children.all()
    return jsonify({
        'children': [c.to_dict() for c in children],
        'count': len(children)
    }), 200


@pages_bp.route('/<int:page_id>/revisions', methods=['GET'])
@jwt_required()
def get_page_revisions(wiki_id, page_id):
    """Get revision history for a page."""
    current_user_id = int(get_jwt_identity())
    wiki, error = check_wiki_access(wiki_id, current_user_id)
    
    if error:
        status = 404 if 'not found' in error else 403
        return jsonify({'error': error}), status
    
    page = Page.query.filter_by(id=page_id, wiki_id=wiki_id).first()
    if not page:
        return jsonify({'error': 'Page not found'}), 404
    
    revisions = PageRevision.query.filter_by(page_id=page_id)\
        .order_by(PageRevision.revision_number.desc()).all()
    
    return jsonify({
        'revisions': [r.to_dict() for r in revisions],
        'count': len(revisions)
    }), 200


@pages_bp.route('/<int:page_id>/revisions/<int:revision_id>', methods=['GET'])
@jwt_required()
def get_page_revision(wiki_id, page_id, revision_id):
    """Get a specific revision's content."""
    current_user_id = int(get_jwt_identity())
    wiki, error = check_wiki_access(wiki_id, current_user_id)
    
    if error:
        status = 404 if 'not found' in error else 403
        return jsonify({'error': error}), status
    
    revision = PageRevision.query.filter_by(id=revision_id, page_id=page_id).first()
    if not revision:
        return jsonify({'error': 'Revision not found'}), 404
    
    data = revision.to_dict()
    data['content'] = revision.content
    return jsonify({'revision': data}), 200


@pages_bp.route('/<int:page_id>/restore/<int:revision_id>', methods=['POST'])
@jwt_required()
def restore_revision(wiki_id, page_id, revision_id):
    """Restore a page to a previous revision."""
    current_user_id = int(get_jwt_identity())
    wiki, error = check_wiki_access(wiki_id, current_user_id, require_edit=True)
    
    if error:
        status = 404 if 'not found' in error else 403
        return jsonify({'error': error}), status
    
    page = Page.query.filter_by(id=page_id, wiki_id=wiki_id).first()
    if not page:
        return jsonify({'error': 'Page not found'}), 404
    
    revision = PageRevision.query.filter_by(id=revision_id, page_id=page_id).first()
    if not revision:
        return jsonify({'error': 'Revision not found'}), 404
    
    # Create a new revision for the current state
    last_revision = PageRevision.query.filter_by(page_id=page_id)\
        .order_by(PageRevision.revision_number.desc()).first()
    next_revision = (last_revision.revision_number + 1) if last_revision else 1
    
    current_revision = PageRevision(
        page_id=page_id,
        title=page.title,
        content=page.content,
        revision_number=next_revision,
        created_by_id=current_user_id,
        change_summary=f'Before restoring to revision {revision.revision_number}'
    )
    db.session.add(current_revision)
    
    # Restore the page
    page.title = revision.title
    page.content = revision.content
    page.last_modified_by_id = current_user_id
    
    db.session.commit()
    
    return jsonify({
        'message': f'Page restored to revision {revision.revision_number}',
        'page': page.to_dict(include_content=True)
    }), 200
