"""
Admin routes for system administration.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, validate, ValidationError
from app.models import db, User, Wiki, Page
from app.tasks import enqueue_page_embedding
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


def require_admin(func):
    """Decorator to require admin privileges."""
    def wrapper(*args, **kwargs):
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        if not user or not user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper


class UserUpdateSchema(Schema):
    display_name = fields.Str(validate=validate.Length(max=120))
    email = fields.Email()
    is_active = fields.Bool()
    is_admin = fields.Bool()
    is_approved = fields.Bool()


user_update_schema = UserUpdateSchema()


@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@require_admin
def list_users():
    """Get all users with statistics."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '').strip()
    
    query = User.query
    
    # Search filter
    if search:
        search_term = f'%{search}%'
        query = query.filter(
            db.or_(
                User.username.ilike(search_term),
                User.email.ilike(search_term),
                User.display_name.ilike(search_term)
            )
        )
    
    # Get total count
    total = query.count()
    
    # Paginate
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get statistics for each user
    user_list = []
    for user in users.items:
        # Count owned wikis
        owned_wikis_count = user.owned_wikis.count()
        
        # Count pages created
        pages_created_count = user.pages_created.count()
        
        user_list.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'display_name': user.display_name,
            'avatar_url': user.avatar_url,
            'is_active': user.is_active,
            'is_admin': user.is_admin,
            'is_approved': user.is_approved,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'stats': {
                'owned_wikis': owned_wikis_count,
                'pages_created': pages_created_count,
            }
        })
    
    return jsonify({
        'users': user_list,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': users.pages
        }
    }), 200


@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
@require_admin
def get_user(user_id):
    """Get detailed user information."""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Get detailed stats
    owned_wikis = user.owned_wikis.all()
    pages_created = user.pages_created.count()
    
    return jsonify({
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'display_name': user.display_name,
            'avatar_url': user.avatar_url,
            'is_active': user.is_active,
            'is_admin': user.is_admin,
            'is_approved': user.is_approved,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'updated_at': user.updated_at.isoformat() if user.updated_at else None,
            'stats': {
                'owned_wikis': len(owned_wikis),
                'pages_created': pages_created,
            },
            'owned_wikis': [{'id': w.id, 'name': w.name} for w in owned_wikis]
        }
    }), 200


@admin_bp.route('/users/<int:user_id>', methods=['PATCH'])
@jwt_required()
@require_admin
def update_user(user_id):
    """Update user information."""
    current_user_id = int(get_jwt_identity())
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    try:
        data = user_update_schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
    
    # Prevent admin from removing their own admin status
    if user_id == current_user_id and 'is_admin' in data and not data['is_admin']:
        return jsonify({'error': 'Cannot remove your own admin privileges'}), 400
    
    # Update fields
    if 'display_name' in data:
        user.display_name = data['display_name']
    if 'email' in data:
        # Check if email is already taken by another user
        existing = User.query.filter(User.email == data['email'], User.id != user_id).first()
        if existing:
            return jsonify({'error': 'Email already in use'}), 400
        user.email = data['email']
    if 'is_active' in data:
        user.is_active = data['is_active']
    if 'is_admin' in data:
        user.is_admin = data['is_admin']
    if 'is_approved' in data:
        user.is_approved = data['is_approved']
    
    db.session.commit()
    
    return jsonify({
        'message': 'User updated successfully',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'display_name': user.display_name,
            'is_active': user.is_active,
            'is_admin': user.is_admin,
            'is_approved': user.is_approved
        }
    }), 200


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
@require_admin
def delete_user(user_id):
    """Delete a user (soft delete by deactivating)."""
    current_user_id = int(get_jwt_identity())
    
    # Prevent self-deletion
    if user_id == current_user_id:
        return jsonify({'error': 'Cannot delete your own account'}), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Soft delete - just deactivate
    user.is_active = False
    db.session.commit()
    
    return jsonify({'message': 'User deactivated successfully'}), 200


