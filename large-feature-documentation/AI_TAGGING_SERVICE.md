# AI Tagging Service - Implementation Progress

## Overview

The AI Tagging Service is a GPU-enabled FastAPI microservice that analyzes wiki page content using local LLMs to automatically generate contextual tags. The service supports both synchronous requests for real-time feedback and asynchronous batch processing via Redis Queue.

**Current Status**: 🟡 **MVP Complete - Not Yet Deployed**

**Version**: 1.0.0 (Initial MVP)

## Key Features

### Tag Generation
- **Hybrid Approach**: Combines LLM-based contextual analysis with semantic matching against existing tags
- **Multiple Prompt Templates**: Detailed, quick, technical, and general modes
- **Confidence Scoring**: Returns 0.0-1.0 confidence score for each suggested tag
- **Tag Deduplication**: Uses sentence transformers to match similar tags and prevent proliferation
- **Category Classification**: Automatically categorizes tags (technology, concept, domain, level, type, platform)

### Processing Modes
- **Synchronous Endpoint** (`/analyze`): Immediate tag generation for real-time UI feedback
- **Asynchronous Queue** (`/analyze/batch`): Bulk processing via Redis Queue for background operations
- **Persistent Jobs**: Queue survives service restarts, jobs can be processed by multiple workers

### Model Support
- **Default**: Gemma 2 2B (4-bit quantized, ~4GB VRAM)
- **Configurable**: Support for 8 different model sizes from 2B to 70B parameters
- **Quantization**: 4-bit and 8-bit support via BitsAndBytes
- **GPU Acceleration**: CUDA support with automatic device mapping

## Architecture

```
┌─────────────────┐
│   Wiki App      │
│  (Flask/React)  │
└────────┬────────┘
         │ HTTP Requests
         │ (Bearer Token Auth)
         ▼
┌─────────────────────────────────────────┐
│        Tagging Microservice             │
│          (FastAPI - Port 8002)          │
│                                         │
│  ┌──────────┐  ┌──────────────────┐   │
│  │ /analyze │  │ /analyze/batch   │   │
│  │  (sync)  │  │    (async)       │   │
│  └────┬─────┘  └────────┬─────────┘   │
│       │                 │              │
│       │                 ▼              │
│       │         ┌──────────────┐       │
│       │         │ Redis Queue  │       │
│       │         │  (tagging)   │       │
│       │         └──────┬───────┘       │
│       │                │               │
│       ▼                ▼               │
│  ┌──────────────────────────┐         │
│  │    LLM Service           │         │
│  │  - Model Loading         │         │
│  │  - Prompt Templates      │         │
│  │  - Tag Generation        │         │
│  │  - Semantic Matching     │         │
│  └──────────────────────────┘         │
└─────────────────────────────────────────┘
         │
         ▼
  ┌──────────────┐
  │  GPU/CUDA    │
  │  (Model)     │
  └──────────────┘
```

## API Endpoints

### Health Check

**GET** `/health`

Check service status and resource usage.

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_name": "google/gemma-2-2b-it",
  "device": "cuda",
  "gpu_memory_used_mb": 4523.2,
  "gpu_memory_total_mb": 24576.0,
  "queue_size": 2
}
```

### Service Information

**GET** `/info`

Get model details, capabilities, and configuration.

**Response:**
```json
{
  "service": "wiki-tagging-service",
  "version": "1.0.0",
  "model": {
    "name": "google/gemma-2-2b-it",
    "type": "llm",
    "parameters": "2B",
    "context_window": 6000,
    "quantization": "4bit"
  },
  "capabilities": {
    "max_input_tokens": 6000,
    "max_tags_per_page": 10,
    "supported_languages": ["en", "code"],
    "batch_processing": true
  },
  "configuration": {
    "temperature": 0.3,
    "top_p": 0.9,
    "max_new_tokens": 300
  },
  "available_prompts": ["detailed", "quick", "technical", "general"]
}
```

### Analyze Page (Synchronous)

**POST** `/analyze`

Generate tags for a single page immediately.

**Headers:**
- `Authorization: Bearer <API_TOKEN>`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "content": "# Flask Tutorial\n\nFlask is a micro web framework...",
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
    "min_confidence": 0.5,
    "suggest_new_tags": true,
    "match_existing_only": false,
    "prompt_template": "detailed"
  }
}
```

