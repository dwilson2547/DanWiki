# Semantic Search Implementation Guide

This guide covers the complete setup and usage of the semantic search feature with embeddings.

## Architecture Overview

```
┌──────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Frontend   │────▶│ Flask API    │────▶│   PostgreSQL    │
└──────────────┘     └──────┬───────┘     │   + pgvector    │
                            │             └─────────────────┘
                            ▼
                     ┌──────────────┐
                     │    Redis     │
                     │ Task Queue   │
                     └──────┬───────┘
                            │
                            ▼
                     ┌──────────────┐     ┌─────────────────┐
                     │  RQ Worker   │────▶│  GPU Embedding  │
                     │  (Background)│     │   Microservice  │
                     └──────────────┘     └─────────────────┘
```

### Components

1. **PostgreSQL with pgvector** - Vector database for similarity search
2. **Redis** - Task queue for background processing
3. **RQ Workers** - Process embedding generation tasks
4. **Embedding Microservice** - GPU-accelerated embedding generation
5. **Flask API** - Main application with search endpoints

---

## Setup Instructions

### 1. Start PostgreSQL and Redis with Docker

```bash
cd /path/to/wiki-app

# Start containers
docker-compose up -d

# Verify containers are running
docker ps

# Check PostgreSQL logs
docker logs wiki-postgres

# Check Redis logs
docker logs wiki-redis
```

### 2. Setup Main Application

```bash
# Create/activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment config
cp .env.docker .env

# Edit .env and update EMBEDDING_SERVICE_URL to point to your GPU machine
# Example: EMBEDDING_SERVICE_URL=http://192.168.1.100:8001

# Run database migrations
flask db upgrade

# If migrations don't exist yet, create them:
flask db init
flask db migrate -m "Add embeddings support"
flask db upgrade
```

### 3. Setup Embedding Microservice (on GPU Machine)

```bash
# On your GPU machine
cd /path/to/wiki-app/embedding_service

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies (requires CUDA for GPU)
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
DEVICE=cuda
BATCH_SIZE=32
MAX_SEQ_LENGTH=256
HOST=0.0.0.0
PORT=8001
EOF

# Start the service
python app.py

# Test it's working
curl http://localhost:8001/health
```

### 4. Start RQ Workers

```bash
# On your main application server
cd /path/to/wiki-app

# Start worker (in a separate terminal)
python worker.py

# Or run multiple workers for parallel processing
python worker.py &
python worker.py &
```

### 5. Start Main Application

```bash
# Development mode
flask run

# Or with gunicorn (production)
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

---

## Database Migration

Create the migration for the new embedding tables:

```bash
flask db migrate -m "Add page embeddings and pgvector support"
```

The migration should include:

```python
# In the migration file
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

