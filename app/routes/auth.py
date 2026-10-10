from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.models import db, User, Wiki

# Sign-in is through authentik only (app/routes/oidc.py); there is no password
# login, registration or password change.
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh an access token."""
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    if not user or not user.is_active:
        return jsonify({'error': 'Invalid user'}), 401
    
    access_token = create_access_token(identity=str(current_user_id))
    return jsonify({'access_token': access_token}), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current authenticated user's profile."""
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({'user': user.to_dict(include_email=True)}), 200


@auth_bp.route('/me', methods=['PATCH'])
@jwt_required()
def update_current_user():
    """Update current user's profile."""
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    # Update allowed fields
    if 'display_name' in data:
        user.display_name = data['display_name']
    if 'avatar_url' in data:
        user.avatar_url = data['avatar_url']
    
    db.session.commit()
    return jsonify({'user': user.to_dict(include_email=True)}), 200


@auth_bp.route('/me', methods=['DELETE'])
@jwt_required()
def delete_account():
    """
    Delete the current user's account.
    
    JSON body:
    - delete_wikis: bool - if True, delete all owned wikis; if False, keep wikis as orphaned
    """
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json() or {}
    delete_wikis = data.get('delete_wikis', False)
    
    # Handle wikis
    owned_wikis = Wiki.query.filter_by(owner_id=current_user_id).all()
    
    if delete_wikis:
        # Delete all owned wikis (cascade will handle pages, attachments, etc.)
        for wiki in owned_wikis:
            db.session.delete(wiki)
    else:
        # Keep wikis but they become orphaned (owner_id will be null or transferred)
        # For now, we'll just leave them as-is since they have a foreign key constraint
        # In production, you might want to transfer ownership to an admin or system account
        # Or make owner_id nullable and set it to None
        pass
    
    # Delete the user account
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({
        'message': 'Account deleted successfully',
        'wikis_deleted': delete_wikis,
        'wikis_count': len(owned_wikis)
    }), 200
