# GitHub Copilot Instructions for Wiki Application

## Project Overview

This is a full-stack AI-powered wiki application with semantic search capabilities. The project consists of multiple interconnected services that work together.

## Changelog
- All notable changes to this project will be documented CHANGELOG.md.
- The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
- and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Readme
- Location: `README.md` in the project root.
- Contains setup instructions, features, and usage details.
- Any time project changes are made that impact the readme, update it accordingly.

## Features and Bugfixes
- Location: `features_and_bugfixes.md` in the project root.
- Lists planned features and bugfixes.
- Users may prompt to fix issues listed here or implement new features.
- Check off the new features or bugfixes as they are completed.

## Large Feature Documentation
- Major features (e.g., AI semantic search, embedding service) have dedicated docs in `large-feature-documentation/`.
- These documents provide in-depth explanations, architecture diagrams, and design decisions.
- Update these docs when significant changes are made to the respective features.
- When starting on new large features, add a new markdown file in that directory.

## Architecture

### Core Services (4 components)
1. **Backend API** (`/app`) - Flask REST API on port 5000
2. **Frontend** (`/frontend`) - React + Vite SPA on port 3000
3. **Embedding Service** (`/embedding_service`) - GPU-accelerated Flask microservice on port 8001
4. **Background Worker** (`/worker.py`) - RQ worker for async embedding generation

### Infrastructure
- **PostgreSQL 16** with pgvector extension (vector similarity search)
- **Redis 7** for RQ task queue and caching
- **Docker Compose** orchestrates PostgreSQL and Redis

## Tech Stack

### Backend
- Flask 3.x with SQLAlchemy ORM
- PostgreSQL with pgvector for vector embeddings
- JWT authentication (Flask-JWT-Extended)
- Marshmallow for validation
- Redis Queue (RQ) for background tasks
- sentence-transformers for embeddings

### Frontend
- React 18 with Vite
- React Router v6
- Toast UI Editor for markdown
- Lucide React for icons
- Context API for state (auth, theme, search)

## Key Patterns & Conventions

### Backend Code Style
- Use Flask blueprints for route organization (`app/routes/`)
- SQLAlchemy models in `app/models/models.py`
- Services in `app/services/` for business logic
- Background tasks in `app/tasks/` using RQ decorators
- JWT tokens required for protected endpoints
- Return JSON responses with consistent error format

### Frontend Code Style
- Functional components with hooks
- Context providers in `frontend/src/context/`
- API calls in `frontend/src/services/api.js`
- Pages in `frontend/src/pages/`
- Reusable components in `frontend/src/components/`
- CSS modules or scoped styles preferred

### Database Patterns
- All models inherit from Base with common fields (id, created_at, updated_at)
- Soft deletes not used - hard deletes only
- Foreign keys with CASCADE delete relationships
- Use SQLAlchemy relationships for joins
- Vector embeddings stored in `page_embeddings` table with pgvector

### API Conventions
- RESTful endpoints under `/api/` prefix
- Authentication: `Authorization: Bearer <token>` header
- Error responses: `{"error": "message", "code": "error_code"}`
- Success responses: `{"data": {...}}`
- File uploads: multipart/form-data with 16MB limit

## Important Locations

### Configuration
- `app/config.py` - Flask config classes
- `.env` - Environment variables (not in git)
- `.env.example` - Template for env vars
- `.env.docker` - Template for docker local development env vars
- `docker-compose.yml` - Database and Redis setup

### Models & Database
- `app/models/models.py` - All SQLAlchemy models
- `migrations/` - Alembic database migrations
- Models: User, Wiki, Page, PageRevision, Attachment, Member, PageEmbedding

### Routes
- `app/routes/auth.py` - User registration, login, profile
- `app/routes/wikis.py` - Wiki CRUD, members, public listing
- `app/routes/pages.py` - Page CRUD, revisions, hierarchy
- `app/routes/attachments.py` - File uploads and downloads
- `app/routes/search.py` - Keyword search
- `app/routes/semantic_search.py` - AI semantic & hybrid search

