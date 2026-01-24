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