from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, validate, ValidationError
from app.models import db, User, Wiki, Page, Tag
import logging

logger = logging.getLogger(__name__)

tags_bp = Blueprint('tags', __name__, url_prefix='/api/wikis/<int:wiki_id>/tags')


class TagSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    color = fields.Str(validate=validate.Regexp(r'^#[0-9A-Fa-f]{6}$'))
    source = fields.Str(validate=validate.OneOf(['human', 'ai', 'automated', 'imported']))
    auto_generated = fields.Bool()
    confidence = fields.Float(validate=validate.Range(min=0.0, max=1.0))
    model_name = fields.Str(validate=validate.Length(max=100))
    verified = fields.Bool()


tag_schema = TagSchema()


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


@tags_bp.route('', methods=['GET'])
@jwt_required()
def list_tags(wiki_id):
    """List all tags for a wiki."""
    current_user_id = int(get_jwt_identity())
    wiki, error = check_wiki_access(wiki_id, current_user_id)
    
    if error:
        status = 404 if 'not found' in error else 403
        return jsonify({'error': error}), status
    
    tags = Tag.query.filter_by(wiki_id=wiki_id).order_by(Tag.name).all()
    return jsonify({
        'tags': [tag.to_dict() for tag in tags],
        'count': len(tags)
    }), 200


@tags_bp.route('', methods=['POST'])
@jwt_required()
def create_tag(wiki_id):
    """Create a new tag for a wiki."""
    current_user_id = int(get_jwt_identity())
    wiki, error = check_wiki_access(wiki_id, current_user_id, require_edit=True)
    
    if error:
        status = 404 if 'not found' in error else 403
        return jsonify({'error': error}), status
    
    try:
        data = tag_schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
    
    # Check if tag already exists
    existing = Tag.query.filter_by(wiki_id=wiki_id, name=data['name']).first()
    if existing:
        return jsonify({'error': 'Tag already exists in this wiki'}), 409
    
    tag = Tag(
        name=data['name'],
        color=data.get('color'),
        wiki_id=wiki_id,
        source=data.get('source', 'human'),  # Default to human-created
        auto_generated=data.get('auto_generated', False),
        confidence=data.get('confidence'),
        model_name=data.get('model_name'),
        verified=data.get('verified', False)
    )
    
    db.session.add(tag)
    db.session.commit()
    
    return jsonify({
        'message': 'Tag created successfully',
        'tag': tag.to_dict()
    }), 201


@tags_bp.route('/<int:tag_id>', methods=['DELETE'])
@jwt_required()
def delete_tag(wiki_id, tag_id):
    """Delete a tag from a wiki."""
    current_user_id = int(get_jwt_identity())
    wiki, error = check_wiki_access(wiki_id, current_user_id, require_edit=True)
    
    if error:
        status = 404 if 'not found' in error else 403
        return jsonify({'error': error}), status
    
    tag = Tag.query.filter_by(id=tag_id, wiki_id=wiki_id).first()
    if not tag:
        return jsonify({'error': 'Tag not found'}), 404
    
    db.session.delete(tag)
    db.session.commit()
    
    return jsonify({'message': 'Tag deleted successfully'}), 200


@tags_bp.route('/<int:tag_id>', methods=['PATCH'])
@jwt_required()
def update_tag(wiki_id, tag_id):
    """Update a tag."""
    current_user_id = int(get_jwt_identity())
    wiki, error = check_wiki_access(wiki_id, current_user_id, require_edit=True)
    
    if error:
        status = 404 if 'not found' in error else 403
        return jsonify({'error': error}), status
    
    tag = Tag.query.filter_by(id=tag_id, wiki_id=wiki_id).first()
    if not tag:
        return jsonify({'error': 'Tag not found'}), 404
    
    try:
        data = tag_schema.load(request.get_json(), partial=True)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
    
    if 'name' in data:
        # Check if new name conflicts with existing tag
        existing = Tag.query.filter_by(wiki_id=wiki_id, name=data['name']).filter(Tag.id != tag_id).first()
        if existing:
            return jsonify({'error': 'Tag name already exists in this wiki'}), 409
        tag.name = data['name']
    
    if 'color' in data:
        tag.color = data['color']
    
    if 'source' in data:
        tag.source = data['source']
    
    if 'auto_generated' in data:
        tag.auto_generated = data['auto_generated']
    
    if 'confidence' in data:
        tag.confidence = data['confidence']
    
    if 'model_name' in data:
        tag.model_name = data['model_name']
    
    if 'verified' in data:
        tag.verified = data['verified']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Tag updated successfully',
        'tag': tag.to_dict()
    }), 200


