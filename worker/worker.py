#!/usr/bin/env python
"""
RQ Worker for Background Tasks

Processes tasks from the Redis queue, primarily embedding generation jobs.
Run multiple instances for parallel processing.
"""

import os
import sys
import logging
from redis import Redis
from rq import Worker, Queue

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.config import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Start the RQ worker."""
    # Create Flask app context
    config_name = os.getenv('FLASK_ENV', 'development')
    app = create_app(config_name)
    
    # Get Redis connection
    redis_url = app.config.get('REDIS_URL', 'redis://localhost:6379/0')
    logger.info(f"Connecting to Redis: {redis_url}")
    
    redis_conn = Redis.from_url(redis_url)
    
    # Create queue
    queues = [Queue('embeddings', connection=redis_conn)]
    
    logger.info("Starting RQ worker...")
    logger.info(f"Listening on queues: {[q.name for q in queues]}")
    
    # Run worker within Flask app context
    with app.app_context():
        worker = Worker(queues, connection=redis_conn)
        worker.work()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Worker error: {e}", exc_info=True)
        sys.exit(1)
