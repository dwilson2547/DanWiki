# AI-Powered Wiki Application

A modern full-stack wiki application with user management, hierarchical pages, file attachments, and a beautiful React UI with dark mode support.

## Features

### Core Features
- **User Management**: Registration, authentication with JWT, role-based permissions
- **Multiple Wikis**: Users can create and manage multiple wikis with public/private visibility
- **Public Home Page**: Browse public wikis organized by author without authentication
- **Hierarchical Pages**: Pages can have parent-child relationships for organized content
- **Rich Markdown Editor**: Toast UI Editor with image upload and syntax highlighting
- **Syntax Highlighting**: Support for 30+ programming languages in code blocks
- **File Attachments**: Upload images and documents to pages with drag-and-drop
- **Revision History**: Track changes with ability to restore previous versions
- **Collaboration**: Share wikis with team members (viewer, editor, admin roles)
- **Bulk Import**: Create entire wiki structures from .zip or .tar.gz archives with automatic page hierarchy
- **Tagging System**: Organize pages with tags, supports frontmatter YAML metadata
- **AI-Powered Semantic Search**: Vector similarity search using locally-run open source models
  - Three search modes: AI Search (semantic), Hybrid (semantic + keyword), Traditional (keyword)
  - Automatic embedding generation via background tasks when pages are created or edited
  - Intelligent markdown-aware text chunking for long documents
  - GPU-accelerated embedding service using sentence-transformers
  - Adjustable similarity thresholds and hybrid search weights

### User Interface
- **Dark Mode**: Full theme support with light and dark modes
- **User Settings**: Comprehensive settings page for profile, appearance, and wiki management
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **User Avatars**: Customizable profile pictures with initials fallback
- **Modern UI**: Clean, intuitive interface built with React

## Tech Stack

### Backend
- **Framework**: Flask with SQLAlchemy ORM
- **Database**: PostgreSQL with pgvector extension for vector similarity search
- **Authentication**: JWT with access/refresh tokens (Flask-JWT-Extended)
- **Validation**: Marshmallow schemas
- **Task Queue**: Redis Queue (RQ) for background embedding generation
- **AI/ML**: sentence-transformers for embeddings, tiktoken for text chunking
- **Embedding Service**: Standalone Flask microservice with GPU support

### Frontend
- **Framework**: React 18 with Vite
- **Router**: React Router v6
- **Editor**: Toast UI Editor with Prism.js syntax highlighting
- **Icons**: Lucide React
- **State**: Context API for auth, theme, and search management

### Infrastructure
- **Containerization**: Docker Compose for PostgreSQL and Redis
- **Vector Database**: PostgreSQL 16 with pgvector extension
- **Message Queue**: Redis 7 with persistence for background tasks
- **Worker Process**: RQ worker for asynchronous embedding generation

## Quick Start

### 1. Setup Environment

```bash
cd wiki-app
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Start Docker Services

Start PostgreSQL with pgvector and Redis:

```bash
docker-compose up -d
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings:
# - DATABASE_URL (PostgreSQL connection string)
# - REDIS_URL (Redis connection string)
# - EMBEDDING_SERVICE_URL (embedding microservice URL, default: http://localhost:8001)
```

### 4. Initialize Database

```bash
flask db init
flask db migrate -m "Initial migration with embeddings and tags support"
flask db upgrade
```

### 5. Seed Demo Data (Optional)

```bash
flask seed-demo
```

### 6. Install Frontend Dependencies

```bash
cd frontend
npm install
```

### 7. Start All Services

From the `frontend` directory, start all services concurrently (frontend, API, embedding service, and worker):

```bash
npm run dev
```

This will start:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **Embedding Service**: http://localhost:8001
- **Background Worker**: RQ worker for embedding tasks

Alternatively, you can start each service individually in separate terminals:

```bash
# Terminal 1: Frontend
cd frontend
npm run dev:frontend

# Terminal 2: Backend API
python run.py

# Terminal 3: Embedding Service
cd embedding_service
python app.py