@admin_bp.route('/pending-users', methods=['GET'])
@jwt_required()
@require_admin
def list_pending_users():
    """Get all users pending approval."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    query = User.query.filter_by(is_approved=False)
    
    # Get total count
    total = query.count()
    
    # Paginate
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    user_list = []
    for user in users.items:
        user_list.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'display_name': user.display_name,
            'avatar_url': user.avatar_url,
            'created_at': user.created_at.isoformat() if user.created_at else None,
        })
    
    return jsonify({
        'users': user_list,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': users.pages
        }
    }), 200


@admin_bp.route('/users/<int:user_id>/approve', methods=['POST'])
@jwt_required()
@require_admin
def approve_user(user_id):
    """Approve a pending user."""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if user.is_approved:
        return jsonify({'error': 'User is already approved'}), 400
    
    user.is_approved = True
    db.session.commit()
    
    logger.info(f"Admin approved user {user_id} ({user.username})")
    
    return jsonify({
        'message': 'User approved successfully',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_approved': user.is_approved
        }
    }), 200


@admin_bp.route('/users/<int:user_id>/reject', methods=['POST'])
@jwt_required()
@require_admin
def reject_user(user_id):
    """Reject and delete a pending user."""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if user.is_approved:
        return jsonify({'error': 'Cannot reject an already approved user. Use delete instead.'}), 400
    
    username = user.username
    
    try:
        db.session.delete(user)
        db.session.commit()
        logger.info(f"Admin rejected and deleted pending user {user_id} ({username})")
        return jsonify({'message': f'User "{username}" rejected and deleted'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to reject user {user_id}: {e}")
        return jsonify({'error': f'Failed to reject user: {str(e)}'}), 500


@admin_bp.route('/stats', methods=['GET'])
@jwt_required()
@require_admin
def get_stats():
    """Get system-wide statistics."""
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    admin_users = User.query.filter_by(is_admin=True).count()
    pending_users = User.query.filter_by(is_approved=False).count()
    
    total_wikis = Wiki.query.count()
    public_wikis = Wiki.query.filter_by(is_public=True).count()
    
    total_pages = Page.query.count()
    pages_pending_embeddings = Page.query.filter(
        db.or_(
            Page.embeddings_status == 'pending',
            Page.embeddings_status == 'failed'
        )
    ).count()
    
    return jsonify({
        'stats': {
            'users': {
                'total': total_users,
                'active': active_users,
                'admins': admin_users,
                'pending_approval': pending_users
            },
            'wikis': {
                'total': total_wikis,
                'public': public_wikis
            },
            'pages': {
                'total': total_pages,
                'pending_embeddings': pages_pending_embeddings
            }
        }
    }), 200


@admin_bp.route('/embeddings/pending', methods=['GET'])
@jwt_required()
@require_admin
def list_pending_embeddings():
    """Get all pages without embeddings."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    status_filter = request.args.get('status', 'all')  # all, pending, failed, processing
    
    query = Page.query
    
    # Filter by status
    if status_filter == 'pending':
        query = query.filter_by(embeddings_status='pending')
    elif status_filter == 'failed':
        query = query.filter_by(embeddings_status='failed')
    elif status_filter == 'processing':
        query = query.filter_by(embeddings_status='processing')
    elif status_filter == 'all':
        query = query.filter(
            db.or_(
                Page.embeddings_status == 'pending',
                Page.embeddings_status == 'failed',
                Page.embeddings_status == 'processing'
            )
        )
    
    # Get total count
    total = query.count()
    
    # Paginate
    pages = query.order_by(Page.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Format results
    page_list = []
    for p in pages.items:
        page_list.append({
            'id': p.id,
            'title': p.title,
            'wiki_id': p.wiki_id,
            'wiki_name': p.wiki.name if p.wiki else None,
            'embeddings_status': p.embeddings_status,
            'created_at': p.created_at.isoformat() if p.created_at else None,
            'updated_at': p.updated_at.isoformat() if p.updated_at else None,
        })
    
    return jsonify({
        'pages': page_list,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': pages.pages
        }
    }), 200


@admin_bp.route('/embeddings/generate/<int:page_id>', methods=['POST'])
@jwt_required()
@require_admin
def generate_page_embedding(page_id):
    """Manually trigger embedding generation for a specific page."""
    page = Page.query.get(page_id)
    if not page:
        return jsonify({'error': 'Page not found'}), 404
    
    try:
        # Reset status and enqueue
        page.embeddings_status = 'pending'
        db.session.commit()
        
        job = enqueue_page_embedding(page_id, force_regenerate=True)
        logger.info(f"Admin triggered embedding for page {page_id}, job: {job.id if job else 'None'}")
        
        return jsonify({
            'message': 'Embedding generation queued',
            'page_id': page_id,
            'job_id': job.id if job else None
        }), 200
    except Exception as e:
        logger.error(f"Failed to enqueue embedding for page {page_id}: {e}")
        return jsonify({'error': f'Failed to queue embedding: {str(e)}'}), 500


@admin_bp.route('/embeddings/generate-all', methods=['POST'])
@jwt_required()
@require_admin
def generate_all_embeddings():
    """Trigger embedding generation for all pages without embeddings."""
    status_filter = request.get_json().get('status', 'pending')  # pending, failed, all
    
    query = Page.query
    
    if status_filter == 'pending':
        query = query.filter_by(embeddings_status='pending')
    elif status_filter == 'failed':
        query = query.filter_by(embeddings_status='failed')
    elif status_filter == 'all':
        query = query.filter(
            db.or_(
                Page.embeddings_status == 'pending',
                Page.embeddings_status == 'failed'
            )
        )
    
    pages = query.all()
    
    queued_count = 0
    failed_count = 0
    
    for page in pages:
        try:
            page.embeddings_status = 'pending'
            db.session.commit()
            
            job = enqueue_page_embedding(page.id, force_regenerate=True)
            if job:
                queued_count += 1
            else:
                failed_count += 1
        except Exception as e:
            logger.error(f"Failed to enqueue embedding for page {page.id}: {e}")
            failed_count += 1
    
    logger.info(f"Admin triggered bulk embedding: {queued_count} queued, {failed_count} failed")
    
    return jsonify({
        'message': 'Bulk embedding generation initiated',
        'queued': queued_count,
        'failed': failed_count,
        'total': len(pages)
    }), 200


