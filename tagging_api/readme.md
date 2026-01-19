# Wiki Content Tagging Microservice

## Overview

A GPU-enabled FastAPI microservice that analyzes wiki page content using local LLMs to automatically generate contextual tags. Supports both synchronous requests for immediate feedback and asynchronous batch processing via Redis Queue.

## Architecture

### Service Type
- **Framework**: FastAPI (async-first, high performance)
- **Transport**: HTTP/REST (gRPC not required for this use case)
- **Deployment**: Standalone microservice running on GPU-enabled machine
- **Authentication**: Bearer token in request headers

### Processing Modes

1. **Synchronous Endpoint** (`POST /analyze`)
   - Immediate tag generation for real-time UI feedback
   - Returns results directly in HTTP response
   - Use for single-page analysis when user needs instant results

2. **Asynchronous Queue** (Redis Queue integration)
   - Batch processing of multiple pages
   - Persistent job queue (survives service restarts)
   - Multiple worker instances can process from same queue
   - Use for bulk tagging operations, background processing

### Queue Architecture

**Leverage Existing RQ Infrastructure**:
- Extend the current Redis Queue setup (same Redis instance)
- Add new queue: `tagging` (alongside existing `embeddings` queue)
- Benefits:
  - Unified queue management
  - Proven persistence and reliability
  - Workers can process both embedding and tagging jobs
  - Single Redis connection pool

**Queue Processing**:
- One request processed at a time per worker (GPU memory management)
- Multiple workers can run on different GPU machines for scale
- Jobs persist across service restarts
- Failed jobs can be retried with exponential backoff

## Tag Generation Strategy

### Hybrid Approach

1. **LLM-Based Contextual Analysis** (Primary)
   - Analyze full page content, title, and structure
   - Generate semantically relevant tags based on context
   - Identify implicit topics and themes
   - Consider markdown structure (headings, lists, code blocks)

2. **Existing Tag Matching** (Secondary)
   - Compare generated tags against wiki's existing tag vocabulary
   - Use semantic similarity to match synonyms
   - Prefer existing tags when overlap detected (avoid tag proliferation)

3. **Confidence Scoring**
   - Return confidence score (0.0-1.0) for each suggested tag
   - Caller decides threshold for auto-application
   - Recommend: >0.8 = auto-apply, 0.5-0.8 = suggest, <0.5 = omit

### Content Analysis

**Input Processing**:
- Parse markdown to extract structure
- Weight different content types:
  - Page title: High weight (primary indicator)
  - Headings: Medium-high weight (section topics)
  - Body text: Medium weight (detailed content)
  - Code blocks: Medium weight (technical tags)
  - Breadcrumbs/hierarchy: Low-medium weight (contextual tags)

**Context Considerations**:
- Page hierarchy position
- Parent/sibling page topics
- Wiki domain/purpose
- Historical tags on similar pages (if provided)

## API Design

### Authentication

All endpoints require authentication:
```
Authorization: Bearer <API_TOKEN>
```

Configure via environment variable: `TAGGING_API_TOKEN`

### Endpoints

#### 1. Analyze Page (Synchronous)

```http
POST /analyze
Content-Type: application/json
Authorization: Bearer <token>

{
  "content": "# Introduction to Flask\n\nFlask is a micro web framework...",
  "title": "Flask Tutorial",
  "existing_tags": [
    {
      "name": "python",
      "color": "#3776AB"
    },
    {
      "name": "web-development",
      "color": "#FF6B6B"
    }
  ],
  "context": {
    "breadcrumbs": ["Programming", "Web Development", "Python"],
    "wiki_id": 1,
    "wiki_name": "Dev Wiki"
  },
  "options": {
    "max_tags": 10,
    "min_confidence": 0.0,
    "suggest_new_tags": true,
    "match_existing_only": false
  }
}
```

