# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered wiki application with semantic search capabilities. Full-stack system with 5 core services:
- **Backend API** (`/app`) - Flask REST API on port 5000
- **Frontend** (`/frontend`) - React + Vite SPA on port 3000
- **Embedding Service** (`/embedding_service`) - GPU-accelerated Flask microservice on port 8001
- **Background Worker** (`/worker`) - RQ worker for async embedding generation
- **Tagging API** (`/tagging_api`) - FastAPI LLM-based auto-tagging service

Infrastructure: PostgreSQL 16 with pgvector (vector search), Redis 7 (task queue).

## Common Commands

```bash
# Start all services (from frontend directory)
cd frontend && npm run dev

# Start individual services
npm run dev:frontend      # React dev server
npm run dev:api           # Flask API
npm run dev:embedding-service  # Embedding microservice
npm run dev:worker        # RQ background worker

# Start infrastructure
docker-compose up -d      # PostgreSQL + Redis

# Database migrations
flask db migrate -m "description"
flask db upgrade

# Build frontend
cd frontend && npm run build

# Run tests
pytest                    # Backend tests
python tests/test_slug_uniqueness.py  # Run specific test
```

## Architecture

### Backend Structure (`/app`)
- `routes/` - Flask blueprints: auth, wikis, pages, attachments, search, semantic_search, tags, bulk_import, admin
- `models/models.py` - SQLAlchemy models: User, Wiki, Page, PageRevision, Attachment, Member, PageEmbedding, Tag
- `services/` - Business logic: embeddings.py (HTTP client), chunking.py (markdown-aware splitting), archive_import.py
- `tasks/` - RQ background jobs: embedding_tasks.py
- `config.py` - Flask configuration

### Frontend Structure (`/frontend/src`)
- `pages/` - Route components: Dashboard, WikiLayout, PageView, PageEdit, SemanticSearchPage, UserSettings
- `components/` - Reusable: MarkdownEditor (Toast UI), PageTree, Search, Modal
- `context/` - React Context providers for auth, theme, search state
- `services/api.js` - Axios API client with JWT handling

### AI/ML Components
- Embedding model: `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions)
- Vector storage: pgvector in `page_embeddings` table
- Chunking: ~400 tokens with 50 token overlap
- Tagging: LLM-based with configurable prompts in `/tagging_api/prompts/`

## Key Patterns

### API Conventions
- RESTful endpoints under `/api/` prefix
- Auth: `Authorization: Bearer <token>` header
- Error format: `{"error": "message", "code": "error_code"}`
- Success format: `{"data": {...}}`
- File uploads: multipart/form-data, 16MB limit

### Database
- All models have id, created_at, updated_at
- Hard deletes (no soft delete)
- CASCADE delete on foreign keys
- Vector search uses HNSW index on embeddings

### Frontend
- Functional components with hooks
- Context API for shared state (no Redux)
- API calls via `services/api.js`
- Toast UI Editor for markdown editing

## Environment Setup

Copy `.env.example` to `.env`. Key variables:
- `DATABASE_URL` - PostgreSQL connection (or SQLite for dev)
- `SECRET_KEY`, `JWT_SECRET_KEY` - Security keys
- `EMBEDDING_SERVICE_URL` - Embedding service endpoint
- `CORS_ORIGINS` - Allowed frontend origins

## Documentation

- `CHANGELOG.md` - Version history (Keep a Changelog format)
- `large-feature-documentation/` - In-depth docs for major features (semantic search, bulk import, tagging)
- Update these when making significant feature changes
