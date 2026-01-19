"""
Embedding Service Client

HTTP client to communicate with the GPU-based embedding microservice.
Handles batching, retries, and error handling.
"""

import requests
import logging
from typing import List, Union, Dict
from flask import current_app

logger = logging.getLogger(__name__)


class EmbeddingServiceError(Exception):
    """Custom exception for embedding service errors."""
    pass


class EmbeddingServiceClient:
    """
    Client for the embedding microservice running on GPU machine.
    
    The microservice exposes a /embed endpoint that generates embeddings
    using sentence-transformers.
    """
    
    def __init__(self, service_url: str = None, timeout: int = None):
        """
        Initialize the embedding service client.
        
        Args:
            service_url: Base URL of the embedding service (default from config)
            timeout: Request timeout in seconds (default from config)
        """
        self.service_url = (service_url or 
                           current_app.config.get('EMBEDDING_SERVICE_URL', 
                                                 'http://localhost:8001'))
        self.timeout = (timeout or 
                       current_app.config.get('EMBEDDING_REQUEST_TIMEOUT', 30))
        
        # Remove trailing slash
        self.service_url = self.service_url.rstrip('/')
    
    def health_check(self) -> bool:
        """
        Check if the embedding service is healthy.
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            response = requests.get(
                f"{self.service_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Embedding service health check failed: {e}")
            return False
    
    def get_info(self) -> Dict:
        """
        Get information about the embedding model.
        
        Returns:
            Dictionary with model info (name, dimension, etc.)
        
        Raises:
            EmbeddingServiceError: If request fails
        """
        try:
            response = requests.get(
                f"{self.service_url}/info",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get embedding service info: {e}")
            raise EmbeddingServiceError(f"Service info request failed: {e}")
    
    def generate_embeddings(self, 
                          texts: Union[str, List[str]],
                          normalize: bool = True) -> List[List[float]]:
        """
        Generate embeddings for text(s).
        
        Args:
            texts: Single text string or list of text strings
            normalize: Whether to normalize embeddings (L2 norm)
        
        Returns:
            List of embedding vectors (each is a list of floats)
        
        Raises:
            EmbeddingServiceError: If generation fails
        """
        # Ensure texts is a list
        was_single = isinstance(texts, str)
        if was_single:
            texts = [texts]
        
        if not texts:
            raise EmbeddingServiceError("No texts provided for embedding")
        
        # Validate text count
        if len(texts) > 1000:
            raise EmbeddingServiceError("Maximum 1000 texts per request")
        
        try:
            logger.info(f"Requesting embeddings for {len(texts)} text(s)")
            
            response = requests.post(
                f"{self.service_url}/embed",
                json={
                    'texts': texts,
                    'normalize': normalize
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            embeddings = data.get('embeddings', [])
            
            logger.info(f"Generated {len(embeddings)} embeddings "
                       f"in {data.get('processing_time_ms', 0):.2f}ms")
            
            return embeddings if not was_single else embeddings[0]
            
        except requests.exceptions.Timeout:
            logger.error(f"Embedding request timed out after {self.timeout}s")
            raise EmbeddingServiceError(f"Request timed out after {self.timeout}s")
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Embedding request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json().get('error', str(e))
                    raise EmbeddingServiceError(f"Service error: {error_detail}")
                except:
                    pass
            raise EmbeddingServiceError(f"Request failed: {e}")
        
        except Exception as e:
            logger.error(f"Unexpected error generating embeddings: {e}")
            raise EmbeddingServiceError(f"Unexpected error: {e}")
    
    def generate_embeddings_batch(self,
                                 texts: List[str],
                                 batch_size: int = None,
                                 normalize: bool = True) -> List[List[float]]:
        """
        Generate embeddings for many texts with automatic batching.
        
        Args:
            texts: List of text strings
            batch_size: Size of each batch (default from config)
            normalize: Whether to normalize embeddings
        
        Returns:
            List of embedding vectors in same order as input
        
        Raises:
            EmbeddingServiceError: If generation fails
        """
        if not texts:
            return []
        
        batch_size = batch_size or current_app.config.get('EMBEDDING_BATCH_SIZE', 32)
        
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1} "
                       f"({len(batch)} texts)")
            
            embeddings = self.generate_embeddings(batch, normalize=normalize)
            all_embeddings.extend(embeddings)
        
        return all_embeddings


# Convenience functions for use in other modules

def get_embedding_client() -> EmbeddingServiceClient:
    """
    Get an instance of the embedding service client.
    
    Returns:
        Configured EmbeddingServiceClient instance
    """
    return EmbeddingServiceClient()


def generate_text_embeddings(texts: Union[str, List[str]],
                            normalize: bool = True) -> List[List[float]]:
    """
    Convenience function to generate embeddings.
    
    Args:
        texts: Text or list of texts
        normalize: Whether to normalize embeddings
    
    Returns:
        Embedding vector(s)
    """
    client = get_embedding_client()
    return client.generate_embeddings(texts, normalize=normalize)


def check_service_health() -> bool:
    """
    Check if embedding service is available.
    
    Returns:
        True if service is healthy
    """
    client = get_embedding_client()
    return client.health_check()
