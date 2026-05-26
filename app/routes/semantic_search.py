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
    current_user_id = int(get_jwt_identity())

    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'error': 'Search query required'}), 400

    wiki_id = request.args.get('wiki_id', type=int)
    limit = min(request.args.get('limit', 20, type=int), 100)
    threshold = float(request.args.get('threshold', 0.3))

    accessible_wiki_ids = get_accessible_wiki_ids(current_user_id)
    if not accessible_wiki_ids:
        return jsonify({'results': [], 'has_more': False}), 200

    if wiki_id:
        if wiki_id not in accessible_wiki_ids:
            return jsonify({'error': 'Wiki not accessible'}), 403
        accessible_wiki_ids = [wiki_id]

    try:
        embedding_client = get_embedding_client()
        query_embedding = embedding_client.generate_embeddings(query, normalize=True)
    except EmbeddingServiceError as e:
        logger.error(f"Failed to generate query embedding: {e}")
        return jsonify({'error': 'Embedding service unavailable', 'details': str(e)}), 503

    try:
        ivfflat_probes = current_app.config.get('IVFFLAT_PROBES')
        if ivfflat_probes is not None:
            db.session.execute(
                text('SET LOCAL ivfflat.probes = :probes'),
                {'probes': ivfflat_probes}
            )

        similarity_query = text("""
            SELECT * FROM (
                SELECT DISTINCT ON (p.id)
                    p.id        AS page_id,
                    p.title     AS page_title,
                    p.slug      AS page_slug,
                    p.wiki_id,
                    w.name      AS wiki_name,
                    w.slug      AS wiki_slug,
                    pe.chunk_text AS excerpt,
                    pe.heading_path,
                    1 - ((pe.embedding <=> :query_embedding) / 2.0) AS similarity_score
                FROM page_embeddings pe
                JOIN pages p ON pe.page_id = p.id
                JOIN wikis w ON p.wiki_id = w.id
                WHERE p.wiki_id = ANY(:wiki_ids)
                  AND p.is_published = TRUE
                ORDER BY p.id, pe.embedding <=> :query_embedding
            ) best_per_page
            WHERE similarity_score >= :threshold
            ORDER BY similarity_score DESC
            LIMIT :limit_plus_one
        """)

        rows = db.session.execute(
            similarity_query,
            {
                'query_embedding': str(query_embedding),
                'wiki_ids': accessible_wiki_ids,
                'threshold': threshold,
                'limit_plus_one': limit + 1,
            }
        ).fetchall()

        has_more = len(rows) > limit
        rows = rows[:limit]

        results = [
            {
                'page_id': row.page_id,
                'page_title': row.page_title,
                'page_slug': row.page_slug,
                'wiki_id': row.wiki_id,
                'wiki_name': row.wiki_name,
                'wiki_slug': row.wiki_slug,
                'excerpt': row.excerpt,
                'heading_path': row.heading_path,
                'similarity_score': float(row.similarity_score),
                'page_url': f'/wikis/{row.wiki_id}/pages/{row.page_id}',
            }
            for row in rows
        ]

        if results:
            max_score = max(r['similarity_score'] for r in results)
            for r in results:
                r['relative_score'] = (
                    round((r['similarity_score'] / max_score) * 100, 1)
                    if max_score > 0 else 0.0
                )

        return jsonify({
            'results': results,
            'has_more': has_more,
            'query': query,
            'threshold': threshold,
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
