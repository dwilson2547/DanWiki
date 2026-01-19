"""
Pydantic models for request/response validation
"""
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator


class TagModel(BaseModel):
    """Existing tag in the wiki."""
    name: str
    color: Optional[str] = None


class ContextModel(BaseModel):
    """Context information about the page."""
    breadcrumbs: Optional[list[str]] = Field(default=None, description="Page hierarchy path")
    wiki_id: Optional[int] = None
    wiki_name: Optional[str] = None


class AnalysisOptions(BaseModel):
    """Options for tag analysis."""
    max_tags: int = Field(default=10, ge=1, le=20)
    min_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    suggest_new_tags: bool = Field(default=True, description="Whether to suggest new tags")
    match_existing_only: bool = Field(default=False, description="Only match against existing tags")
    prompt_template: Optional[str] = Field(default=None, description="Name of prompt template to use")


class AnalyzeRequest(BaseModel):
    """Request model for /analyze endpoint."""
    content: str = Field(..., min_length=1, description="Markdown content of the page")
    title: str = Field(..., min_length=1, description="Page title")
    existing_tags: Optional[list[TagModel]] = Field(default=None, description="Existing tags in the wiki")
    context: Optional[ContextModel] = Field(default=None, description="Page context information")
    options: Optional[AnalysisOptions] = Field(default_factory=AnalysisOptions)


class SuggestedTag(BaseModel):
    """A suggested tag with metadata."""
    name: str = Field(..., description="Tag name (lowercase, hyphen-separated)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    is_new: bool = Field(..., description="Whether this is a new tag or matches existing")
    rationale: str = Field(..., description="Why this tag was suggested")
    category: Optional[str] = Field(default=None, description="Tag category (technology, concept, etc.)")
    matched_existing_tag: Optional[str] = Field(default=None, description="Name of matched existing tag")
    
    @field_validator('name')
    @classmethod
    def normalize_tag_name(cls, v: str) -> str:
        """Normalize tag name to lowercase and replace spaces with hyphens."""
        return v.lower().strip().replace(' ', '-')


class AnalysisStats(BaseModel):
    """Statistics about the analysis."""
    new_tags_suggested: int
    existing_tags_matched: int
    total_tags: int
    content_tokens: int


class AnalyzeResponse(BaseModel):
    """Response model for /analyze endpoint."""
    tags: list[SuggestedTag]
    model_name: str
    model_version: str = "1.0"
    processing_time_ms: float
    stats: AnalysisStats


class BatchPageRequest(BaseModel):
    """Single page in a batch request."""
    page_id: int
    content: str
    title: str
    existing_tags: Optional[list[TagModel]] = None
    context: Optional[ContextModel] = None


class BatchAnalyzeRequest(BaseModel):
    """Request model for /analyze/batch endpoint."""
    pages: list[BatchPageRequest] = Field(..., min_length=1)
    callback_url: Optional[str] = Field(default=None, description="URL to call when job completes")
    options: Optional[AnalysisOptions] = Field(default_factory=AnalysisOptions)


class BatchAnalyzeResponse(BaseModel):
    """Response model for /analyze/batch endpoint."""
    job_id: str
    status: Literal["queued", "processing", "completed", "failed"]
    page_count: int
    estimated_time_seconds: Optional[int] = None
    queue_position: Optional[int] = None


class PageResult(BaseModel):
    """Result for a single page in batch processing."""
    page_id: int
    tags: list[SuggestedTag]
    processing_time_ms: float
    error: Optional[str] = None


class JobProgress(BaseModel):
    """Progress information for a batch job."""
    total: int
    completed: int
    failed: int


class JobStatusResponse(BaseModel):
    """Response model for /jobs/{job_id} endpoint."""
    job_id: str
    status: Literal["queued", "processing", "completed", "failed"]
    progress: JobProgress
    results: Optional[list[PageResult]] = None
    created_at: str
    completed_at: Optional[str] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Response model for /health endpoint."""
    status: Literal["healthy", "unhealthy"]
    model_loaded: bool
    model_name: str
    device: str
    gpu_memory_used_mb: Optional[float] = None
    gpu_memory_total_mb: Optional[float] = None
    queue_size: Optional[int] = None


class ModelCapabilities(BaseModel):
    """Model capabilities information."""
    max_input_tokens: int
    max_tags_per_page: int
    supported_languages: list[str]
    batch_processing: bool


class ModelInfoConfig(BaseModel):
    """Model configuration details."""
    temperature: float
    top_p: float
    max_new_tokens: int


class ModelInfoDetail(BaseModel):
    """Detailed model information."""
    name: str
    type: str
    parameters: Optional[str] = None
    context_window: Optional[int] = None
    quantization: Optional[str] = None


class InfoResponse(BaseModel):
    """Response model for /info endpoint."""
    service: str
    version: str
    model: ModelInfoDetail
    capabilities: ModelCapabilities
    configuration: ModelInfoConfig
    available_prompts: list[str]
