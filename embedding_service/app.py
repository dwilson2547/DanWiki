"""
Embedding Microservice for Wiki Application

A standalone Flask service that generates text embeddings using sentence-transformers.
Designed to run on a GPU machine for fast embedding generation.

Endpoints:
- POST /embed - Generate embeddings for text or array of texts
- GET /health - Health check
- GET /info - Model information
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from sentence_transformers import SentenceTransformer
import numpy as np
import logging
import os
from typing import List, Union
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
MODEL_NAME = os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
DEVICE = os.getenv('DEVICE', 'cuda')  # 'cuda' for GPU, 'cpu' for CPU
BATCH_SIZE = int(os.getenv('BATCH_SIZE', '32'))
MAX_SEQ_LENGTH = int(os.getenv('MAX_SEQ_LENGTH', '256'))

# Load model
logger.info(f"Loading model: {MODEL_NAME} on device: {DEVICE}")
try:
    model = SentenceTransformer(MODEL_NAME, device=DEVICE)
    model.max_seq_length = MAX_SEQ_LENGTH
    logger.info(f"Model loaded successfully. Embedding dimension: {model.get_sentence_embedding_dimension()}")
except Exception as e:
    logger.error(f"Failed to load model: {e}")
    raise


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'model': MODEL_NAME,
        'device': DEVICE,
        'embedding_dimension': model.get_sentence_embedding_dimension()
    }), 200


@app.route('/info', methods=['GET'])
def model_info():
    """Get model information."""
    return jsonify({
        'model_name': MODEL_NAME,
        'embedding_dimension': model.get_sentence_embedding_dimension(),
        'max_seq_length': model.max_seq_length,
        'device': DEVICE,
        'batch_size': BATCH_SIZE
    }), 200


@app.route('/embed', methods=['POST'])
def generate_embeddings():
    """
    Generate embeddings for input text(s).
    
    Request JSON:
    {
        "texts": "single text" | ["text1", "text2", ...],
        "normalize": true  # optional, default true
    }
    
    Response JSON:
    {
        "embeddings": [[...], [...], ...],
        "dimension": 384,
        "model": "sentence-transformers/all-MiniLM-L6-v2",
        "count": 2,
        "processing_time_ms": 45.2
    }
    """
    start_time = time.time()
    
    try:
        data = request.get_json()
        
        if not data or 'texts' not in data:
            return jsonify({'error': 'Missing "texts" field in request'}), 400
        
        texts = data['texts']
        normalize = data.get('normalize', True)
        
        # Handle single text or array of texts
        if isinstance(texts, str):
            texts = [texts]
        elif not isinstance(texts, list):
            return jsonify({'error': '"texts" must be a string or array of strings'}), 400
        
        if not texts:
            return jsonify({'error': 'Empty texts array'}), 400
        
        if len(texts) > 1000:
            return jsonify({'error': 'Maximum 1000 texts per request'}), 400
        
        # Validate all texts are strings
        if not all(isinstance(t, str) for t in texts):
            return jsonify({'error': 'All texts must be strings'}), 400
        
        # Generate embeddings
        logger.info(f"Generating embeddings for {len(texts)} text(s)")
        embeddings = model.encode(
            texts,
            batch_size=BATCH_SIZE,
            show_progress_bar=False,
            normalize_embeddings=normalize,
            convert_to_numpy=True
        )
        
        # Convert to list for JSON serialization
        embeddings_list = embeddings.tolist()
        
        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        
        return jsonify({
            'embeddings': embeddings_list,
            'dimension': model.get_sentence_embedding_dimension(),
            'model': MODEL_NAME,
            'count': len(texts),
            'processing_time_ms': round(processing_time, 2)
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        return jsonify({'error': str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', '8001'))
    host = os.getenv('HOST', '0.0.0.0')
    
    logger.info(f"Starting embedding service on {host}:{port}")
    app.run(host=host, port=port, debug=False)
