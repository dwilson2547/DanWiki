# Embedding Microservice

A standalone Flask service for generating text embeddings using sentence-transformers. Designed to run on a GPU machine for fast embedding generation.

## Features

- **Fast GPU-accelerated embeddings** using sentence-transformers
- **Batch processing** for efficient embedding generation
- **Configurable models** - default: `all-MiniLM-L6-v2` (384 dimensions)
- **REST API** with simple POST endpoint
- **Health checks** and model information endpoints

## Installation

### Requirements

- Python 3.9+
- CUDA-capable GPU (recommended) or CPU fallback
- CUDA toolkit and drivers (for GPU acceleration)

### Setup

```bash
cd embedding_service

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Set environment variables or create a `.env` file:

```bash
# Model configuration
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
DEVICE=cuda  # or 'cpu' for CPU-only
BATCH_SIZE=32
MAX_SEQ_LENGTH=256

# Server configuration
HOST=0.0.0.0
PORT=8001
```

### Available Models

Popular models you can use:

| Model | Dimension | Max Tokens | Speed | Quality |
|-------|-----------|------------|-------|---------|
| `all-MiniLM-L6-v2` | 384 | 256 | Very Fast | Good |
| `all-mpnet-base-v2` | 768 | 384 | Medium | Better |
| `all-MiniLM-L12-v2` | 384 | 256 | Fast | Good |

## Usage

### Start the Service

```bash
python app.py
```

The service will start on `http://0.0.0.0:8001`

### API Endpoints

#### POST /embed

Generate embeddings for text(s).

**Request:**
```json
{
  "texts": "Your text here",
  "normalize": true
}
```

Or multiple texts:
```json
{
  "texts": ["First text", "Second text", "Third text"],
  "normalize": true
}
```

**Response:**
```json
{
  "embeddings": [
    [0.123, -0.456, 0.789, ...],
    [0.234, -0.567, 0.890, ...]
  ],
  "dimension": 384,
  "model": "sentence-transformers/all-MiniLM-L6-v2",
  "count": 2,
  "processing_time_ms": 45.2
}
```

**Example with curl:**
```bash
curl -X POST http://localhost:8001/embed \
  -H "Content-Type: application/json" \
  -d '{"texts": "Hello, world!"}'
```

**Example with Python:**
```python
import requests

response = requests.post(
    'http://localhost:8001/embed',
    json={'texts': ['Text 1', 'Text 2']}
)
data = response.json()
embeddings = data['embeddings']  # List of embedding vectors
```

#### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "model": "sentence-transformers/all-MiniLM-L6-v2",
  "device": "cuda",
  "embedding_dimension": 384
}
```

#### GET /info

Get detailed model information.

**Response:**
```json
{
  "model_name": "sentence-transformers/all-MiniLM-L6-v2",
  "embedding_dimension": 384,
  "max_seq_length": 256,
  "device": "cuda",
  "batch_size": 32
}
```

## Deployment

### Docker Deployment (Recommended)

Create a `Dockerfile` in this directory:

```dockerfile
FROM pytorch/pytorch:2.1.2-cuda12.1-cudnn8-runtime

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 8001

CMD ["python", "app.py"]
```

Build and run:
```bash
docker build -t embedding-service .
docker run --gpus all -p 8001:8001 -e DEVICE=cuda embedding-service
```

### Production Considerations

1. **Use Gunicorn** for production:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:8001 --timeout 120 app:app
   ```

2. **Enable HTTPS** with nginx reverse proxy

3. **Add authentication** if exposed to public network

4. **Monitor GPU usage** and adjust `BATCH_SIZE` accordingly

5. **Set up logging** to file for debugging

## Performance

- **Single text**: ~10-20ms on GPU
- **Batch of 32 texts**: ~50-100ms on GPU
- **CPU fallback**: ~10x slower than GPU

## Troubleshooting

### CUDA out of memory

Reduce `BATCH_SIZE`:
```bash
export BATCH_SIZE=16
```

### Model download fails

Models are downloaded from Hugging Face on first run. Ensure internet connectivity.

### Slow performance

- Check `DEVICE=cuda` is set
- Verify GPU is available: `nvidia-smi`
- Increase `BATCH_SIZE` for batch requests

## License

MIT License