@tags_bp.route('/<int:tag_id>/verify', methods=['POST'])
@jwt_required()
def verify_tag(wiki_id, tag_id):
    """Mark a tag as verified by the current user."""
    from datetime import datetime, timezone
    
    current_user_id = int(get_jwt_identity())
    wiki, error = check_wiki_access(wiki_id, current_user_id, require_edit=True)
    
    if error:
        status = 404 if 'not found' in error else 403
        return jsonify({'error': error}), status
    
    tag = Tag.query.filter_by(id=tag_id, wiki_id=wiki_id).first()
    if not tag:
        return jsonify({'error': 'Tag not found'}), 404
    
    tag.verified = True
    tag.verified_by_id = current_user_id
    tag.verified_at = datetime.now(timezone.utc)
    
    db.session.commit()
    
    return jsonify({
        'message': 'Tag verified successfully',
        'tag': tag.to_dict()
    }), 200


# Page tag management routes
page_tags_bp = Blueprint('page_tags', __name__, url_prefix='/api/wikis/<int:wiki_id>/pages/<int:page_id>/tags')


@page_tags_bp.route('', methods=['GET'])
@jwt_required()
def get_page_tags(wiki_id, page_id):
    """Get all tags for a specific page."""
    current_user_id = int(get_jwt_identity())
    wiki, error = check_wiki_access(wiki_id, current_user_id)
    
    if error:
        status = 404 if 'not found' in error else 403
        return jsonify({'error': error}), status
    
    page = Page.query.filter_by(id=page_id, wiki_id=wiki_id).first()
    if not page:
        return jsonify({'error': 'Page not found'}), 404
    
    return jsonify({
        'tags': [tag.to_dict() for tag in page.tags]
    }), 200


@page_tags_bp.route('/<int:tag_id>', methods=['POST'])
@jwt_required()
def add_tag_to_page(wiki_id, page_id, tag_id):
    """Add a tag to a page."""
    current_user_id = int(get_jwt_identity())
    wiki, error = check_wiki_access(wiki_id, current_user_id, require_edit=True)
    
    if error:
        status = 404 if 'not found' in error else 403
        return jsonify({'error': error}), status
    
    page = Page.query.filter_by(id=page_id, wiki_id=wiki_id).first()
    if not page:
        return jsonify({'error': 'Page not found'}), 404
    
    tag = Tag.query.filter_by(id=tag_id, wiki_id=wiki_id).first()
    if not tag:
        return jsonify({'error': 'Tag not found'}), 404
    
    # Check if tag is already on the page
    if tag in page.tags:
        return jsonify({'error': 'Tag already added to this page'}), 409
    
    page.tags.append(tag)
    db.session.commit()
    
    return jsonify({
        'message': 'Tag added to page',
        'tags': [t.to_dict() for t in page.tags]
    }), 200


@page_tags_bp.route('/<int:tag_id>', methods=['DELETE'])
@jwt_required()
def remove_tag_from_page(wiki_id, page_id, tag_id):
    """Remove a tag from a page."""
    current_user_id = int(get_jwt_identity())
    wiki, error = check_wiki_access(wiki_id, current_user_id, require_edit=True)
    
    if error:
        status = 404 if 'not found' in error else 403
        return jsonify({'error': error}), status
    
    page = Page.query.filter_by(id=page_id, wiki_id=wiki_id).first()
    if not page:
        return jsonify({'error': 'Page not found'}), 404
    
    tag = Tag.query.filter_by(id=tag_id, wiki_id=wiki_id).first()
    if not tag:
        return jsonify({'error': 'Tag not found'}), 404
    
    # Check if tag is on the page
    if tag not in page.tags:
        return jsonify({'error': 'Tag not found on this page'}), 404
    
    page.tags.remove(tag)
    db.session.commit()
    
    return jsonify({
        'message': 'Tag removed from page',
        'tags': [t.to_dict() for t in page.tags]
    }), 200
