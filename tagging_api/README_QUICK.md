# Wiki Tagging Microservice

Automated tag generation for wiki pages using local LLMs.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your settings (especially API_TOKEN)
   ```

3. **Start the service:**
   ```bash
   # Development mode
   uvicorn app:app --reload --port 8002
   
   # Production mode
   uvicorn app:app --host 0.0.0.0 --port 8002 --workers 1
   ```

4. **Start worker for batch processing (optional):**
   ```bash
   python worker.py
   ```

## Usage

### Synchronous Analysis

```bash
curl -X POST http://localhost:8002/analyze \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Flask Tutorial",
    "content": "# Introduction to Flask...",
    "existing_tags": [{"name": "python", "color": "#3776AB"}],
    "context": {"breadcrumbs": ["Programming", "Web Dev"]},
    "options": {"max_tags": 10, "min_confidence": 0.5}
  }'
```

### Batch Processing

```bash
# Queue batch job
curl -X POST http://localhost:8002/analyze/batch \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "pages": [
      {"page_id": 1, "title": "Page 1", "content": "..."},
      {"page_id": 2, "title": "Page 2", "content": "..."}
    ]
  }'

# Check job status
curl http://localhost:8002/jobs/{job_id} \
  -H "Authorization: Bearer your-token"
```

## Configuration

See `.env.example` for all configuration options.

### Model Selection

Edit `MODEL_NAME` in `.env`:
- `google/gemma-2-2b-it` - Fast, 4GB VRAM (default)
- `google/gemma-2-9b-it` - Better quality, 10GB VRAM
- `microsoft/Phi-3-mini-4k-instruct` - Good balance, 5GB VRAM

### Prompt Templates

Choose via `DEFAULT_PROMPT_TEMPLATE` or per-request:
- `detailed` - Comprehensive analysis (default)
- `quick` - Fast processing
- `technical` - Code-focused
- `general` - Balanced approach

## API Documentation

Once running, visit: http://localhost:8002/docs

## Project Structure

```
tagging_api/
├── app.py                 # FastAPI application
├── worker.py              # RQ worker for batch jobs
├── config.py              # Configuration management
├── models.py              # Pydantic models
├── llm_service.py         # LLM interaction logic
├── prompts/               # Prompt templates
│   ├── __init__.py
│   ├── detailed.py
│   ├── quick.py
│   ├── technical.py
│   └── general.py
├── requirements.txt
├── .env.example
└── readme.md
```

## Requirements

- Python 3.10+
- CUDA 11.8+ (for GPU)
- 8GB+ GPU VRAM (for Gemma 2B)
- Redis server

## See Also

- [Full Requirements Documentation](readme.md)
- [AI Tagging Integration Guide](../large-feature-documentation/AI_TAGGING_GUIDE.md)
