from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from flask_jwt_extended.exceptions import NoAuthorizationError
from marshmallow import Schema, fields, validate, ValidationError
from slugify import slugify
from sqlalchemy import func
from app.models import db, User, Wiki, wiki_members

wikis_bp = Blueprint('wikis', __name__, url_prefix='/api/wikis')


class WikiSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    description = fields.Str(validate=validate.Length(max=2000))
    is_public = fields.Bool(load_default=False)
    slug = fields.Str(validate=validate.Length(max=220))


class WikiMemberSchema(Schema):
    user_id = fields.Int(required=True)
    role = fields.Str(validate=validate.OneOf(['viewer', 'editor', 'admin']))


wiki_schema = WikiSchema()
member_schema = WikiMemberSchema()


def get_user_wikis(user_id: int):
    """Get all wikis a user has access to (owned or member)."""
    user = User.query.get(user_id)
    owned = Wiki.query.filter_by(owner_id=user_id).all()
    member_wikis = user.wikis if user else []
    
    # Combine and deduplicate
    all_wikis = {w.id: w for w in owned}
    for w in member_wikis:
        if w.id not in all_wikis:
            all_wikis[w.id] = w
    
    return list(all_wikis.values())


@wikis_bp.route('/public', methods=['GET'])
def list_public_wikis():
    """
    List all public wikis organized by author.
    No authentication required.
    
    Query params:
    - group_by: 'author' to group by owner (default), 'none' for flat list
    - search: filter by name or description
    - limit: max results per author (default 10)
    """
    group_by = request.args.get('group_by', 'author')
    search_term = request.args.get('search', '').strip()
    limit_per_author = min(request.args.get('limit', 10, type=int), 50)
    
    # Base query for public wikis
    query = Wiki.query.filter_by(is_public=True)
    
    # Apply search filter if provided
    if search_term:
        search_pattern = f'%{search_term}%'
        query = query.filter(
            db.or_(
                Wiki.name.ilike(search_pattern),
                Wiki.description.ilike(search_pattern)
            )
        )
    
    if group_by == 'author':
        # Get all public wikis with their owners
        wikis = query.order_by(Wiki.updated_at.desc()).all()
        
        # Group by author
        authors_dict = {}
        for wiki in wikis:
            owner_id = wiki.owner_id
            if owner_id not in authors_dict:
                authors_dict[owner_id] = {
                    'author': wiki.owner.to_dict(),
                    'wikis': []
                }
            if len(authors_dict[owner_id]['wikis']) < limit_per_author:
                authors_dict[owner_id]['wikis'].append(wiki.to_dict())
        
        # Convert to list and sort by number of wikis
        authors = list(authors_dict.values())
        authors.sort(key=lambda x: len(x['wikis']), reverse=True)
        
        return jsonify({
            'authors': authors,
            'total_authors': len(authors),
            'total_wikis': len(wikis)
        }), 200
    else:
        # Flat list
        wikis = query.order_by(Wiki.updated_at.desc()).limit(100).all()
        return jsonify({
            'wikis': [w.to_dict() for w in wikis],
            'count': len(wikis)
        }), 200


@wikis_bp.route('', methods=['GET'])
@jwt_required()
def list_wikis():
    """List all wikis the current user has access to."""
    current_user_id = int(get_jwt_identity())
    wikis = get_user_wikis(current_user_id)
    
    return jsonify({
        'wikis': [w.to_dict() for w in wikis],
        'count': len(wikis)
    }), 200


@wikis_bp.route('', methods=['POST'])
@jwt_required()
def create_wiki():
    """Create a new wiki."""
    current_user_id = int(get_jwt_identity())
    
    try:
        data = wiki_schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
    
    # Generate slug if not provided
    slug = data.get('slug') or slugify(data['name'])
    
    # Check for duplicate slug for this owner
    existing = Wiki.query.filter_by(owner_id=current_user_id, slug=slug).first()
    if existing:
        return jsonify({'error': 'You already have a wiki with this name/slug'}), 409
    
    wiki = Wiki(
        name=data['name'],
        slug=slug,
        description=data.get('description'),
        is_public=data.get('is_public', False),
        owner_id=current_user_id
    )
    
    db.session.add(wiki)
    db.session.commit()
    
    return jsonify({
        'message': 'Wiki created successfully',
        'wiki': wiki.to_dict()
    }), 201


@wikis_bp.route('/<int:wiki_id>', methods=['GET'])
@jwt_required()
def get_wiki(wiki_id):
    """Get a specific wiki by ID."""
    current_user_id = int(get_jwt_identity())
    wiki = Wiki.query.get(wiki_id)
    
    if not wiki:
        return jsonify({'error': 'Wiki not found'}), 404
    
    # Check access
    user = User.query.get(current_user_id)
    # Admins can access all wikis
    if not user.is_admin and not wiki.is_public and wiki.owner_id != current_user_id:
        if not user.get_wiki_role(wiki_id):
            return jsonify({'error': 'Access denied'}), 403
    
    include_pages = request.args.get('include_pages', 'false').lower() == 'true'
    return jsonify({'wiki': wiki.to_dict(include_pages=include_pages)}), 200