**Response:**
```json
{
  "tags": [
    {
      "name": "flask",
      "confidence": 0.95,
      "is_new": true,
      "rationale": "Primary framework discussed in content",
      "category": "framework",
      "matched_existing_tag": null
    },
    {
      "name": "python",
      "confidence": 0.92,
      "is_new": false,
      "rationale": "Flask is a Python framework, content includes Python code",
      "category": "language",
      "matched_existing_tag": "python"
    },
    {
      "name": "rest-api",
      "confidence": 0.87,
      "is_new": true,
      "rationale": "Tutorial covers RESTful endpoint creation",
      "category": "architecture",
      "matched_existing_tag": null
    }
  ],
  "model_name": "google/gemma-2-2b-it",
  "model_version": "1.0",
  "processing_time_ms": 342.5,
  "stats": {
    "new_tags_suggested": 2,
    "existing_tags_matched": 1,
    "total_tags": 3,
    "content_tokens": 1523
  }
}
```

### Analyze Batch (Asynchronous)

**POST** `/analyze/batch`

Queue multiple pages for background processing.

**Headers:**
- `Authorization: Bearer <API_TOKEN>`
- `Content-Type: application/json`

**Request Body:**
```json
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

**Response:**
```json
{
  "job_id": "tag_batch_abc123def456",
  "status": "queued",
  "page_count": 2,
  "estimated_time_seconds": 120,
  "queue_position": 3
}
```

### Get Job Status

**GET** `/jobs/{job_id}`

Check status of a batch job.

**Headers:**
- `Authorization: Bearer <API_TOKEN>`

**Response:**
```json
{
  "job_id": "tag_batch_abc123def456",
  "status": "completed",
  "progress": {
    "total": 2,
    "completed": 2,
    "failed": 0
  },
  "results": [
    {
      "page_id": 123,
      "tags": [...],
      "processing_time_ms": 342.5,
      "error": null
    },
    {
      "page_id": 124,
      "tags": [...],
      "processing_time_ms": 298.3,
      "error": null
    }
  ],
  "created_at": "2026-01-19T10:30:00Z",
  "completed_at": "2026-01-19T10:32:15Z",
  "error": null
}
```

## Prompt Templates

### Detailed (Default)
**Best for**: Complex pages, technical documentation, tutorials  
**Focus**: Deep content analysis with comprehensive rationale

```python
# Analyzes:
- Main topics and technologies
- Content type and difficulty level
- Semantic similarity to existing tags
- Category classification
```

### Quick
**Best for**: Short pages, simple content, batch processing  
**Focus**: Speed over detailed analysis

```python
# Optimizations:
- More aggressive content truncation
- Fewer instructions for model
- 3-7 tags instead of 5-10
```

### Technical
**Best for**: API docs, code examples, programming tutorials  
**Focus**: Programming languages, frameworks, patterns

```python
# Specializes in:
- Programming language detection
- Framework/library identification
- Design pattern recognition
- API type classification
```

### General
**Best for**: Mixed content, general wikis, unknown content type  
**Focus**: Balanced multi-dimensional analysis

```python
# Covers:
- Topic identification
- Content type classification
- Domain and application area
- Target audience level
```

## Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Service
API_TOKEN=your-secret-token-here
PORT=8002

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_QUEUE_NAME=tagging

# Model Selection
MODEL_NAME=google/gemma-2-2b-it
DEVICE=cuda
QUANTIZATION=4bit

# Generation Parameters
TEMPERATURE=0.3
TOP_P=0.9
MAX_NEW_TOKENS=300

# Processing
MAX_INPUT_TOKENS=6000
MAX_TAGS_PER_PAGE=10
MIN_CONFIDENCE=0.0

# Tag Matching
SIMILARITY_THRESHOLD=0.75
```

### Model Options

| Model | Params | VRAM | Speed | Quality | Use Case |
|-------|--------|------|-------|---------|----------|
| **Gemma 2 2B** ⭐ | 2B | ~4GB | 50 tok/s | Good | Quick iteration, testing |
| Phi-3 Mini | 3.8B | ~5GB | 40 tok/s | Excellent | Good balance |
| Qwen2 1.5B | 1.5B | ~3GB | 70 tok/s | Fair | Ultra-fast processing |
| **Gemma 2 9B** ⭐ | 9B | ~10GB | 25 tok/s | Excellent | Best quality/perf |
| Llama 3.1 8B | 8B | ~10GB | 20 tok/s | Very Good | General purpose |
| Mistral 7B | 7B | ~9GB | 30 tok/s | Very Good | Fast + quality |
| Llama 3.1 70B | 70B | ~50GB | 8 tok/s | Best | Maximum quality |

⭐ = Recommended options

## Implementation Details

### Backend Components

**FastAPI Application** (`tagging_api/app.py`):
- Endpoint definitions with Pydantic validation
- Bearer token authentication middleware
- CORS configuration
- Global error handling
- Lifespan events for model loading
- Redis Queue integration