**Response**:
```json
{
  "tags": [
    {
      "name": "flask",
      "confidence": 0.95,
      "is_new": true,
      "rationale": "Primary framework discussed in content",
      "category": "framework"
    },
    {
      "name": "python",
      "confidence": 0.92,
      "is_new": false,
      "rationale": "Flask is a Python framework, content includes Python code",
      "category": "language",
      "matched_existing_tag_id": "python"
    },
    {
      "name": "REST API",
      "confidence": 0.87,
      "is_new": true,
      "rationale": "Tutorial covers RESTful endpoint creation",
      "category": "architecture"
    },
    {
      "name": "web-development",
      "confidence": 0.85,
      "is_new": false,
      "rationale": "Web application development tutorial",
      "category": "domain",
      "matched_existing_tag_id": "web-development"
    },
    {
      "name": "beginner",
      "confidence": 0.78,
      "is_new": true,
      "rationale": "Tutorial-style content with introductory examples",
      "category": "level"
    }
  ],
  "model_name": "gemma-2-9b-it",
  "model_version": "v1.0",
  "processing_time_ms": 342,
  "stats": {
    "new_tags_suggested": 3,
    "existing_tags_matched": 2,
    "total_tags": 5,
    "content_tokens": 1523
  }
}
```

#### 2. Queue Batch Job (Asynchronous)

```http
POST /analyze/batch
Content-Type: application/json
Authorization: Bearer <token>

{
  "pages": [
    {
      "page_id": 123,
      "content": "...",
      "title": "Flask Tutorial",
      "existing_tags": [...],
      "context": {...}
    },
    {
      "page_id": 124,
      "content": "...",
      "title": "Django Guide",
      "existing_tags": [...],
      "context": {...}
    }
  ],
  "callback_url": "https://wiki.example.com/api/tagging/callback",
  "options": {
    "max_tags": 10,
    "min_confidence": 0.5
  }
}
```

**Response**:
```json
{
  "job_id": "tag_batch_abc123",
  "status": "queued",
  "page_count": 2,
  "estimated_time_seconds": 120,
  "queue_position": 3
}
```

**Check Job Status**:
```http
GET /jobs/{job_id}
Authorization: Bearer <token>
```

**Response**:
```json
{
  "job_id": "tag_batch_abc123",
  "status": "completed",  // queued, processing, completed, failed
  "progress": {
    "total": 2,
    "completed": 2,
    "failed": 0
  },
  "results": [
    {
      "page_id": 123,
      "tags": [...],
      "processing_time_ms": 342
    },
    {
      "page_id": 124,
      "tags": [...],
      "processing_time_ms": 298
    }
  ],
  "created_at": "2026-01-19T10:30:00Z",
  "completed_at": "2026-01-19T10:32:15Z"
}
```

#### 3. Health Check

```http
GET /health
```

