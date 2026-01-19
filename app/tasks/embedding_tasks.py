"""
Background Tasks for Embedding Generation

RQ (Redis Queue) tasks for asynchronous embedding generation and indexing.
"""

import logging
from datetime import datetime, timezone
from typing import List, Dict
from redis import Redis
from rq import Queue
from flask import current_app

from app.models import db, Page, PageEmbedding
from app.services.chunking import chunk_page_content
from app.services.embeddings import get_embedding_client, EmbeddingServiceError

logger = logging.getLogger(__name__)


def get_redis_connection():
    """Get Redis connection for RQ."""
    redis_url = current_app.config.get('REDIS_URL', 'redis://localhost:6379/0')
    return Redis.from_url(redis_url)


def get_task_queue():
    """Get the RQ task queue."""
    return Queue('embeddings', connection=get_redis_connection())


def enqueue_page_embedding(page_id: int, force_regenerate: bool = False):
    """
    Enqueue a page for embedding generation.
    
    Args:
        page_id: ID of the page to process
        force_regenerate: If True, regenerate even if embeddings exist
    
    Returns:
        RQ Job instance
    """
    queue = get_task_queue()
    job = queue.enqueue(
        generate_page_embeddings,
        page_id,
        force_regenerate,
        job_timeout='10m',
        result_ttl=86400,  # Keep result for 24 hours
        failure_ttl=86400
    )
    logger.info(f"Enqueued embedding generation for page {page_id}, job: {job.id}")
    return job


def generate_page_embeddings(page_id: int, force_regenerate: bool = False):
    """
    Background task to generate embeddings for a page.
    
    This is the main worker task that:
    1. Loads the page
    2. Chunks the content
    3. Generates embeddings via the GPU microservice
    4. Stores embeddings in the database
    
    Args:
        page_id: ID of the page to process
        force_regenerate: If True, delete existing embeddings first
    """
    logger.info(f"Starting embedding generation for page {page_id}")
    
    try:
        # Load page
        page = Page.query.get(page_id)
        if not page:
            logger.error(f"Page {page_id} not found")
            return {'success': False, 'error': 'Page not found'}
        
        # Update status
        page.embeddings_status = 'processing'
        db.session.commit()
        
        # Delete existing embeddings if regenerating
        if force_regenerate:
            logger.info(f"Deleting existing embeddings for page {page_id}")
            PageEmbedding.query.filter_by(page_id=page_id).delete()
            db.session.commit()
        
        # Check if embeddings already exist (and not forcing regeneration)
        if not force_regenerate:
            existing_count = PageEmbedding.query.filter_by(page_id=page_id).count()
            if existing_count > 0:
                logger.info(f"Page {page_id} already has {existing_count} embeddings, skipping")
                page.embeddings_status = 'completed'
                page.embeddings_updated_at = datetime.now(timezone.utc)
                db.session.commit()
                return {'success': True, 'chunks': existing_count, 'skipped': True}
        
        # Chunk the page content
        logger.info(f"Chunking page {page_id}: {page.title}")
        chunks = chunk_page_content(page.title, page.content or '')
        
        if not chunks:
            logger.warning(f"No chunks generated for page {page_id}")
            page.embeddings_status = 'completed'
            page.embeddings_updated_at = datetime.now(timezone.utc)
            db.session.commit()
            return {'success': True, 'chunks': 0}
        
        logger.info(f"Generated {len(chunks)} chunks for page {page_id}")
        
        # Extract texts for embedding
        texts = [chunk['chunk_text'] for chunk in chunks]
        
        # Generate embeddings via microservice
        logger.info(f"Requesting embeddings from service for {len(texts)} chunks")
        embedding_client = get_embedding_client()
        
        try:
            embeddings = embedding_client.generate_embeddings_batch(
                texts,
                normalize=True
            )
        except EmbeddingServiceError as e:
            logger.error(f"Embedding service error: {e}")
            page.embeddings_status = 'failed'
            db.session.commit()
            return {'success': False, 'error': str(e)}
        
        if len(embeddings) != len(chunks):
            logger.error(f"Mismatch: {len(embeddings)} embeddings for {len(chunks)} chunks")
            page.embeddings_status = 'failed'
            db.session.commit()
            return {'success': False, 'error': 'Embedding count mismatch'}
        
        # Store embeddings in database
        logger.info(f"Storing {len(embeddings)} embeddings for page {page_id}")
        stored_count = 0
        
        for chunk, embedding in zip(chunks, embeddings):
            page_embedding = PageEmbedding(
                page_id=page_id,
                chunk_index=chunk['chunk_index'],
                chunk_text=chunk['chunk_text'],
                heading_path=chunk.get('heading_path', ''),
                token_count=chunk.get('token_count', 0),
                embedding=embedding
            )
            db.session.add(page_embedding)
            stored_count += 1
        
        # Update page status
        page.embeddings_status = 'completed'
        page.embeddings_updated_at = datetime.now(timezone.utc)
        
        db.session.commit()
        
        logger.info(f"Successfully generated and stored {stored_count} embeddings for page {page_id}")
        
        return {
            'success': True,
            'page_id': page_id,
            'chunks': stored_count,
            'skipped': False
        }
    
    except Exception as e:
        logger.error(f"Error generating embeddings for page {page_id}: {e}", exc_info=True)
        
        # Update page status to failed
        try:
            page = Page.query.get(page_id)
            if page:
                page.embeddings_status = 'failed'
                db.session.commit()
        except Exception as inner_e:
            logger.error(f"Failed to update page status: {inner_e}")
        
        return {'success': False, 'error': str(e)}


def regenerate_all_embeddings():
    """
    Background task to regenerate embeddings for all published pages.
    
    This can be used when:
    - Upgrading to a new embedding model
    - Fixing issues with existing embeddings
    - Initial bulk processing
    
    Returns:
        Dictionary with job statistics
    """
    logger.info("Starting bulk embedding regeneration for all pages")
    
    try:
        # Get all published pages
        pages = Page.query.filter_by(is_published=True).all()
        logger.info(f"Found {len(pages)} published pages to process")
        
        queue = get_task_queue()
        jobs = []
        
        for page in pages:
            job = queue.enqueue(
                generate_page_embeddings,
                page.id,
                True,  # force_regenerate
                job_timeout='10m'
            )
            jobs.append(job.id)
        
        logger.info(f"Enqueued {len(jobs)} embedding generation jobs")
        
        return {
            'success': True,
            'total_pages': len(pages),
            'jobs_enqueued': len(jobs)
        }
    
    except Exception as e:
        logger.error(f"Error in bulk regeneration: {e}", exc_info=True)
        return {'success': False, 'error': str(e)}
