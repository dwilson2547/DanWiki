"""
Wiki Tagging Microservice - FastAPI Application

A GPU-enabled service for automated wiki page tagging using local LLMs.
"""
import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Header, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from redis import Redis
from rq import Queue
from rq.job import Job

from config import settings
from llm_service import llm_service
from models import (
    AnalyzeRequest,
    AnalyzeResponse,
    BatchAnalyzeRequest,
    BatchAnalyzeResponse,
    JobStatusResponse,
    JobProgress,
    PageResult,
    HealthResponse,
    InfoResponse,
    ModelInfoDetail,
    ModelCapabilities,
    ModelInfoConfig,
)
from prompts import list_templates

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Redis connection for queue
redis_conn: Optional[Redis] = None
tagging_queue: Optional[Queue] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    logger.info("Starting Wiki Tagging Service")
    logger.info(f"Model: {settings.model_name}")
    logger.info(f"Device: {settings.device}")
    
    try:
        # Load LLM model
        llm_service.load_model()
        logger.info("Model loaded successfully")
        
        # Connect to Redis
        global redis_conn, tagging_queue
        redis_conn = Redis.from_url(settings.redis_url)
        tagging_queue = Queue(settings.redis_queue_name, connection=redis_conn)
        logger.info(f"Connected to Redis queue: {settings.redis_queue_name}")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Wiki Tagging Service")
    if redis_conn:
        redis_conn.close()


# Create FastAPI app
app = FastAPI(
    title="Wiki Tagging Service",
    description="Automated tag generation for wiki pages using local LLMs",
    version=settings.version,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Authentication dependency
async def verify_token(authorization: str = Header(...)):
    """Verify the bearer token."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header"
        )
    
    token = authorization.replace("Bearer ", "")
    if token != settings.api_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API token"
        )
    return token


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    gpu_used, gpu_total = llm_service.get_gpu_memory_info()
    queue_size = len(tagging_queue) if tagging_queue else None
    
    return HealthResponse(
        status="healthy" if llm_service.is_loaded() else "unhealthy",
        model_loaded=llm_service.is_loaded(),
        model_name=settings.model_name,
        device=settings.device,
        gpu_memory_used_mb=gpu_used,
        gpu_memory_total_mb=gpu_total,
        queue_size=queue_size
    )


@app.get("/info", response_model=InfoResponse)
async def get_info():
    """Get service and model information."""
    # Extract model size from name (e.g., "gemma-2-2b-it" -> "2B")
    model_params = None
    model_name_lower = settings.model_name.lower()
    for size in ["2b", "7b", "9b", "13b", "70b"]:
        if size in model_name_lower:
            model_params = size.upper()
            break
    
    return InfoResponse(
        service=settings.service_name,
        version=settings.version,
        model=ModelInfoDetail(
            name=settings.model_name,
            type="llm",
            parameters=model_params,
            context_window=settings.max_input_tokens,
            quantization=settings.quantization if settings.quantization != "none" else None
        ),
        capabilities=ModelCapabilities(
            max_input_tokens=settings.max_input_tokens,
            max_tags_per_page=settings.max_tags_per_page,
            supported_languages=["en", "code"],
            batch_processing=True
        ),
        configuration=ModelInfoConfig(
            temperature=settings.temperature,
            top_p=settings.top_p,
            max_new_tokens=settings.max_new_tokens
        ),
        available_prompts=list_templates()
    )


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_page(
    request: AnalyzeRequest,
    token: str = Depends(verify_token)
):
    """
    Analyze a wiki page and generate tag suggestions.
    
    This is a synchronous endpoint that returns results immediately.
    """
    try:
        # Extract existing tag names
        existing_tag_names = [tag.name for tag in request.existing_tags] if request.existing_tags else []
        
        # Get breadcrumbs
        breadcrumbs = request.context.breadcrumbs if request.context else None
        
        # Get prompt template
        prompt_template = request.options.prompt_template or settings.default_prompt_template
        
        # Generate tags
        tags, stats, processing_time = llm_service.generate_tags(
            title=request.title,
            content=request.content,
            existing_tags=existing_tag_names,
            breadcrumbs=breadcrumbs,
            max_tags=request.options.max_tags,
            min_confidence=request.options.min_confidence,
            prompt_template=prompt_template
        )
        
        return AnalyzeResponse(
            tags=tags,
            model_name=settings.model_name,
            model_version=settings.version,
            processing_time_ms=processing_time,
            stats=stats
        )
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tag generation failed: {str(e)}"
        )


@app.post("/analyze/batch", response_model=BatchAnalyzeResponse)
async def analyze_batch(
    request: BatchAnalyzeRequest,
    token: str = Depends(verify_token)
):
    """
    Queue a batch of pages for tag analysis.
    
    Returns immediately with a job ID. Use GET /jobs/{job_id} to check status.
    """
    if not tagging_queue:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Queue service not available"
        )
    
    try:
        # Create unique job ID
        job_id = f"tag_batch_{uuid.uuid4().hex[:12]}"
        
        # Enqueue the batch job
        job = tagging_queue.enqueue(
            'worker.process_batch',  # Function to call
            request.model_dump(),     # Job arguments
            job_id=job_id,
            timeout=settings.inference_timeout_seconds * len(request.pages),
            result_ttl=86400,  # Keep results for 24 hours
            failure_ttl=86400,
        )
        
        # Calculate queue position
        queue_position = len(tagging_queue)
        
        # Estimate processing time (rough estimate: 2 seconds per page)
        estimated_time = len(request.pages) * 2
        
        logger.info(f"Batch job queued: {job_id}, {len(request.pages)} pages")
        
        return BatchAnalyzeResponse(
            job_id=job_id,
            status="queued",
            page_count=len(request.pages),
            estimated_time_seconds=estimated_time,
            queue_position=queue_position
        )
        
    except Exception as e:
        logger.error(f"Failed to queue batch job: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue job: {str(e)}"
        )


@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    token: str = Depends(verify_token)
):
    """Get the status of a batch job."""
    if not redis_conn:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Queue service not available"
        )
    
    try:
        job = Job.fetch(job_id, connection=redis_conn)
        
        # Map RQ status to our status
        status_map = {
            'queued': 'queued',
            'started': 'processing',
            'finished': 'completed',
            'failed': 'failed',
        }
        job_status = status_map.get(job.get_status(), 'queued')
        
        # Get results if completed
        results = None
        if job_status == 'completed' and job.result:
            results = job.result.get('results', [])
        
        # Get error if failed
        error = None
        if job_status == 'failed':
            error = str(job.exc_info) if job.exc_info else "Unknown error"
        
        # Build progress
        if job.meta and 'progress' in job.meta:
            progress = JobProgress(**job.meta['progress'])
        else:
            # Default progress
            total = job.meta.get('total_pages', 0) if job.meta else 0
            progress = JobProgress(
                total=total,
                completed=0 if job_status != 'completed' else total,
                failed=0
            )
        
        return JobStatusResponse(
            job_id=job_id,
            status=job_status,
            progress=progress,
            results=results,
            created_at=job.created_at.isoformat() if job.created_at else None,
            completed_at=job.ended_at.isoformat() if job.ended_at else None,
            error=error
        )
        
    except Exception as e:
        logger.error(f"Failed to get job status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found: {job_id}"
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host=settings.host,
        port=settings.port,
        reload=False,
        log_level=settings.log_level.lower()
    )
