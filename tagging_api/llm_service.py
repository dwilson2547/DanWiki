"""
LLM service for tag generation.

Handles model loading, inference, and tag extraction.
"""
import json
import logging
import time
import torch
from typing import Optional
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from sentence_transformers import SentenceTransformer, util

from config import settings
from models import SuggestedTag, AnalysisStats
from prompts import get_template

logger = logging.getLogger(__name__)


class LLMService:
    """Service for generating tags using a local LLM."""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.embedding_model = None
        self.model_name = settings.model_name
        self.device = settings.device
        self._tag_embeddings_cache = {}
        
    def load_model(self):
        """Load the LLM and embedding models."""
        logger.info(f"Loading LLM model: {self.model_name}")
        logger.info(f"Device: {self.device}")
        logger.info(f"Quantization: {settings.quantization}")
        
        try:
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                cache_dir=settings.cache_dir,
                trust_remote_code=True
            )
            
            # Configure quantization if enabled
            quantization_config = None
            if settings.quantization != "none":
                quantization_config = BitsAndBytesConfig(**settings.quantization_config)
            
            # Load model
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                cache_dir=settings.cache_dir,
                quantization_config=quantization_config,
                device_map=settings.device_map,
                trust_remote_code=True,
                torch_dtype=torch.float16 if settings.device == "cuda" else torch.float32,
            )
            
            logger.info(f"Model loaded successfully on {self.model.device}")
            
            # Load sentence transformer for tag matching
            logger.info(f"Loading embedding model: {settings.embedding_model}")
            self.embedding_model = SentenceTransformer(
                settings.embedding_model,
                device=self.device
            )
            logger.info("Embedding model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load models: {e}", exc_info=True)
            raise
    
    def is_loaded(self) -> bool:
        """Check if models are loaded."""
        return self.model is not None and self.tokenizer is not None
    
    def generate_tags(
        self,
        title: str,
        content: str,
        existing_tags: Optional[list[str]] = None,
        breadcrumbs: Optional[list[str]] = None,
        max_tags: int = 10,
        min_confidence: float = 0.0,
        prompt_template: str = "detailed"
    ) -> tuple[list[SuggestedTag], AnalysisStats, float]:
        """
        Generate tags for a wiki page.
        
        Returns:
            tuple: (list of suggested tags, stats, processing time in ms)
        """
        if not self.is_loaded():
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        start_time = time.time()
        existing_tags = existing_tags or []
        
        # Cache embeddings for existing tags
        if settings.enable_tag_cache:
            self._cache_tag_embeddings(existing_tags)
        
        # Get prompt template
        template = get_template(prompt_template)
        
        # Format prompts
        system_prompt = template.SYSTEM_PROMPT
        user_prompt = template.format_prompt(
            title=title,
            content=content,
            existing_tags=existing_tags,
            breadcrumbs=breadcrumbs
        )
        
        # Create chat messages (Gemma/Llama format)
        messages = [
            {"role": "user", "content": f"{system_prompt}\n\n{user_prompt}"}
        ]
        
        # Generate response
        try:
            response_text = self._generate_response(messages)
            logger.debug(f"Model response: {response_text[:500]}...")
            
            # Parse tags from JSON response
            suggested_tags = self._parse_tags_from_response(
                response_text,
                existing_tags,
                max_tags,
                min_confidence
            )
            
            # Calculate stats
            new_count = sum(1 for tag in suggested_tags if tag.is_new)
            matched_count = sum(1 for tag in suggested_tags if not tag.is_new)
            
            # Estimate token count (rough approximation)
            token_count = len(content.split()) * 1.3  # Rough estimate
            
            stats = AnalysisStats(
                new_tags_suggested=new_count,
                existing_tags_matched=matched_count,
                total_tags=len(suggested_tags),
                content_tokens=int(token_count)
            )
            
            processing_time_ms = (time.time() - start_time) * 1000
            
            return suggested_tags, stats, processing_time_ms
            
        except Exception as e:
            logger.error(f"Tag generation failed: {e}", exc_info=True)
            raise
    
    def _generate_response(self, messages: list[dict]) -> str:
        """Generate response from the model."""
        # Apply chat template
        formatted_input = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        # Tokenize
        inputs = self.tokenizer(
            formatted_input,
            return_tensors="pt",
            truncation=True,
            max_length=settings.max_input_tokens
        ).to(self.model.device)
        
        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                **settings.generation_config,
                pad_token_id=self.tokenizer.eos_token_id,
            )
        
        # Decode
        response = self.tokenizer.decode(
            outputs[0][inputs['input_ids'].shape[1]:],
            skip_special_tokens=True
        )
        
        return response.strip()
    
    def _parse_tags_from_response(
        self,
        response: str,
        existing_tags: list[str],
        max_tags: int,
        min_confidence: float
    ) -> list[SuggestedTag]:
        """Parse tags from the model's JSON response."""
        # Extract JSON array from response
        try:
            # Try to find JSON array in the response
            start_idx = response.find('[')
            end_idx = response.rfind(']')
            
            if start_idx == -1 or end_idx == -1:
                logger.warning("No JSON array found in response")
                return []
            
            json_str = response[start_idx:end_idx + 1]
            tag_data = json.loads(json_str)
            
            if not isinstance(tag_data, list):
                logger.warning("Response is not a JSON array")
                return []
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response was: {response}")
            return []
        
        # Convert to SuggestedTag objects
        suggested_tags = []
        for item in tag_data[:max_tags]:
            try:
                # Check if this matches an existing tag
                matched_tag = self._find_matching_tag(
                    item.get('name', ''),
                    existing_tags
                )
                
                # Override is_new if we found a match
                if matched_tag and not item.get('is_new', True):
                    item['matched_existing_tag'] = matched_tag
                
                tag = SuggestedTag(**item)
                
                # Filter by confidence
                if tag.confidence >= min_confidence:
                    suggested_tags.append(tag)
                    
            except Exception as e:
                logger.warning(f"Failed to parse tag item: {item}, error: {e}")
                continue
        
        return suggested_tags
    
    def _find_matching_tag(
        self,
        tag_name: str,
        existing_tags: list[str]
    ) -> Optional[str]:
        """
        Find if a tag name matches any existing tags using semantic similarity.
        
        Returns the matched existing tag name or None.
        """
        if not existing_tags or not settings.enable_tag_cache:
            return None
        
        tag_name_lower = tag_name.lower().strip()
        
        # Exact match first
        for existing in existing_tags:
            if existing.lower() == tag_name_lower:
                return existing
        
        # Semantic similarity match
        try:
            tag_embedding = self.embedding_model.encode(
                tag_name,
                convert_to_tensor=True,
                device=self.device
            )
            
            # Get embeddings for existing tags
            existing_embeddings = []
            for existing_tag in existing_tags:
                if existing_tag in self._tag_embeddings_cache:
                    existing_embeddings.append(
                        self._tag_embeddings_cache[existing_tag]
                    )
                else:
                    # Compute and cache
                    emb = self.embedding_model.encode(
                        existing_tag,
                        convert_to_tensor=True,
                        device=self.device
                    )
                    self._tag_embeddings_cache[existing_tag] = emb
                    existing_embeddings.append(emb)
            
            if not existing_embeddings:
                return None
            
            # Stack embeddings
            existing_tensor = torch.stack(existing_embeddings)
            
            # Compute similarities
            similarities = util.cos_sim(tag_embedding, existing_tensor)[0]
            
            # Find best match
            max_sim_idx = similarities.argmax().item()
            max_similarity = similarities[max_sim_idx].item()
            
            if max_similarity >= settings.similarity_threshold:
                matched_tag = existing_tags[max_sim_idx]
                logger.debug(
                    f"Matched '{tag_name}' to '{matched_tag}' "
                    f"(similarity: {max_similarity:.3f})"
                )
                return matched_tag
            
        except Exception as e:
            logger.warning(f"Error in tag matching: {e}")
        
        return None
    
    def _cache_tag_embeddings(self, tags: list[str]):
        """Pre-compute and cache embeddings for tags."""
        for tag in tags:
            if tag not in self._tag_embeddings_cache:
                try:
                    embedding = self.embedding_model.encode(
                        tag,
                        convert_to_tensor=True,
                        device=self.device
                    )
                    self._tag_embeddings_cache[tag] = embedding
                except Exception as e:
                    logger.warning(f"Failed to cache embedding for tag '{tag}': {e}")
    
    def get_gpu_memory_info(self) -> tuple[Optional[float], Optional[float]]:
        """Get GPU memory usage in MB (used, total)."""
        if self.device == "cuda" and torch.cuda.is_available():
            try:
                used = torch.cuda.memory_allocated() / (1024 ** 2)
                total = torch.cuda.get_device_properties(0).total_memory / (1024 ** 2)
                return used, total
            except Exception as e:
                logger.warning(f"Failed to get GPU memory info: {e}")
        return None, None


# Global service instance
llm_service = LLMService()