# Terminal 4: Background Worker
python worker.py
```

### 8. Try Bulk Import (Optional)

Create a sample wiki archive and test the bulk import feature:

```bash
python create_sample_archive.py
# This creates sample_wiki.zip - use it in the UI or via API
```

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login and get tokens |
| POST | `/api/auth/refresh` | Refresh access token |
| GET | `/api/auth/me` | Get current user |
| PATCH | `/api/auth/me` | Update profile (display name, avatar) |
| DELETE | `/api/auth/me` | Delete account (with/without wikis) |
| POST | `/api/auth/change-password` | Change password |

### Wikis

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/wikis` | List user's wikis |
| GET | `/api/wikis/public` | List all public wikis (grouped by author) |
| POST | `/api/wikis` | Create wiki |
| POST | `/api/wikis/import` | Create wiki from archive (.zip, .tar.gz) |
| GET | `/api/wikis/:id` | Get wiki |
| PATCH | `/api/wikis/:id` | Update wiki |
| DELETE | `/api/wikis/:id` | Delete wiki |
| POST | `/api/wikis/:id/import` | Import archive into existing wiki |
| GET | `/api/wikis/:id/pages/tree` | Get hierarchical page tree |
| GET | `/api/wikis/:id/members` | List members |
| POST | `/api/wikis/:id/members` | Add member |
| PATCH | `/api/wikis/:id/members/:uid` | Update member role |
| DELETE | `/api/wikis/:id/members/:uid` | Remove member |

### Pages

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/wikis/:id/pages` | List pages (flat or tree) |
| POST | `/api/wikis/:id/pages` | Create page |
| GET | `/api/wikis/:id/pages/:pid` | Get page |
| GET | `/api/wikis/:id/pages/by-path/:path` | Get page by path |
| PATCH | `/api/wikis/:id/pages/:pid` | Update page |
| DELETE | `/api/wikis/:id/pages/:pid` | Delete page |
| POST | `/api/wikis/:id/pages/:pid/move` | Move page |
| GET | `/api/wikis/:id/pages/:pid/children` | Get children |
| GET | `/api/wikis/:id/pages/:pid/revisions` | Get revisions |
| POST | `/api/wikis/:id/pages/:pid/restore/:rid` | Restore revision |

### Attachments

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/wikis/:wid/pages/:pid/attachments` | List attachments |
| POST | `/api/wikis/:wid/pages/:pid/attachments` | Upload file |
| POST | `/api/wikis/:wid/pages/:pid/upload-image` | Upload image (editor) |
| GET | `/api/attachments/:id` | Get attachment info |
| GET | `/api/attachments/:id/download` | Download file |
| GET | `/api/attachments/:id/view` | View inline |
| DELETE | `/api/attachments/:id` | Delete attachment |

### Search

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/search/pages?q=...` | Search all pages (keyword) |
| GET | `/api/search/wikis/:id/pages?q=...` | Search wiki pages (keyword) |
| GET | `/api/search/users?q=...` | Search users |
| POST | `/api/search/semantic` | AI-powered semantic search |
| POST | `/api/search/hybrid` | Hybrid search (semantic + keyword) |

## API Examples

### Register User
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"john","email":"john@example.com","password":"securepass123"}'
```

### Login
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"john","password":"securepass123"}'
```

### Create Wiki (with token)
```bash
curl -X POST http://localhost:5000/api/wikis \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{"name":"My Knowledge Base","description":"Personal notes"}'
```

### Create Page
```bash
curl -X POST http://localhost:5000/api/wikis/1/pages \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{"title":"Getting Started","content":"# Welcome\n\nThis is my first page."}'
```

### Create Child Page
```bash
curl -X POST http://localhost:5000/api/wikis/1/pages \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{"title":"Sub Topic","content":"Details here...","parent_id":1}'
```

### Import Wiki from Archive
```bash
curl -X POST http://localhost:5000/api/wikis/import \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "archive=@my-wiki.zip" \
  -F "name=My Imported Wiki" \
  -F "description=Imported from archive" \
  -F "is_public=false"
