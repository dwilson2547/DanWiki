"""
Semantic Search Routes

AI-powered semantic search using pgvector similarity search on page embeddings.
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import text, func
import logging
from typing import List, Dict

from app.models import db, User, Wiki, Page, PageEmbedding
from app.services.embeddings import get_embedding_client, EmbeddingServiceError

logger = logging.getLogger(__name__)

semantic_search_bp = Blueprint('semantic_search', __name__, url_prefix='/api/search')


def get_accessible_wiki_ids(user_id: int) -> List[int]:
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


@semantic_search_bp.route('/semantic', methods=['GET'])
@jwt_required()
def semantic_search():
    """
    Semantic search across page embeddings using vector similarity.
    
    Query params:
    - q: search query (required)
    - wiki_id: limit to specific wiki (optional)
    - limit: max results (default 20, max 100)
    - offset: pagination offset (default 0)
    - threshold: minimum similarity score 0-1 (default 0.5)
    
    Returns:
        List of matching page chunks with similarity scores
    """
    current_user_id = int(get_jwt_identity())
    
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'error': 'Search query required'}), 400
    
    wiki_id = request.args.get('wiki_id', type=int)
    limit = min(request.args.get('limit', 20, type=int), 100)
    offset = request.args.get('offset', 0, type=int)
    threshold = float(request.args.get('threshold', 0.5))
    
    # Get accessible wikis
    accessible_wiki_ids = get_accessible_wiki_ids(current_user_id)
    
    if not accessible_wiki_ids:
        return jsonify({'results': [], 'total': 0}), 200
    
    # If specific wiki requested, verify access
    if wiki_id:
        if wiki_id not in accessible_wiki_ids:
            return jsonify({'error': 'Wiki not accessible'}), 403
        accessible_wiki_ids = [wiki_id]
    
    # Generate embedding for the query
    try:
        embedding_client = get_embedding_client()
        query_embedding = embedding_client.generate_embeddings(query, normalize=True)
        logger.info(f"Generated query embedding for: {query[:50]}")
    except EmbeddingServiceError as e:
        logger.error(f"Failed to generate query embedding: {e}")
        return jsonify({'error': 'Embedding service unavailable', 'details': str(e)}), 503
    
    # Perform vector similarity search
    # Using cosine similarity via <=> operator (pgvector)
    # The distance operator returns smaller values for more similar vectors
    # We convert to similarity score: similarity = 1 - distance
    
    embedding_dim = current_app.config.get('EMBEDDING_DIMENSION', 384)
    
    try:
        ivfflat_probes = current_app.config.get('IVFFLAT_PROBES')
        if ivfflat_probes is not None:
            db.session.execute(text('SET LOCAL ivfflat.probes = :probes'), {'probes': ivfflat_probes})

        # Build the query
        # Note: pgvector's <=> operator returns cosine distance (0 = identical, 2 = opposite)
        # We want cosine similarity in [0,1], so: similarity = 1 - (distance / 2)
        similarity_query = text("""
            SELECT 
                pe.id as embedding_id,
                pe.page_id,
                pe.chunk_index,
                pe.chunk_text,
                pe.heading_path,
                pe.token_count,
                p.title as page_title,
                p.slug as page_slug,
                p.wiki_id,
                w.name as wiki_name,
                w.slug as wiki_slug,
                                1 - ((pe.embedding <=> :query_embedding) / 2.0) as similarity_score
            FROM page_embeddings pe
            JOIN pages p ON pe.page_id = p.id
            JOIN wikis w ON p.wiki_id = w.id
            WHERE p.wiki_id = ANY(:wiki_ids)
              AND p.is_published = true
                            AND (1 - ((pe.embedding <=> :query_embedding) / 2.0)) >= :threshold
            ORDER BY pe.embedding <=> :query_embedding
            LIMIT :limit OFFSET :offset
        """)
        
        result = db.session.execute(
            similarity_query,
            {
                'query_embedding': str(query_embedding),
                'wiki_ids': accessible_wiki_ids,
                'threshold': threshold,
                'limit': limit,
                'offset': offset
            }
        )
        
        rows = result.fetchall()
        
        # Format results
        results = []
        seen_pages = set()
        
        for row in rows:
            result_dict = {
                'embedding_id': row[0],
                'page_id': row[1],
                'chunk_index': row[2],
                'chunk_text': row[3],
                'heading_path': row[4],
                'token_count': row[5],
                'page_title': row[6],
                'page_slug': row[7],
                'wiki_id': row[8],
                'wiki_name': row[9],
                'wiki_slug': row[10],
                'similarity_score': float(row[11]),
                'page_url': f"/wikis/{row[8]}/pages/{row[1]}"
            }
            
            results.append(result_dict)
            seen_pages.add(row[1])
        
        # Get total count (approximate for performance)
        # In production, you might want to cache this or use estimates
        count_query = text("""
            SELECT COUNT(DISTINCT pe.page_id)
            FROM page_embeddings pe
            JOIN pages p ON pe.page_id = p.id
            WHERE p.wiki_id = ANY(:wiki_ids)
              AND p.is_published = true
              AND (1 - ((pe.embedding <=> :query_embedding) / 2.0)) >= :threshold
        """)
        
        count_result = db.session.execute(
            count_query,
            {
                'query_embedding': str(query_embedding),
                'wiki_ids': accessible_wiki_ids,
                'threshold': threshold
            }
        )
        total_pages = count_result.scalar() or 0
        
        return jsonify({
            'results': results,
            'total_chunks': len(results),
            'total_pages': total_pages,
            'unique_pages': len(seen_pages),
            'query': query,
            'threshold': threshold
        }), 200
        
    except Exception as e:
        logger.error(f"Semantic search failed: {e}", exc_info=True)
        return jsonify({'error': 'Search failed', 'details': str(e)}), 500


@semantic_search_bp.route('/hybrid', methods=['GET'])
@jwt_required()
def hybrid_search():
    """
    Hybrid search combining keyword search and semantic search.
    
    Merges results from both keyword matching and vector similarity,
    providing better results than either alone.
    
    Query params:
    - q: search query (required)
    - wiki_id: limit to specific wiki (optional)
    - limit: max results (default 20)
    - semantic_weight: weight for semantic results 0-1 (default 0.7)
    """
    current_user_id = int(get_jwt_identity())
    
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'error': 'Search query required'}), 400
    
    wiki_id = request.args.get('wiki_id', type=int)
    limit = min(request.args.get('limit', 20, type=int), 100)
    semantic_weight = float(request.args.get('semantic_weight', 0.7))
    keyword_weight = 1.0 - semantic_weight
    
    # Get accessible wikis
    accessible_wiki_ids = get_accessible_wiki_ids(current_user_id)
    
    if not accessible_wiki_ids:
        return jsonify({'results': [], 'total': 0}), 200
    
    if wiki_id:
        if wiki_id not in accessible_wiki_ids:
            return jsonify({'error': 'Wiki not accessible'}), 403
        accessible_wiki_ids = [wiki_id]
    
    # 1. Keyword search
    search_term = f'%{query}%'
    keyword_query = db.session.query(
        Page.id,
        Page.title,
        Page.slug,
        Page.summary,
        Page.wiki_id,
        Wiki.name.label('wiki_name'),
        Wiki.slug.label('wiki_slug'),
        # Simple scoring: prioritize title matches
        func.coalesce(
            func.nullif(
                (func.lower(Page.title).like(func.lower(search_term))).cast(db.Integer) * 2 +
                (func.lower(Page.content).like(func.lower(search_term))).cast(db.Integer),
                0
            ),
            1
        ).label('keyword_score')
    ).join(Wiki).filter(
        Page.wiki_id.in_(accessible_wiki_ids),
        Page.is_published == True,
        db.or_(
            Page.title.ilike(search_term),
            Page.content.ilike(search_term),
            Page.summary.ilike(search_term)
        )
    ).limit(limit * 2).all()  # Get more for merging
    
    # 2. Semantic search
    try:
        embedding_client = get_embedding_client()
        query_embedding = embedding_client.generate_embeddings(query, normalize=True)

        ivfflat_probes = current_app.config.get('IVFFLAT_PROBES')
        if ivfflat_probes is not None:
            db.session.execute(text('SET LOCAL ivfflat.probes = :probes'), {'probes': ivfflat_probes})
        
        semantic_query = text("""
            SELECT DISTINCT ON (p.id)
                p.id,
                p.title,
                p.slug,
                p.summary,
                p.wiki_id,
                w.name as wiki_name,
                w.slug as wiki_slug,
                MAX(1 - ((pe.embedding <=> :query_embedding) / 2.0)) as semantic_score
            FROM pages p
            JOIN page_embeddings pe ON p.id = pe.page_id
            JOIN wikis w ON p.wiki_id = w.id
            WHERE p.wiki_id = ANY(:wiki_ids)
              AND p.is_published = true
            GROUP BY p.id, p.title, p.slug, p.summary, p.wiki_id, w.name, w.slug
            ORDER BY p.id, semantic_score DESC
            LIMIT :limit
        """)
        
        semantic_result = db.session.execute(
            semantic_query,
            {
                'query_embedding': str(query_embedding),
                'wiki_ids': accessible_wiki_ids,
                'limit': limit * 2
            }
        )
        semantic_rows = semantic_result.fetchall()
    except Exception as e:
        logger.error(f"Semantic search portion failed: {e}")
        semantic_rows = []
    
    # 3. Merge and re-rank results
    page_scores = {}
    
    # Add keyword results
    for row in keyword_query:
        page_id = row[0]
        page_scores[page_id] = {
            'page_id': page_id,
            'title': row[1],
            'slug': row[2],
            'summary': row[3],
            'wiki_id': row[4],
            'wiki_name': row[5],
            'wiki_slug': row[6],
            'keyword_score': float(row[7]) if row[7] else 0,
            'semantic_score': 0,
            'combined_score': 0,
            'page_url': f"/wikis/{row[4]}/pages/{page_id}"
        }
    
    # Add/update with semantic results
    for row in semantic_rows:
        page_id = row[0]
        if page_id not in page_scores:
            page_scores[page_id] = {
                'page_id': page_id,
                'title': row[1],
                'slug': row[2],
                'summary': row[3],
                'wiki_id': row[4],
                'wiki_name': row[5],
                'wiki_slug': row[6],
                'keyword_score': 0,
                'semantic_score': 0,
                'combined_score': 0,
                'page_url': f"/wikis/{row[4]}/pages/{page_id}"
            }
        page_scores[page_id]['semantic_score'] = float(row[7]) if row[7] else 0
    
    # Calculate combined scores
    for page_id, scores in page_scores.items():
        scores['combined_score'] = (
            scores['keyword_score'] * keyword_weight +
            scores['semantic_score'] * semantic_weight
        )
    
    # Sort by combined score and limit
    results = sorted(
        page_scores.values(),
        key=lambda x: x['combined_score'],
        reverse=True
    )[:limit]
    
    return jsonify({
        'results': results,
        'total': len(results),
        'query': query,
        'semantic_weight': semantic_weight,
        'keyword_weight': keyword_weight
    }), 200
