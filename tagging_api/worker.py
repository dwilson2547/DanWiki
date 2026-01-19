#!/usr/bin/env python
"""
RQ Worker for Tagging Service Background Tasks

Processes batch tagging jobs from the Redis queue.
Can run multiple instances for parallel processing on different GPU machines.
"""

import os
import sys
import logging
from datetime import datetime
from redis import Redis
from rq import Worker, Queue

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import settings
from llm_service import llm_service
from models import PageResult, SuggestedTag

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def process_batch(batch_request: dict) -> dict:
    """
    Process a batch of pages for tag generation.
    
    This function runs in the worker process and is called by RQ.
    
    Args:
        batch_request: Dictionary containing batch request data
        
    Returns:
        Dictionary with results for each page
    """
    logger.info(f"Processing batch job with {len(batch_request['pages'])} pages")
    
    # Ensure model is loaded
    if not llm_service.is_loaded():
        logger.info("Loading model in worker process...")
        llm_service.load_model()
    
    results = []
    failed_count = 0
    
    # Get options
    options = batch_request.get('options', {})
    max_tags = options.get('max_tags', 10)
    min_confidence = options.get('min_confidence', 0.0)
    prompt_template = options.get('prompt_template', settings.default_prompt_template)
    
    # Process each page
    for idx, page_data in enumerate(batch_request['pages']):
        page_id = page_data['page_id']
        
        try:
            logger.info(f"Processing page {idx + 1}/{len(batch_request['pages'])}: {page_id}")
            
            # Extract existing tags
            existing_tag_names = [
                tag['name'] for tag in page_data.get('existing_tags', [])
            ]
            
            # Get breadcrumbs
            breadcrumbs = None
            if page_data.get('context'):
                breadcrumbs = page_data['context'].get('breadcrumbs')
            
            # Generate tags
            tags, stats, processing_time = llm_service.generate_tags(
                title=page_data['title'],
                content=page_data['content'],
                existing_tags=existing_tag_names,
                breadcrumbs=breadcrumbs,
                max_tags=max_tags,
                min_confidence=min_confidence,
                prompt_template=prompt_template
            )
            
            # Convert to dict for JSON serialization
            result = PageResult(
                page_id=page_id,
                tags=tags,
                processing_time_ms=processing_time,
                error=None
            )
            results.append(result.model_dump())
            
            logger.info(
                f"Page {page_id} processed successfully: "
                f"{len(tags)} tags generated in {processing_time:.0f}ms"
            )
            
        except Exception as e:
            logger.error(f"Failed to process page {page_id}: {e}", exc_info=True)
            
            result = PageResult(
                page_id=page_id,
                tags=[],
                processing_time_ms=0,
                error=str(e)
            )
            results.append(result.model_dump())
            failed_count += 1
    
    logger.info(
        f"Batch processing completed: "
        f"{len(results) - failed_count} successful, {failed_count} failed"
    )
    
    return {
        'results': results,
        'total_pages': len(batch_request['pages']),
        'successful': len(results) - failed_count,
        'failed': failed_count,
        'completed_at': datetime.utcnow().isoformat()
    }


def main():
    """Start the RQ worker."""
    logger.info("Starting Tagging Service Worker")
    logger.info(f"Redis URL: {settings.redis_url}")
    logger.info(f"Queue name: {settings.redis_queue_name}")
    logger.info(f"Model: {settings.model_name}")
    
    try:
        # Connect to Redis
        redis_conn = Redis.from_url(settings.redis_url)
        logger.info("Connected to Redis")
        
        # Create queue
        queue = Queue(settings.redis_queue_name, connection=redis_conn)
        logger.info(f"Listening on queue: {settings.redis_queue_name}")
        
        # Pre-load model before starting worker
        logger.info("Pre-loading model...")
        llm_service.load_model()
        logger.info("Model loaded successfully")
        
        # Create and start worker
        worker = Worker([queue], connection=redis_conn)
        logger.info("Worker starting...")
        worker.work(with_scheduler=True)
        
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Worker error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
