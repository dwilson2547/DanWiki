"""
Configuration for Wiki Tagging Service
"""
import os
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Service configuration
    service_name: str = "wiki-tagging-service"
    version: str = "1.0.0"
    api_token: str  # Required - no default
    port: int = 8002
    host: str = "0.0.0.0"
    workers: int = 1
    log_level: str = "INFO"
    
    # Redis configuration
    redis_url: str = "redis://localhost:6379/0"
    redis_queue_name: str = "tagging"
    
    # Model configuration
    model_name: str = "google/gemma-2-2b-it"
    model_type: Literal["transformers", "llama-cpp", "vllm"] = "transformers"
    device: str = "cuda"  # cuda, cpu, mps (for Mac)
    device_map: str = "auto"
    cache_dir: str = "./models"
    
    # Quantization
    quantization: Literal["none", "4bit", "8bit"] = "4bit"
    load_in_4bit: bool = True
    load_in_8bit: bool = False
    
    # Generation parameters
    temperature: float = 0.3
    top_p: float = 0.9
    top_k: int = 50
    max_new_tokens: int = 300
    repetition_penalty: float = 1.1
    
    # Processing limits
    max_input_tokens: int = 6000
    max_tags_per_page: int = 10
    min_confidence: float = 0.0
    batch_size: int = 1  # Process one at a time to manage GPU memory
    
    # Prompt configuration
    default_prompt_template: str = "detailed"
    prompt_templates_dir: str = "./prompts"
    
    # Caching
    enable_tag_cache: bool = True
    cache_ttl_seconds: int = 86400  # 24 hours
    
    # Timeouts and retries
    inference_timeout_seconds: int = 30
    max_retries: int = 3
    retry_delay_seconds: int = 5
    
    # Sentence transformer for tag matching
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    similarity_threshold: float = 0.75  # For matching existing tags
    
    @property
    def quantization_config(self) -> dict:
        """Get quantization configuration for model loading."""
        if self.quantization == "4bit":
            return {
                "load_in_4bit": True,
                "bnb_4bit_compute_dtype": "float16",
                "bnb_4bit_quant_type": "nf4",
                "bnb_4bit_use_double_quant": True,
            }
        elif self.quantization == "8bit":
            return {"load_in_8bit": True}
        return {}
    
    @property
    def generation_config(self) -> dict:
        """Get generation configuration for the model."""
        return {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "max_new_tokens": self.max_new_tokens,
            "repetition_penalty": self.repetition_penalty,
            "do_sample": True if self.temperature > 0 else False,
        }


# Global settings instance
settings = Settings()