**LLM Service** (`tagging_api/llm_service.py`):
- Model loading with quantization support
- Prompt formatting and generation
- JSON response parsing
- Semantic tag matching using sentence transformers
- Tag embedding cache management
- GPU memory monitoring

**Worker** (`tagging_api/worker.py`):
- RQ worker for background jobs
- Batch processing with error handling
- Progress tracking and reporting
- Model pre-loading on startup

**Prompt Templates** (`tagging_api/prompts/`):
- Modular template system
- Registry for template discovery
- Format functions with content truncation
- Template-specific optimizations

**Configuration** (`tagging_api/config.py`):
- Pydantic Settings for type-safe config
- Environment variable loading
- Quantization config generation
- Generation parameter management

**Data Models** (`tagging_api/models.py`):
- Request/response Pydantic models
- Field validation and normalization
- Type hints for all structures

### Dependencies

**Core Framework:**
- `fastapi==0.109.0` - Modern async web framework
- `uvicorn[standard]==0.27.0` - ASGI server
- `pydantic==2.5.3` - Data validation

**ML/LLM:**
- `torch>=2.1.0` - PyTorch for model inference
- `transformers>=4.36.0` - HuggingFace transformers
- `accelerate>=0.25.0` - Model optimization
- `bitsandbytes>=0.41.0` - Quantization support
- `sentence-transformers>=2.3.0` - Tag similarity

**Queue:**
- `redis>=5.0.1` - Redis client
- `rq>=1.15.1` - Redis Queue for background jobs

**Utilities:**
- `httpx>=0.26.0` - HTTP client for callbacks
- `python-dotenv>=1.0.0` - Environment management

## Deployment

### Development Setup

```bash
# Navigate to service directory
cd tagging_api

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start service
uvicorn app:app --reload --port 8002

# Start worker (separate terminal)
python worker.py
```

### Production Deployment

**Option 1: Systemd Services**

```bash
# Copy service files
sudo cp systemd/tagging-api.service /etc/systemd/system/
sudo cp systemd/tagging-worker.service /etc/systemd/system/

# Enable and start
sudo systemctl enable tagging-api tagging-worker
sudo systemctl start tagging-api tagging-worker

# Check status
sudo systemctl status tagging-api
sudo systemctl status tagging-worker
```

**Option 2: Docker (TODO)**

```bash
# Build image
docker build -t wiki-tagging-service .

# Run with GPU support
docker run --gpus all \
  -p 8002:8002 \
  -e API_TOKEN=your-token \
  -e REDIS_URL=redis://redis:6379/0 \
  wiki-tagging-service
```

### Hardware Requirements

**Minimum (Gemma 2B)**:
- GPU: 8GB VRAM (e.g., RTX 3060, RTX 4060)
- RAM: 16GB system memory
- Storage: 20GB for models

**Recommended (Gemma 9B)**:
- GPU: 12GB+ VRAM (e.g., RTX 3080, RTX 4070)
- RAM: 32GB system memory
- Storage: 40GB for models

**High-End (Llama 70B)**:
- GPU: 48GB+ VRAM (e.g., A100, H100)
- RAM: 64GB+ system memory
- Storage: 100GB for models

## Integration with Wiki App

### Phase 1: Manual Trigger (Current)

User clicks "Generate Tags" button → Wiki app calls `/analyze` → Display suggestions → User approves/rejects

```python
# Example integration code (future)
import requests

def generate_tags_for_page(page_id):
    page = Page.query.get(page_id)
    existing_tags = [tag.name for tag in page.tags]
    
    response = requests.post(
        "http://localhost:8002/analyze",
        headers={"Authorization": f"Bearer {TAGGING_API_TOKEN}"},
        json={
            "title": page.title,
            "content": page.content,
            "existing_tags": [{"name": t} for t in existing_tags],
            "context": {
                "breadcrumbs": [p['title'] for p in page.get_breadcrumbs()],
                "wiki_id": page.wiki_id
            }
        }
    )
    
    return response.json()
```

### Phase 2: Background Auto-Tagging (Planned)

On page create/update → Queue tagging job → Apply high-confidence tags automatically → Show as "unverified"

### Phase 3: Continuous Improvement (Planned)

Track which suggested tags get verified → Fine-tune prompts → Improve confidence calibration

## Testing

### Manual Testing

```bash
# Test health endpoint
curl http://localhost:8002/health

# Test info endpoint
curl http://localhost:8002/info

# Test analyze endpoint
curl -X POST http://localhost:8002/analyze \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Page",
    "content": "This is a Python tutorial about Flask web framework.",
    "existing_tags": [{"name": "python"}],
    "options": {"max_tags": 5}
  }'
```