### AI/ML Components
- `embedding_service/app.py` - Standalone embedding microservice
- `app/services/embeddings.py` - HTTP client for embedding service
- `app/services/chunking.py` - Markdown-aware text splitting
- `app/tasks/embedding_tasks.py` - Background embedding generation
- Model: `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions)

### Frontend Pages
- `Home.jsx` - Public homepage with wiki browsing
- `Dashboard.jsx` - User's wiki management
- `WikiLayout.jsx` - Wiki navigation and page tree
- `PageView.jsx` - Markdown page display
- `PageEdit.jsx` - Toast UI markdown editor
- `UserSettings.jsx` - Profile, wikis, account settings
- `SemanticSearchPage.jsx` - AI search interface

## Development Workflow

### Starting the Application
```bash
# From frontend directory - starts all 4 services
npm run dev

# Or individually:
npm run dev:frontend        # React dev server
npm run dev:api            # Flask API server  
npm run dev:embedding-service  # Embedding microservice
npm run dev:worker         # RQ background worker
```

### Database Migrations
```bash
flask db migrate -m "description"
flask db upgrade
```

### Running Tests
```bash
pytest                     # Backend tests
cd frontend && npm test    # Frontend tests
```

## Common Tasks

### Adding a New Route
1. Create route function in appropriate blueprint (`app/routes/`)
2. Use `@bp.route()` decorator
3. Add `@jwt_required()` for protected routes
4. Validate input with Marshmallow schema
5. Return JSON response

### Adding a New Model
1. Add model class to `app/models/models.py`
2. Run `flask db migrate -m "Add ModelName"`
3. Run `flask db upgrade`
4. Create corresponding Marshmallow schema if needed

### Adding AI Features
1. Text chunking: Use `app/services/chunking.py`
2. Embeddings: Call embedding service via `app/services/embeddings.py`
3. Background processing: Use RQ task in `app/tasks/`
4. Vector search: Query `PageEmbedding` model with pgvector operators

### Adding Frontend Components
1. Create component in `frontend/src/components/`
2. Import and use in pages
3. Use Context for shared state (auth, theme)
4. API calls via `services/api.js`

## Dependencies & Versions

### Backend
- Python 3.9+
- Flask 3.x
- SQLAlchemy 2.x
- psycopg2-binary (PostgreSQL driver)
- pgvector (vector extension)
- torch + sentence-transformers (embeddings)
- redis + rq (task queue)

### Frontend
- React 18
- Vite 5
- React Router 6
- @toast-ui/editor 3.x
- axios for HTTP

## Security Notes

- JWT tokens expire in 1 hour (access) and 30 days (refresh)
- Passwords hashed with bcrypt
- File upload restrictions: 16MB max, allowed extensions validated
- CORS configured for localhost:3000 and localhost:5173
- SQL injection prevented by SQLAlchemy ORM
- XSS prevention via React's built-in escaping

## Performance Considerations

- Embedding generation runs in background (RQ worker)
- Image uploads limited to 16MB
- Vector search uses HNSW index on embeddings (configure in production)
- Chunk size: ~400 tokens with 50 token overlap
- Batch embeddings when possible

## Testing Approach

- Use pytest for backend tests
- Test database uses separate PostgreSQL instance
- Mock embedding service in tests
- Frontend tests with React Testing Library

## Future Enhancement Areas

1. **Auto-linking** - Use embeddings + LLM to suggest related page links
2. **Page suggestions** - Analyze content gaps, suggest topics
3. **Smart summaries** - Auto-generate TL;DR sections
4. **RAG Q&A** - Question answering over wiki content
5. **Real-time collaboration** - WebSocket-based live editing

## Troubleshooting

### Embedding Service Issues
- Check GPU availability: `nvidia-smi`
- Verify service running on port 8001
- Check EMBEDDING_SERVICE_URL in .env

### Database Connection
- Ensure Docker containers running: `docker-compose ps`
- Check DATABASE_URL in .env
- Verify pgvector extension installed: `SELECT * FROM pg_extension WHERE extname = 'vector';`

### Redis/RQ Issues
- Verify Redis running: `redis-cli ping`
- Check worker logs: Worker runs in foreground
- Inspect RQ dashboard: `rq info` (if rq-dashboard installed)

### Frontend Build Issues
- Clear node_modules: `rm -rf node_modules package-lock.json && npm install`
- Check Node version: 18+ required
- Verify API base URL in api.js

## Git Workflow

- Main development on `main` branch
- Feature branches: `feature/description`
- Commit messages: Conventional commits style
- Don't commit: `.env`, `uploads/`, `node_modules/`, `__pycache__/`