**Response**:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_name": "gemma-2-9b-it",
  "device": "cuda",
  "gpu_memory_used_mb": 4523,
  "gpu_memory_total_mb": 24576,
  "queue_size": 5
}
```

#### 4. Model Information

```http
GET /info
```

**Response**:
```json
{
  "service": "wiki-tagging-service",
  "version": "1.0.0",
  "model": {
    "name": "gemma-2-9b-it",
    "type": "llm",
    "parameters": "9B",
    "context_window": 8192,
    "quantization": "4-bit"
  },
  "capabilities": {
    "max_input_tokens": 6000,
    "max_tags_per_page": 20,
    "supported_languages": ["en", "code"],
    "batch_processing": true
  },
  "configuration": {
    "temperature": 0.3,
    "top_p": 0.9,
    "max_new_tokens": 200
  }
}
```

## Model Options

### Recommended Models (Ordered by Size)

#### Small Models (2-4B parameters) - **Start Here**
Good for: Quick iteration, lower VRAM, faster inference

1. **Gemma 2 2B IT** (Recommended starter)
   - VRAM: ~3-4GB (4-bit quantized)
   - Speed: ~50 tokens/sec on RTX 3090
   - Quality: Good for straightforward tagging
   - Model: `google/gemma-2-2b-it`

2. **Phi-3 Mini (3.8B)**
   - VRAM: ~4-5GB (4-bit quantized)
   - Speed: ~40 tokens/sec
   - Quality: Excellent instruction following
   - Model: `microsoft/Phi-3-mini-4k-instruct`

3. **Qwen2 1.5B Instruct**
   - VRAM: ~2-3GB (4-bit quantized)
   - Speed: ~70 tokens/sec
   - Quality: Fast, decent for simple tagging
   - Model: `Qwen/Qwen2-1.5B-Instruct`

#### Medium Models (7-9B parameters)
Good for: Better context understanding, more nuanced tags

4. **Gemma 2 9B IT** (Best quality/performance balance)
   - VRAM: ~8-10GB (4-bit quantized)
   - Speed: ~25 tokens/sec on RTX 3090
   - Quality: Excellent reasoning and context understanding
   - Model: `google/gemma-2-9b-it`

5. **Llama 3.1 8B Instruct**
   - VRAM: ~8-10GB (4-bit quantized)
   - Speed: ~20 tokens/sec
   - Quality: Strong general purpose model
   - Model: `meta-llama/Meta-Llama-3.1-8B-Instruct`

6. **Mistral 7B Instruct v0.3**
   - VRAM: ~7-9GB (4-bit quantized)
   - Speed: ~30 tokens/sec
   - Quality: Good balance of speed and quality
   - Model: `mistralai/Mistral-7B-Instruct-v0.3`

#### Large Models (13B+ parameters)
Good for: Maximum quality, complex reasoning

7. **Llama 3.1 70B Instruct** (If you have the hardware)
   - VRAM: ~40-50GB (4-bit quantized)
   - Speed: ~5-10 tokens/sec
   - Quality: State-of-the-art open source
   - Model: `meta-llama/Meta-Llama-3.1-70B-Instruct`

### Model Configuration

Environment variables for easy model swapping:
```bash
# Model selection
TAGGING_MODEL_NAME="google/gemma-2-2b-it"
TAGGING_MODEL_TYPE="transformers"  # transformers, llama-cpp, vllm

# Quantization
QUANTIZATION="4bit"  # none, 4bit, 8bit

# Generation parameters
TEMPERATURE=0.3  # Lower = more consistent tags
TOP_P=0.9
MAX_NEW_TOKENS=200

# Hardware
DEVICE="cuda"
DEVICE_MAP="auto"  # Let model decide GPU allocation
```

### Prompt Engineering

**System Prompt Template**:
```
You are a wiki content analyzer that generates relevant tags for documentation pages.
Your task is to analyze the provided content and suggest appropriate tags.

Guidelines:
- Generate 5-10 tags maximum
- Tags should be concise (1-3 words)
- Include both specific and general tags
- Consider: technologies, concepts, difficulty level, content type
- Prefer existing tags when semantically similar
- Return tags in order of relevance (highest first)
```

**User Prompt Template**:
```
Page Title: {title}
Wiki Context: {breadcrumbs}

Content:
{content}

Existing Tags in Wiki: {existing_tags}

Analyze this content and suggest relevant tags. For each tag:
1. Name (lowercase, hyphen-separated)
2. Confidence (0.0-1.0)
3. Brief rationale
4. Whether it's new or matches an existing tag