```

### Upload Image
```bash
curl -X POST http://localhost:5000/api/wikis/1/pages/1/upload-image \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@/path/to/image.png"
```

## Frontend Application

The application includes a complete React frontend located in the `frontend/` directory.

### Key Features

- **Public Home**: Browse public wikis without login
- **User Dashboard**: Manage your wikis and settings
- **Markdown Editor**: Toast UI Editor with image upload and syntax highlighting
- **Dark Mode**: Toggle between light and dark themes
- **User Settings**: Manage profile, avatars, wikis, and account
- **AI Search Page**: Dedicated semantic search interface with three modes and adjustable parameters
- **Bulk Import**: Upload .zip or .tar.gz archives to create entire wiki structures (see [BULK_IMPORT.md](BULK_IMPORT.md))

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Editor Image Upload Integration

The editor supports image upload via drag-and-drop or paste. Images are uploaded to the `/upload-image` endpoint:

```javascript
// Toast UI Editor example
const editor = new Editor({
  hooks: {
    addImageBlobHook: async (blob, callback) => {
      const formData = new FormData();
      formData.append('file', blob);
      
      const response = await fetch(
        `/api/wikis/${wikiId}/pages/${pageId}/upload-image`,
        {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` },
          body: formData
        }
      );
      
      const data = await response.json();
      callback(data.url, 'uploaded image');
    }
  }
});
```

## Project Structure

```
wiki-app/
├── app/                      # Backend (Flask)
│   ├── __init__.py          # App factory
│   ├── config.py            # Configuration
│   ├── models/
│   │   ├── __init__.py
│   │   └── models.py        # SQLAlchemy models (Page, Wiki, Tag, etc.)
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py          # Authentication & user management
│   │   ├── wikis.py         # Wiki CRUD & public listing
│   │   ├── pages.py         # Page CRUD & revisions
│   │   ├── attachments.py   # File handling & uploads
│   │   ├── search.py        # Keyword search functionality
│   │   ├── semantic_search.py  # AI semantic & hybrid search
│   │   └── bulk_import.py   # Archive import endpoints
│   ├── services/
│   │   ├── chunking.py      # Markdown-aware text chunking
│   │   ├── embeddings.py    # Embedding service HTTP client
│   │   └── archive_import.py   # Archive processing & import logic
│   └── tasks/
│       └── embedding_tasks.py  # RQ background tasks for embeddings
├── embedding_service/        # GPU-accelerated embedding microservice
│   ├── app.py               # Flask app with /embed endpoint
│   └── requirements.txt     # sentence-transformers, torch, etc.
├── frontend/                 # Frontend (React)
│   ├── src/
│   │   ├── components/      # Reusable components
│   │   │   ├── MarkdownEditor.jsx
│   │   │   ├── UserMenu.jsx
│   │   │   ├── SemanticSearch.jsx  # AI search component
│   │   │   └── ...
│   │   ├── pages/           # Route pages
│   │   │   ├── Home.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   ├── UserSettings.jsx
│   │   │   ├── WikiLayout.jsx
│   │   │   ├── PageView.jsx
│   │   │   ├── SemanticSearchPage.jsx  # Dedicated AI search page
│   │   │   └── ...
│   │   ├── context/         # State management
│   │   │   ├── AuthContext.jsx
│   │   │   └── ThemeContext.jsx
│   │   ├── services/        # API clients
│   │   │   └── api.js       # Including semantic search APIs
│   │   ├── styles/          # CSS files
│   │   │   ├── index.css
│   │   │   ├── prism-theme.css
│   │   │   └── semantic-search.css
│   │   └── App.jsx          # Main app component
│   ├── package.json
│   └── vite.config.js
├── uploads/                  # File uploads directory
├── docker-compose.yml        # PostgreSQL + Redis containers
├── worker.py                 # RQ worker for background tasks
├── requirements.txt          # Python dependencies
├── run.py                   # Backend entry point
├── create_sample_archive.py  # Script to create sample wiki archive
├── .env.example
├── BULK_IMPORT.md           # Bulk import feature documentation
└── CHANGELOG.md             # Version history
```

## AI-Powered Features

### Semantic Search (Implemented)

The application includes a complete semantic search implementation using locally-run open source models:

- **Vector Database**: PostgreSQL with pgvector extension for efficient similarity search
- **Embedding Model**: sentence-transformers/all-MiniLM-L6-v2 (384 dimensions)
- **Background Processing**: Redis Queue (RQ) for asynchronous embedding generation
- **Intelligent Chunking**: Markdown-aware text splitting with ~400 token chunks and 50 token overlap
- **GPU Acceleration**: Standalone Flask microservice for fast embedding generation
- **Search Modes**:
  - **AI Search**: Pure vector similarity search
  - **Hybrid Search**: Combines semantic and keyword search with adjustable weights
  - **Traditional**: Standard keyword search

### Semantic Search API

**AI Search** (POST `/api/search/semantic`):
```json
{
  "query": "how to optimize database queries",
  "threshold": 0.5,
  "limit": 10
}
```

**Hybrid Search** (POST `/api/search/hybrid`):
```json
{
  "query": "database performance",
  "semantic_weight": 0.7,
  "keyword_weight": 0.3,
  "threshold": 0.5,
  "limit": 10
}
```

### Future AI Enhancements

1. **Auto-Linking**: Use embeddings + LLM to suggest links between related pages
2. **Page Suggestions**: Analyze content gaps and suggest new topics to cover
3. **Smart Summaries**: Auto-generate page summaries and TL;DR sections
4. **Question Answering**: RAG-based Q&A over wiki content

## License

MIT
