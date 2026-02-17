# Wiki Application - Semantic Search Feature

## Quick Start Guide

### Prerequisites
- Docker and Docker Compose
- Python 3.9+
- GPU machine with CUDA (for embedding service)

### 1. Start Infrastructure (5 minutes)

```bash
# Start PostgreSQL + Redis
docker-compose up -d

# Verify running
docker ps
```

### 2. Setup Embedding Microservice on GPU Machine (10 minutes)

```bash
cd embedding_service
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start service
python app.py
```

### 3. Setup Main Application (5 minutes)

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.docker .env
# Edit .env and set EMBEDDING_SERVICE_URL to your GPU machine

# Run migrations
flask db upgrade

# Start worker
python worker.py &

# Start app
flask run
```

### 4. Test It Works

```bash
# Create a test page (get JWT token first via login)
curl -X POST http://localhost:5000/api/wikis/1/pages \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Page", "content": "This is a test page about Python programming and machine learning."}'

# Wait a few seconds for embedding generation...

# Search semantically
curl "http://localhost:5000/api/search/semantic?q=machine+learning" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Architecture Summary

```
User Request → Flask API → PostgreSQL (data + vectors)
                    ↓
              Redis Queue
                    ↓
              RQ Worker → GPU Embedding Service → Store Embeddings
                                                        ↓
                                                  Vector Search
```

---

## Key Files

| File/Directory | Purpose |
|----------------|---------|
| `docker-compose.yml` | PostgreSQL + Redis setup |
| `embedding_service/` | GPU microservice for embeddings |
| `app/models/models.py` | PageEmbedding model |
| `app/services/chunking.py` | Text chunking logic |
| `app/services/embeddings.py` | Embedding client |
| `app/tasks/embedding_tasks.py` | Background tasks |
| `app/routes/semantic_search.py` | Search endpoints |
| `worker.py` | RQ worker script |
| `SEMANTIC_SEARCH_SETUP.md` | Full documentation |

---

## API Endpoints

### Semantic Search
```
GET /api/search/semantic?q=your+query
```

Returns AI-powered semantic search results with similarity scores.

### Hybrid Search
```
GET /api/search/hybrid?q=your+query&semantic_weight=0.7
```

Combines keyword and semantic search for best results.

### Original Keyword Search
```
GET /api/search/pages?q=your+query
```

Traditional keyword-based search (still available).

---

## Configuration

Key environment variables in `.env`:

```bash
# Database (Docker PostgreSQL)
DATABASE_URL=postgresql://wiki_user:wiki_password_dev_only@localhost:5432/wiki_db

# Redis (Docker Redis)
REDIS_URL=redis://localhost:6379/0

# GPU Embedding Service
EMBEDDING_SERVICE_URL=http://your-gpu-machine:8001
EMBEDDING_DIMENSION=384
MAX_CHUNK_TOKENS=256
CHUNK_OVERLAP_TOKENS=50
```

---

## How It Works

1. **Page Created/Updated** → Task queued
2. **RQ Worker** picks up task →
3. **Text Chunking** splits long docs into ~256 token chunks
4. **GPU Service** generates embeddings for each chunk
5. **Database** stores embeddings with pgvector
6. **Search** uses vector similarity (cosine distance)

---

## Monitoring

```bash
# Check worker status
ps aux | grep worker.py

# Check queue length
docker exec -it wiki-redis redis-cli
> LLEN rq:queue:embeddings
> exit

# Check embedding service
curl http://gpu-machine:8001/health

# View logs
docker logs wiki-postgres
docker logs wiki-redis
tail -f worker.log
```

---

## Troubleshooting

### No search results?
1. Check worker is running: `ps aux | grep worker`
2. Check embedding service: `curl http://gpu-machine:8001/health`
3. Verify page has embeddings: Check `embeddings_status` in database

### Slow searches?
1. Ensure vector index exists on `page_embeddings.embedding`
2. Adjust similarity threshold (lower = more results)
3. Check database query performance

### Worker not processing?
1. Check Redis connection
2. View worker logs for errors
3. Restart worker: `pkill -f worker.py && python worker.py &`

---

## Upgrading to Better Model

Want better search quality? Switch to `all-mpnet-base-v2`:

1. Update embedding service `.env`:
   ```
   EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
   ```

2. Update main app `.env`:
   ```
   EMBEDDING_DIMENSION=768
   ```

3. Alter database vector dimension:
   ```sql
   ALTER TABLE page_embeddings ALTER COLUMN embedding TYPE vector(768);
   ```

4. Regenerate embeddings:
   ```python
   from app.tasks import regenerate_all_embeddings
   regenerate_all_embeddings()
   ```

---

## Production Checklist

- [ ] Change default database passwords
- [ ] Enable HTTPS for embedding service
- [ ] Set up Nginx reverse proxy
- [ ] Configure Redis password
- [ ] Run multiple workers (4-8)
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Configure backup for PostgreSQL
- [ ] Use production WSGI server (gunicorn/uwsgi)
- [ ] Implement rate limiting on search endpoints

---

For complete documentation, see [SEMANTIC_SEARCH_SETUP.md](SEMANTIC_SEARCH_SETUP.md)