Return as JSON array.
```

## Implementation Considerations

### Rate Limiting & Resource Management

**Queue-Based Approach** (Recommended):
- Accept all incoming requests immediately
- Add to Redis Queue
- Worker processes one job at a time
- Natural backpressure through queue depth
- No request rejection (persistent queue)

**Benefits**:
- Predictable GPU memory usage
- Graceful handling of load spikes
- Fair job ordering (FIFO)
- Easy horizontal scaling (add more workers)

**Alternative - In-Memory Rate Limiting**:
- If synchronous endpoint needs hard limits
- Use FastAPI middleware with token bucket
- Return 429 Too Many Requests when at capacity

### Caching Strategy

**Tag Vector Cache**:
- Pre-compute embeddings for all existing wiki tags
- Cache in memory or Redis
- Fast similarity matching for tag deduplication
- Refresh when new tags added to wiki

**Model Output Cache** (Optional):
- Cache results for identical content
- Use content hash as key
- TTL: 1-7 days
- Reduce redundant processing

### Error Handling

**Model Failures**:
- Timeout after 30s for single page analysis
- Retry logic: 3 attempts with exponential backoff
- Fallback: Return empty tag list with error flag

**Queue Failures**:
- Job marked as failed after max retries
- Store failure reason in job metadata
- Webhook callback on failure (if provided)

**GPU OOM**:
- Catch CUDA out of memory errors
- Log and mark job as failed
- Consider reducing batch size dynamically

### Monitoring & Observability

**Metrics to Track**:
- Average processing time per page
- Tags generated per page (avg, min, max)
- Model confidence scores distribution
- Queue depth and processing rate
- GPU utilization and memory
- Error rates by error type

**Logging**:
- Request/response logging (INFO level)
- Model inference time (DEBUG)
- Errors with full stack traces (ERROR)
- Queue job lifecycle events (INFO)

## Integration with Wiki Application

### Current Scope (Phase 1)

**Simple HTTP API**:
- Tagging service is stateless
- No direct database access
- Wiki app calls `/analyze` endpoint with page content
- Wiki app handles tag creation/assignment in its database
- Wiki app manages authentication tokens

**Benefits**:
- Clear separation of concerns
- Easy to develop and test independently
- Flexible deployment options
- Can swap models without wiki app changes

### Future Enhancements (Phase 2+)

1. **Direct Database Integration**
   - Add endpoint: `POST /analyze/page/{page_id}`
   - Service pulls page from wiki database
   - Service creates Tag records directly
   - Requires database connection configuration

2. **Webhook Callbacks**
   - Notify wiki app when batch jobs complete
   - Push results instead of polling
   - Include job ID and status

3. **Tag Suggestion UI**
   - Show suggestions before applying
   - Allow user to accept/reject individual tags
   - Confidence-based filtering in UI

4. **Active Learning**
   - Track which suggested tags get verified
   - Use verification data to fine-tune prompts
   - Improve confidence calibration

5. **Multi-Model Ensemble**
   - Run multiple models for same content
   - Aggregate results with weighted voting
   - Higher confidence for consensus tags

6. **Incremental Tagging**
   - Only analyze new/changed sections
   - Preserve tags for unchanged content
   - Diff-based tag updates

## Deployment

### Requirements

**Hardware**:
- GPU: 8GB+ VRAM (for Gemma 2B-9B models)
- RAM: 16GB+ system memory
- Storage: 20GB for model weights

**Software**:
- Python 3.10+
- CUDA 11.8+ / ROCm (for AMD GPUs)
- Redis server (shared with wiki app)

### Docker Support

```dockerfile
FROM nvidia/cuda:12.1-runtime-ubuntu22.04

# Install Python and dependencies
RUN apt-get update && apt-get install -y python3.10 python3-pip

# Install PyTorch with CUDA support
RUN pip install torch --index-url https://download.pytorch.org/whl/cu121

# Install application dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY . /app
WORKDIR /app

# Download model on build (optional)
# RUN python download_model.py

EXPOSE 8002

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8002"]
```

### Environment Variables

```bash
# Service
TAGGING_API_TOKEN=your-secret-token-here
PORT=8002
WORKERS=1  # Number of uvicorn workers

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_QUEUE_NAME=tagging

# Model
TAGGING_MODEL_NAME=google/gemma-2-2b-it
DEVICE=cuda
QUANTIZATION=4bit
CACHE_DIR=/models

# Processing
MAX_INPUT_TOKENS=6000
MAX_TAGS_PER_PAGE=10
TEMPERATURE=0.3
BATCH_SIZE=1  # Process one at a time
```

### Running the Service

**Development**:
```bash
cd tagging_api
pip install -r requirements.txt
uvicorn app:app --reload --port 8002
```

**Production**:
```bash
# Main FastAPI service
uvicorn app:app --host 0.0.0.0 --port 8002 --workers 1

# RQ Worker for batch processing (separate process)
python worker.py
```

**Docker Compose** (alongside wiki app):
```yaml
services:
  tagging-service:
    build: ./tagging_api
    ports:
      - "8002:8002"
    environment:
      - REDIS_URL=redis://redis:6379/0
      - TAGGING_MODEL_NAME=google/gemma-2-2b-it
    volumes:
      - ./models:/models
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

## Testing Strategy

### Unit Tests
- Prompt generation logic
- Content parsing and chunking
- Tag deduplication algorithm
- Confidence scoring