def upgrade():
    # Add embedding status to pages
    op.add_column('pages', sa.Column('embeddings_status', sa.String(20), default='pending'))
    op.add_column('pages', sa.Column('embeddings_updated_at', sa.DateTime(), nullable=True))
    
    # Create page_embeddings table
    op.create_table(
        'page_embeddings',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('page_id', sa.Integer(), sa.ForeignKey('pages.id'), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('chunk_text', sa.Text(), nullable=False),
        sa.Column('heading_path', sa.String(500)),
        sa.Column('token_count', sa.Integer()),
        sa.Column('embedding', Vector(384)),  # 384 dimensions for all-MiniLM-L6-v2
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    
    # Create indexes
    op.create_index('idx_page_embeddings_page_id', 'page_embeddings', ['page_id'])
    op.create_unique_constraint('unique_page_chunk', 'page_embeddings', ['page_id', 'chunk_index'])
    
    # Create vector similarity index (IVFFlat for fast search)
    op.execute('CREATE INDEX idx_page_embeddings_vector ON page_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)')

def downgrade():
    op.drop_index('idx_page_embeddings_vector', 'page_embeddings')
    op.drop_table('page_embeddings')
    op.drop_column('pages', 'embeddings_updated_at')
    op.drop_column('pages', 'embeddings_status')
```

Apply the migration:

```bash
flask db upgrade
```

---

## API Usage

### Semantic Search Endpoint

**Endpoint:** `GET /api/search/semantic`

Search using AI-powered semantic similarity.

**Parameters:**
- `q` (required): Search query
- `wiki_id` (optional): Limit to specific wiki
- `limit` (optional): Max results (default 20, max 100)
- `offset` (optional): Pagination offset
- `threshold` (optional): Minimum similarity score 0-1 (default 0.5)

**Example:**
```bash
curl -X GET "http://localhost:5000/api/search/semantic?q=how+to+install+python" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Response:**
```json
{
  "results": [
    {
      "embedding_id": 123,
      "page_id": 45,
      "chunk_index": 0,
      "chunk_text": "# Installation Guide\n\nTo install Python...",
      "heading_path": "Getting Started > Installation",
      "page_title": "Python Setup",
      "page_slug": "python-setup",
      "wiki_name": "Developer Docs",
      "similarity_score": 0.87,
      "page_url": "/wikis/1/pages/45"
    }
  ],
  "total_chunks": 5,
  "total_pages": 3,
  "unique_pages": 3,
  "query": "how to install python",
  "threshold": 0.5
}
```

### Hybrid Search Endpoint

**Endpoint:** `GET /api/search/hybrid`

Combines keyword and semantic search for best results.

**Parameters:**
- `q` (required): Search query
- `wiki_id` (optional): Limit to specific wiki
- `limit` (optional): Max results (default 20)
- `semantic_weight` (optional): Weight for semantic results 0-1 (default 0.7)

**Example:**
```bash
curl -X GET "http://localhost:5000/api/search/hybrid?q=authentication&semantic_weight=0.6" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## Monitoring & Management

### Check Task Queue Status

```bash
# Connect to Redis CLI
docker exec -it wiki-redis redis-cli

# Check queue length
LLEN rq:queue:embeddings

# View failed jobs
LLEN rq:queue:failed

# Exit
exit
```

### Monitor Workers

```bash
# View worker logs
tail -f worker.log

# Check worker process
ps aux | grep worker.py
```

### Regenerate All Embeddings

If you upgrade the embedding model or need to reprocess all pages:

```python
from app import create_app
from app.tasks import regenerate_all_embeddings

app = create_app()
with app.app_context():
    result = regenerate_all_embeddings()
    print(result)
```

### Check Embedding Service Health

```bash
curl http://your-gpu-machine:8001/health
curl http://your-gpu-machine:8001/info
```

---

## Configuration

### Environment Variables

**Main Application (.env):**
```bash
# Database
DATABASE_URL=postgresql://wiki_user:wiki_password_dev_only@localhost:5432/wiki_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Embedding Service
EMBEDDING_SERVICE_URL=http://gpu-machine:8001
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
MAX_CHUNK_TOKENS=256
CHUNK_OVERLAP_TOKENS=50
EMBEDDING_BATCH_SIZE=32
EMBEDDING_REQUEST_TIMEOUT=30
IVFFLAT_PROBES=10

# Workers
RQ_WORKER_COUNT=2
```

**Embedding Service (.env on GPU machine):**
```bash
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
DEVICE=cuda
BATCH_SIZE=32
MAX_SEQ_LENGTH=256
HOST=0.0.0.0
PORT=8001
```

---

## Upgrading the Embedding Model

To switch to a better model (e.g., `all-mpnet-base-v2`):

1. **Update embedding service:**
   ```bash
   # On GPU machine
   cd embedding_service
   # Edit .env
   EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
   # Restart service
   ```

2. **Update main app config:**
   ```bash
   # Edit .env
   EMBEDDING_DIMENSION=768  # all-mpnet-base-v2 has 768 dimensions
   ```

3. **Update database:**
   ```sql
   -- Create new migration or manually alter
   ALTER TABLE page_embeddings ALTER COLUMN embedding TYPE vector(768);
   ```

4. **Regenerate all embeddings:**
   ```python
   from app.tasks import regenerate_all_embeddings
   regenerate_all_embeddings()
   ```

---

## Troubleshooting

### Embeddings Not Generating

1. Check worker is running: `ps aux | grep worker.py`
2. Check Redis connection: `redis-cli ping`
3. Check embedding service: `curl http://gpu-machine:8001/health`
4. View worker logs for errors

### Slow Search Performance

1. Ensure vector index exists:
   ```sql
   SELECT indexname FROM pg_indexes WHERE tablename = 'page_embeddings';
   ```

2. Rebuild vector index if needed:
   ```sql
   REINDEX INDEX idx_page_embeddings_vector;
   ```

3. Adjust IVFFlat lists parameter for your dataset size

### Embedding Service Connection Errors

1. Check firewall rules between servers
2. Verify GPU machine is accessible: `ping gpu-machine`
3. Check service logs on GPU machine
4. Test with curl from main server:
   ```bash
   curl -v http://gpu-machine:8001/health
   ```

### High Memory Usage

1. Reduce `EMBEDDING_BATCH_SIZE` in config
2. Reduce `MAX_CHUNK_TOKENS` to create smaller chunks
3. Limit concurrent workers

---

## Performance Optimization

### For Large Wikis (1000+ pages)

1. **Increase IVFFlat lists:**
   ```sql
   -- lists = sqrt(total_rows), typically 100-1000
   CREATE INDEX ... USING ivfflat (embedding vector_cosine_ops) WITH (lists = 500)
   ```

2. **Use HNSW index (PG 16+):**
   ```sql
   CREATE INDEX ... USING hnsw (embedding vector_cosine_ops)
   ```

3. **Add more workers:**
   ```bash
   # Run 4-8 workers depending on CPU
   for i in {1..4}; do python worker.py & done
   ```

4. **Batch page creation:**
   - Create pages in bulk
   - Queue embeddings after batch complete

---

## Production Deployment

### Docker Compose Production

See `docker-compose.prod.yml` for production setup with:
- PostgreSQL with replication
- Redis with persistence
- Nginx reverse proxy
- Multiple RQ workers
- Monitoring with Prometheus/Grafana

### Security Considerations

1. **Change default passwords** in `docker-compose.yml`
2. **Use HTTPS** for embedding service communication
3. **Add authentication** to embedding service if exposed
4. **Limit API rate** for search endpoints
5. **Enable Redis password protection**

---

## Testing

```bash
# Test chunking
python -c "from app.services.chunking import chunk_page_content; print(chunk_page_content('Test', 'Long content...'))"

# Test embedding client
python -c "from app.services.embeddings import check_service_health; print(check_service_health())"

# Test search
curl -X GET "http://localhost:5000/api/search/semantic?q=test" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Support

For issues or questions:
1. Check logs: `docker logs wiki-postgres`, `docker logs wiki-redis`
2. Review worker logs
3. Check embedding service logs on GPU machine
4. Verify all services are running with `docker ps` and `ps aux | grep worker`