### Automated Tests (TODO)

- [ ] Unit tests for prompt formatting
- [ ] Integration tests for API endpoints
- [ ] Model inference tests
- [ ] Tag matching accuracy tests
- [ ] Load testing for concurrent requests

## Performance Metrics

### Target Latency
- **Synchronous**: <2s for typical page (1000 tokens)
- **Health Check**: <100ms
- **Job Queue**: 10-20 pages/minute per worker

### Target Quality
- **Precision**: >80% of suggested tags are relevant
- **Recall**: >70% of human-selected tags captured
- **Confidence Calibration**: 85% confidence ≈ 75-95% accuracy

## Current Status & Next Steps

### ✅ Completed (MVP)
- [x] FastAPI application structure
- [x] Authentication middleware
- [x] `/analyze` synchronous endpoint
- [x] `/analyze/batch` asynchronous endpoint
- [x] `/health` and `/info` endpoints
- [x] LLM service with Gemma 2B support
- [x] 4 prompt templates (detailed, quick, technical, general)
- [x] Semantic tag matching
- [x] Tag embedding cache
- [x] RQ worker for batch processing
- [x] Environment configuration
- [x] Error handling and logging
- [x] Documentation

### 🚧 In Progress
- [ ] Testing on GPU hardware
- [ ] Model download and caching
- [ ] Performance benchmarking
- [ ] First integration with wiki app

### 📋 Planned
- [ ] Frontend "Generate Tags" button in PageEdit
- [ ] Tag suggestion UI component
- [ ] Batch tagging for existing pages
- [ ] Systemd service files
- [ ] Docker containerization
- [ ] Monitoring and metrics
- [ ] A/B testing different prompts
- [ ] Fine-tuning confidence thresholds
- [ ] Model comparison benchmarks
- [ ] Active learning from verifications
- [ ] Webhook callbacks for async jobs
- [ ] Direct database integration option

## Known Issues & Limitations

### Current Limitations
- **Single GPU Only**: No multi-GPU support yet
- **No Caching**: Repeated requests for same content reprocessed
- **No Streaming**: Must wait for full response
- **Basic Auth**: Only bearer token, no OAuth/SSO
- **No Rate Limiting**: Could be overwhelmed by requests
- **Memory Management**: No dynamic batch size adjustment

### Planned Improvements
- Response caching with Redis
- Streaming responses for large batches
- Rate limiting per token
- Dynamic GPU memory management
- Multi-GPU support via vLLM
- Model hot-swapping without restart

## Troubleshooting

### Model Won't Load
- **CUDA out of memory**: Try smaller model or 4-bit quantization
- **Module not found**: Check CUDA/PyTorch installation
- **Download fails**: Check internet connection, HuggingFace access

### Tags Not Matching Existing
- **Too strict threshold**: Lower `SIMILARITY_THRESHOLD` in .env
- **Embedding mismatch**: Ensure same model for all tag embeddings
- **Cache issues**: Restart service to clear cache

### Slow Performance
- **GPU not used**: Check `DEVICE=cuda` in .env
- **Large model**: Switch to smaller model (2B instead of 9B)
- **Many concurrent requests**: Add more workers or queue jobs

### Worker Not Processing
- **Redis not running**: Check Redis connection
- **Wrong queue name**: Verify `REDIS_QUEUE_NAME` matches
- **Model not loaded**: Check worker logs for loading errors

## Future Enhancements

### Short Term
- [ ] Response caching with TTL
- [ ] Batch size optimization
- [ ] Confidence threshold tuning UI
- [ ] Model performance comparison tool

### Medium Term
- [ ] Multi-model ensemble voting
- [ ] Custom prompt template editor
- [ ] Tag relationship detection
- [ ] Historical tag trend analysis

### Long Term
- [ ] Fine-tuning on verified tags
- [ ] Transfer learning for wiki-specific models
- [ ] Automated prompt optimization
- [ ] Multi-language support
- [ ] Image-based tag suggestions
- [ ] Cross-wiki tag recommendations

## Resources

### Documentation
- [Requirements & Architecture](../tagging_api/readme.md)
- [Quick Start Guide](../tagging_api/README_QUICK.md)
- [AI Tagging Integration Guide](AI_TAGGING_GUIDE.md)

### External Links
- [Gemma Models](https://huggingface.co/google/gemma-2-2b-it)
- [Sentence Transformers](https://www.sbert.net/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Redis Queue (RQ)](https://python-rq.org/)

---

**Document Version**: 1.0.0  
**Last Updated**: 2026-01-19  
**Status**: Living document - updated as feature progresses