### Integration Tests
- API endpoint contracts
- Redis queue operations
- Model inference pipeline
- Authentication middleware

### Load Tests
- Concurrent request handling
- Queue processing throughput
- GPU memory usage under load
- Response time degradation

### Model Evaluation
- Precision/recall on test dataset
- Confidence calibration accuracy
- Tag diversity metrics
- Processing time benchmarks

## Development Roadmap

### Phase 1: MVP ✅ **COMPLETE**
- [x] FastAPI application structure
- [x] Authentication middleware
- [x] `/analyze` synchronous endpoint
- [x] Basic LLM integration (Gemma 2B)
- [x] Prompt engineering (4 templates: detailed, quick, technical, general)
- [x] Response formatting
- [x] Error handling
- [x] Logging setup

### Phase 2: Queue Integration ✅ **COMPLETE**
- [x] Redis Queue setup
- [x] `/analyze/batch` endpoint
- [x] RQ worker implementation
- [x] Job status tracking
- [x] Retry logic
- [x] Job results storage

### Phase 3: Production Readiness 🚧 **IN PROGRESS**
- [ ] Docker containerization
- [x] Environment configuration
- [x] Health checks
- [ ] Metrics/monitoring (logging implemented, metrics TBD)
- [x] API documentation (Swagger auto-generated at /docs)
- [ ] Performance optimization

### Phase 4: Advanced Features 📋 **PLANNED**
- [ ] Multiple model support (configurable via env, no runtime switching yet)
- [x] Tag caching strategy (embedding cache implemented)
- [ ] Webhook callbacks
- [ ] Model swapping API
- [ ] Fine-tuning capabilities
- [ ] Active learning integration

## Security Considerations

### Authentication
- Require bearer token for all endpoints
- Rotate tokens periodically
- Rate limit per token
- Log all authentication attempts

### Input Validation
- Sanitize markdown input
- Limit content length (max tokens)
- Validate JSON schema
- Prevent injection attacks

### Output Safety
- Escape HTML in tag names
- Validate tag name format
- Limit tag count
- Filter inappropriate content

### Infrastructure
- Run service in isolated container
- Limit network access (only Redis and caller)
- Use read-only filesystem where possible
- Regular security updates

## Performance Targets

### Latency
- Synchronous endpoint: <2s for typical page (1000 tokens)
- Queue processing: 10-20 pages/minute per worker
- Health check: <100ms

### Throughput
- Single worker: 500-1000 pages/hour
- Scalable with additional GPU workers

### Quality
- Precision: >0.80 (80% of suggested tags are relevant)
- Recall: >0.70 (captures 70% of human-selected tags)
- Confidence calibration: ±0.10 (85% confident ≈ 75-95% accurate)

## Appendix

### Tag Categories
Suggested categorization scheme for UI grouping:

- **Technology**: Programming languages, frameworks, libraries
- **Concept**: Design patterns, algorithms, architectures
- **Domain**: Industry, application area, use case
- **Level**: Beginner, intermediate, advanced, expert
- **Type**: Tutorial, reference, guide, api-docs, troubleshooting
- **Platform**: Web, mobile, desktop, cloud, embedded
- **Status**: Draft, reviewed, outdated, deprecated

### Sample Prompts

See `/prompts` directory for complete prompt templates and examples.

### API Client Example

```python
import requests

class TaggingClient:
    def __init__(self, base_url: str, api_token: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {api_token}"}
    
    def analyze_page(self, content: str, title: str, existing_tags: list) -> dict:
        response = requests.post(
            f"{self.base_url}/analyze",
            json={
                "content": content,
                "title": title,
                "existing_tags": existing_tags
            },
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

# Usage
client = TaggingClient("http://localhost:8002", "your-token")
result = client.analyze_page(
    content="# Flask Tutorial\n\n...",
    title="Flask Tutorial",
    existing_tags=[{"name": "python", "color": "#3776AB"}]
)

for tag in result["tags"]:
    if tag["confidence"] > 0.8:
        print(f"Apply: {tag['name']} ({tag['confidence']:.2f})")
```

---

**Document Version**: 1.0  
**Last Updated**: 2026-01-19  
**Status**: Planning/Requirements Phase
