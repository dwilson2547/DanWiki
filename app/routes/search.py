from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_, func, case
from app.models import db, User, Wiki, Page

search_bp = Blueprint('search', __name__, url_prefix='/api/search')


def get_accessible_wiki_ids(user_id: int) -> list[int]:
    """Get list of wiki IDs the user can access."""
    user = User.query.get(user_id)
    if not user:
        return []
    
    # Admins can access all wikis
    if user.is_admin:
        return [w.id for w in Wiki.query.all()]
    
    # Get owned wikis
    owned_ids = [w.id for w in user.owned_wikis]
    
    # Get member wikis
    member_ids = [w.id for w in user.wikis]
    
    # Get public wikis
    public_ids = [w.id for w in Wiki.query.filter_by(is_public=True).all()]
    
    # Combine and deduplicate
    return list(set(owned_ids + member_ids + public_ids))


@search_bp.route('/pages', methods=['GET'])
@jwt_required()
def search_pages():
    """
    Search pages across all accessible wikis.
    
    Query params:
    - q: search query (required)
    - wiki_id: limit to specific wiki (optional)
    - limit: max results (default 20)
    - offset: pagination offset (default 0)
    """
    current_user_id = int(get_jwt_identity())
    
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'error': 'Search query required'}), 400
    
    wiki_id = request.args.get('wiki_id', type=int)
    limit = min(request.args.get('limit', 20, type=int), 100)
    offset = request.args.get('offset', 0, type=int)
    
    # Get accessible wikis
    accessible_wiki_ids = get_accessible_wiki_ids(current_user_id)
    
    if not accessible_wiki_ids:
        return jsonify({'pages': [], 'total': 0}), 200
    
    # If specific wiki requested, verify access
    if wiki_id:
        if wiki_id not in accessible_wiki_ids:
            return jsonify({'error': 'Wiki not accessible'}), 403
        accessible_wiki_ids = [wiki_id]
    
    # Build search query
    # Basic keyword search - can be enhanced with full-text search or embeddings later
    search_term = f'%{query}%'
    
    base_query = Page.query.filter(
        Page.wiki_id.in_(accessible_wiki_ids),
        Page.is_published == True,
        or_(
            Page.title.ilike(search_term),
            Page.content.ilike(search_term),
            Page.summary.ilike(search_term)
        )
    )
    
    # Get total count
    total = base_query.count()
    
    # Get results with pagination
    pages = base_query.order_by(
        # Prioritize title matches
        case(
            (Page.title.ilike(search_term), 0),
            else_=1
        ),
        Page.updated_at.desc()
    ).offset(offset).limit(limit).all()
    
    # Build response with highlighted context
    results = []
    for page in pages:
        result = page.to_dict()
        result['wiki'] = {'id': page.wiki.id, 'name': page.wiki.name, 'slug': page.wiki.slug}
        
        # Add search context (snippet where query was found)
        content_lower = (page.content or '').lower()
        query_lower = query.lower()
        
        if query_lower in content_lower:
            # Find position and extract context
            pos = content_lower.find(query_lower)
            start = max(0, pos - 100)
            end = min(len(page.content), pos + len(query) + 100)
            
            snippet = page.content[start:end]
            if start > 0:
                snippet = '...' + snippet
            if end < len(page.content):
                snippet = snippet + '...'
            
            result['context'] = snippet
        elif query_lower in (page.title or '').lower():
            result['context'] = page.summary or (page.content[:200] + '...' if page.content and len(page.content) > 200 else page.content)
        else:
            result['context'] = page.summary or (page.content[:200] + '...' if page.content and len(page.content) > 200 else page.content)
        
        results.append(result)
    
    return jsonify({
        'pages': results,
        'total': total,
        'limit': limit,
        'offset': offset,
        'query': query
    }), 200


@search_bp.route('/wikis/<int:wiki_id>/pages', methods=['GET'])
@jwt_required()
def search_wiki_pages(wiki_id):
    """Search pages within a specific wiki."""
    current_user_id = int(get_jwt_identity())
    
    # Verify wiki access
    wiki = Wiki.query.get(wiki_id)
    if not wiki:
        return jsonify({'error': 'Wiki not found'}), 404
    
    user = User.query.get(current_user_id)
    if not wiki.is_public and wiki.owner_id != current_user_id:
        if not user.get_wiki_role(wiki_id):
            return jsonify({'error': 'Access denied'}), 403
    
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'error': 'Search query required'}), 400
    
    limit = min(request.args.get('limit', 20, type=int), 100)
    offset = request.args.get('offset', 0, type=int)
    
    search_term = f'%{query}%'
    
    base_query = Page.query.filter(
        Page.wiki_id == wiki_id,
        Page.is_published == True,
        or_(
            Page.title.ilike(search_term),
            Page.content.ilike(search_term),
            Page.summary.ilike(search_term)
        )
    )
    
    total = base_query.count()
    
    pages = base_query.order_by(
        func.case(
            (Page.title.ilike(search_term), 0),
            else_=1
        ),
        Page.updated_at.desc()
    ).offset(offset).limit(limit).all()
    
    results = []
    for page in pages:
        result = page.to_dict()
        
        content_lower = (page.content or '').lower()
        query_lower = query.lower()
        
        if query_lower in content_lower:
            pos = content_lower.find(query_lower)
            start = max(0, pos - 100)
            end = min(len(page.content), pos + len(query) + 100)
            
            snippet = page.content[start:end]
            if start > 0:
                snippet = '...' + snippet
            if end < len(page.content):
                snippet = snippet + '...'
            
            result['context'] = snippet
        else:
            result['context'] = page.summary or (page.content[:200] + '...' if page.content and len(page.content) > 200 else page.content)
        
        results.append(result)
    
    return jsonify({
        'pages': results,
        'total': total,
        'limit': limit,
        'offset': offset,
        'query': query
    }), 200


@search_bp.route('/users', methods=['GET'])
@jwt_required()
def search_users():
    """Search users by username or display name (for adding wiki members)."""
    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify({'error': 'Search query must be at least 2 characters'}), 400
    
    limit = min(request.args.get('limit', 10, type=int), 50)
    
    search_term = f'%{query}%'
    
    users = User.query.filter(
        User.is_active == True,
        or_(
            User.username.ilike(search_term),
            User.display_name.ilike(search_term)
        )
    ).limit(limit).all()
    
    return jsonify({
        'users': [u.to_dict() for u in users],
        'count': len(users)
    }), 200