@wikis_bp.route('/<int:wiki_id>', methods=['PATCH'])
@jwt_required()
def update_wiki(wiki_id):
    """Update a wiki."""
    current_user_id = int(get_jwt_identity())
    wiki = Wiki.query.get(wiki_id)
    
    if not wiki:
        return jsonify({'error': 'Wiki not found'}), 404
    
    user = User.query.get(current_user_id)
    if not user.is_admin and not user.can_admin_wiki(wiki_id):
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.get_json()
    
    if 'name' in data:
        wiki.name = data['name']
        # Optionally update slug if name changed
        if data.get('update_slug', False):
            wiki.slug = slugify(data['name'])
    if 'description' in data:
        wiki.description = data['description']
    if 'is_public' in data:
        wiki.is_public = data['is_public']
    if 'slug' in data:
        # Check for conflicts
        existing = Wiki.query.filter_by(
            owner_id=wiki.owner_id, 
            slug=data['slug']
        ).first()
        if existing and existing.id != wiki_id:
            return jsonify({'error': 'Slug already in use'}), 409
        wiki.slug = data['slug']
    
    db.session.commit()
    return jsonify({'wiki': wiki.to_dict()}), 200


@wikis_bp.route('/<int:wiki_id>', methods=['DELETE'])
@jwt_required()
def delete_wiki(wiki_id):
    """Delete a wiki and all its pages."""
    current_user_id = int(get_jwt_identity())
    wiki = Wiki.query.get(wiki_id)
    
    if not wiki:
        return jsonify({'error': 'Wiki not found'}), 404
    
    # Only owner can delete
    if wiki.owner_id != current_user_id:
        user = User.query.get(current_user_id)
        if not user.is_admin:
            return jsonify({'error': 'Only the owner can delete a wiki'}), 403
    
    db.session.delete(wiki)
    db.session.commit()
    
    return jsonify({'message': 'Wiki deleted successfully'}), 200


# Member management endpoints
@wikis_bp.route('/<int:wiki_id>/members', methods=['GET'])
@jwt_required()
def list_members(wiki_id):
    """List all members of a wiki."""
    current_user_id = int(get_jwt_identity())
    wiki = Wiki.query.get(wiki_id)
    
    if not wiki:
        return jsonify({'error': 'Wiki not found'}), 404
    
    user = User.query.get(current_user_id)
    if not user.is_admin and wiki.owner_id != current_user_id and not user.get_wiki_role(wiki_id):
        return jsonify({'error': 'Access denied'}), 403
    
    # Get members with their roles
    members = db.session.execute(
        db.select(User, wiki_members.c.role, wiki_members.c.joined_at)
        .join(wiki_members, User.id == wiki_members.c.user_id)
        .where(wiki_members.c.wiki_id == wiki_id)
    ).all()
    
    members_list = [{
        **user.to_dict(),
        'role': role,
        'joined_at': joined_at.isoformat() if joined_at else None
    } for user, role, joined_at in members]
    
    # Add owner
    owner_data = wiki.owner.to_dict()
    owner_data['role'] = 'owner'
    
    return jsonify({
        'owner': owner_data,
        'members': members_list
    }), 200


@wikis_bp.route('/<int:wiki_id>/members', methods=['POST'])
@jwt_required()
def add_member(wiki_id):
    """Add a member to a wiki."""
    current_user_id = int(get_jwt_identity())
    wiki = Wiki.query.get(wiki_id)
    
    if not wiki:
        return jsonify({'error': 'Wiki not found'}), 404
    
    current_user = User.query.get(current_user_id)
    if not current_user.is_admin and not current_user.can_admin_wiki(wiki_id):
        return jsonify({'error': 'Permission denied'}), 403
    
    try:
        data = member_schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
    
    new_member = User.query.get(data['user_id'])
    if not new_member:
        return jsonify({'error': 'User not found'}), 404
    
    if new_member.id == wiki.owner_id:
        return jsonify({'error': 'Cannot add owner as member'}), 400
    
    # Check if already a member
    existing_role = new_member.get_wiki_role(wiki_id)
    if existing_role:
        return jsonify({'error': 'User is already a member'}), 409
    
    wiki.add_member(new_member, data.get('role', 'viewer'))
    db.session.commit()
    
    return jsonify({'message': 'Member added successfully'}), 201


@wikis_bp.route('/<int:wiki_id>/members/<int:user_id>', methods=['PATCH'])
@jwt_required()
def update_member(wiki_id, user_id):
    """Update a member's role."""
    current_user_id = int(get_jwt_identity())
    wiki = Wiki.query.get(wiki_id)
    
    if not wiki:
        return jsonify({'error': 'Wiki not found'}), 404
    
    current_user = User.query.get(current_user_id)
    if not current_user.is_admin and not current_user.can_admin_wiki(wiki_id):
        return jsonify({'error': 'Permission denied'}), 403
    
    member = User.query.get(user_id)
    if not member:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    role = data.get('role')
    
    if role not in ('viewer', 'editor', 'admin'):
        return jsonify({'error': 'Invalid role'}), 400
    
    wiki.update_member_role(member, role)
    db.session.commit()
    
    return jsonify({'message': 'Member role updated'}), 200


@wikis_bp.route('/<int:wiki_id>/members/<int:user_id>', methods=['DELETE'])
@jwt_required()
def remove_member(wiki_id, user_id):
    """Remove a member from a wiki."""
    current_user_id = int(get_jwt_identity())
    wiki = Wiki.query.get(wiki_id)
    
    if not wiki:
        return jsonify({'error': 'Wiki not found'}), 404
    
    current_user = User.query.get(current_user_id)
    # Allow self-removal, site admin, or wiki admin removal
    if user_id != current_user_id and not current_user.is_admin and not current_user.can_admin_wiki(wiki_id):
        return jsonify({'error': 'Permission denied'}), 403
    
    member = User.query.get(user_id)
    if not member:
        return jsonify({'error': 'User not found'}), 404
    
    wiki.remove_member(member)
    db.session.commit()
    
    return jsonify({'message': 'Member removed'}), 200