@admin_bp.route('/wikis', methods=['GET'])
@jwt_required()
@require_admin
def list_wikis():
    """Get all wikis with owner and statistics."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '').strip()
    group_by = request.args.get('group_by', 'none')  # none, owner
    
    query = Wiki.query
    
    # Join User table if needed for grouping or search
    needs_user_join = group_by == 'owner' or search
    if needs_user_join and search:
        search_term = f'%{search}%'
        query = query.join(User).filter(
            db.or_(
                Wiki.name.ilike(search_term),
                Wiki.description.ilike(search_term),
                User.username.ilike(search_term),
                User.display_name.ilike(search_term)
            )
        )
    elif needs_user_join:
        # Join User for ordering when grouping by owner
        query = query.join(User)
    
    # Get total count
    total = query.count()
    
    if group_by == 'owner':
        # Group wikis by owner
        wikis = query.order_by(User.username, Wiki.created_at.desc()).all()
        
        # Organize by owner
        owners_dict = {}
        for wiki in wikis:
            owner_id = wiki.owner_id
            if owner_id not in owners_dict:
                owners_dict[owner_id] = {
                    'owner': {
                        'id': wiki.owner.id,
                        'username': wiki.owner.username,
                        'display_name': wiki.owner.display_name or wiki.owner.username,
                        'email': wiki.owner.email
                    },
                    'wikis': []
                }
            
            owners_dict[owner_id]['wikis'].append({
                'id': wiki.id,
                'name': wiki.name,
                'description': wiki.description,
                'is_public': wiki.is_public,
                'created_at': wiki.created_at.isoformat() if wiki.created_at else None,
                'page_count': wiki.pages.count(),
                'member_count': len(wiki.members)
            })
        
        return jsonify({
            'owners': list(owners_dict.values()),
            'total_wikis': total
        }), 200
    else:
        # Paginate flat list
        wikis = query.order_by(Wiki.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        wiki_list = []
        for wiki in wikis.items:
            wiki_list.append({
                'id': wiki.id,
                'name': wiki.name,
                'description': wiki.description,
                'is_public': wiki.is_public,
                'created_at': wiki.created_at.isoformat() if wiki.created_at else None,
                'owner': {
                    'id': wiki.owner.id,
                    'username': wiki.owner.username,
                    'display_name': wiki.owner.display_name or wiki.owner.username
                },
                'stats': {
                    'pages': wiki.pages.count(),
                    'members': len(wiki.members)
                }
            })
        
        return jsonify({
            'wikis': wiki_list,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': wikis.pages
            }
        }), 200


@admin_bp.route('/wikis/<int:wiki_id>', methods=['DELETE'])
@jwt_required()
@require_admin
def delete_wiki(wiki_id):
    """Delete a wiki (admin only)."""
    wiki = Wiki.query.get(wiki_id)
    if not wiki:
        return jsonify({'error': 'Wiki not found'}), 404
    
    wiki_name = wiki.name
    
    try:
        db.session.delete(wiki)
        db.session.commit()
        logger.info(f"Admin deleted wiki {wiki_id} ({wiki_name})")
        return jsonify({'message': f'Wiki "{wiki_name}" deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to delete wiki {wiki_id}: {e}")
        return jsonify({'error': f'Failed to delete wiki: {str(e)}'}), 500


@admin_bp.route('/wikis/<int:wiki_id>/transfer', methods=['POST'])
@jwt_required()
@require_admin
def transfer_wiki_ownership(wiki_id):
    """Transfer wiki ownership to another user."""
    wiki = Wiki.query.get(wiki_id)
    if not wiki:
        return jsonify({'error': 'Wiki not found'}), 404
    
    data = request.get_json()
    new_owner_id = data.get('owner_id')
    
    if not new_owner_id:
        return jsonify({'error': 'new_owner_id is required'}), 400
    
    new_owner = User.query.get(new_owner_id)
    if not new_owner:
        return jsonify({'error': 'New owner not found'}), 404
    
    old_owner_id = wiki.owner_id
    wiki.owner_id = new_owner_id
    
    db.session.commit()
    
    logger.info(f"Admin transferred wiki {wiki_id} from user {old_owner_id} to user {new_owner_id}")
    
    return jsonify({
        'message': 'Wiki ownership transferred successfully',
        'wiki': {
            'id': wiki.id,
            'name': wiki.name,
            'new_owner': {
                'id': new_owner.id,
                'username': new_owner.username
            }
        }
    }), 200
