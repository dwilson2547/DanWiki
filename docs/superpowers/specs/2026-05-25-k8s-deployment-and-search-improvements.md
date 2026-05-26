# DanWiki: K8s Deployment & Semantic Search Improvements

**Date:** 2026-05-25

## Scope

Two parallel tracks:

1. **Packaging & deployment** — Dockerfiles, Helm chart, ArgoCD manifests, pgvector PostgreSQL instances
2. **Semantic search improvements** — heading context in embeddings, page-level result grouping, relative score display, RRF hybrid fusion

## Constraints

- NFS storage only (no S3 dependency)
- No GPU nodes — tagging API/worker gated behind `tagging.enabled: false`
- Tagging API quality is unreviewed — keep it deployable but off by default
- MiniLM-L6-v2 stays as the embedding model (`EMBEDDING_MODEL` made configurable via env var for future swap)
- `nvidia/llama-nemotron-embed-vl-1b-v2` deferred as a future exploration task
- pgvector instances managed in `cluster_config` repo, not this repo
- HyDE and other LLM-in-search-path improvements deferred

---

## Part 1: Infrastructure & Deployment

### pgvector PostgreSQL (`cluster_config` repo)

Two new StatefulSets appended to `cluster_config/postgres/postgres.yaml` alongside the existing prod/dev pair.

| Name | Namespace | Image | Storage | Secret |
|---|---|---|---|---|
| `postgres-pgvector` | `postgres` | `pgvector/pgvector:pg16` | 50Gi `nfs-dataset` | `postgres-pgvector-credentials` |
| `postgres-pgvector-dev` | `postgres` | `pgvector/pgvector:pg16` | 20Gi `nfs-dataset` | `postgres-pgvector-dev-credentials` |

Init SQL via ConfigMap mounted at `/docker-entrypoint-initdb.d/init.sql` (same mechanism as `cluster_config/docker/postgres/init.sql`): `CREATE EXTENSION IF NOT EXISTS vector;`

Services expose both as ClusterIP on port 5432:
- `postgres-pgvector.postgres.svc.cluster.local`
- `postgres-pgvector-dev.postgres.svc.cluster.local`

Secrets must be created manually before ArgoCD sync (same pattern as existing postgres secrets). An `example_secret.yml` template is added to `cluster_config/example-secrets/`.

Resource profile matches existing `postgres-dev`: 1 CPU request / 2 CPU limit, 1Gi / 2Gi memory.

### Docker Images (4 images, 5 deployments)

| Image | Dockerfile location | Used by |
|---|---|---|
| `danwiki-backend` | `Dockerfile` (repo root) | `backend` deployment + `worker` deployment (different `command`) |
| `danwiki-frontend` | `frontend/Dockerfile` | `frontend` deployment |
| `danwiki-embedding` | `embedding_service/Dockerfile` | `embedding-service` deployment |
| `danwiki-tagging` | `tagging_api/Dockerfile` | `tagging-api` + `tagging-worker` deployments (different `command`) |

**Backend Dockerfile** — multi-stage not needed (no compiled assets). Python 3.12-slim base, installs `requirements.txt`, sets `FLASK_ENV=production`, entrypoint via `run.py`.

**Worker** reuses backend image — same `image:` reference in Helm, different `command: ["python", "worker/worker.py"]`.

**Frontend Dockerfile** — two-stage: Node 20-alpine builds `npm run build`, then Nginx alpine serves `/usr/share/nginx/html`. Nginx config proxies `/api/` to backend service.

**Embedding Dockerfile** — Python 3.12-slim, installs `embedding_service/requirements.txt`. Default `DEVICE=cpu` (no GPU). Model downloads on first start (or pre-baked into image via build arg).

**Tagging Dockerfile** — Python 3.12-slim, installs `tagging_api/requirements.txt`. Heavy image (~3GB with torch). `DEVICE=cpu` default; GPU override via env var when `tagging.enabled: true` with node affinity.

### Helm Chart (`helm/danwiki/`)

Follows the scrape-stack/gyopart self-managed Helm pattern: ArgoCD points at `helm/danwiki/` in this repo, `main` branch for prod, `dev` branch for dev.

**Chart structure:**
```
helm/danwiki/
  Chart.yaml
  values.yaml          # prod defaults
  values-dev.yaml      # dev overrides (smaller resources, dev DB, debug logging)
  templates/
    _helpers.tpl
    configmap.yaml
    ingress.yaml
    uploads-pvc.yaml
    backend/
      deployment.yaml
      service.yaml
    frontend/
      deployment.yaml
      service.yaml
    embedding-service/
      deployment.yaml
      service.yaml
    worker/
      deployment.yaml
    redis/
      deployment.yaml
      service.yaml
      pvc.yaml
    tagging/
      api-deployment.yaml      # {{ if .Values.tagging.enabled }}
      worker-deployment.yaml   # {{ if .Values.tagging.enabled }}
      service.yaml             # {{ if .Values.tagging.enabled }}
```

**Key values:**
```yaml
image:
  repository: ghcr.io/dwilson2547
  tag: latest
  pullPolicy: IfNotPresent

ingress:
  host: danwiki.local

database:
  host: postgres-pgvector.postgres.svc.cluster.local
  name: wiki_db
  secretName: danwiki-db-credentials

redis:
  storageSize: 1Gi

uploads:
  storageSize: 20Gi
  storageClass: nfs-client

embedding:
  model: sentence-transformers/all-MiniLM-L6-v2
  device: cpu

tagging:
  enabled: false

cors:
  origins: "https://danwiki.local"
```

**Storage:**
- `uploads-pvc.yaml` — `ReadWriteMany`, `nfs-client`, size from `values.yaml`. Mounted into backend at `/app/uploads` and worker at `/app/uploads`.
- Redis PVC — `ReadWriteOnce`, `nfs-client`, 1Gi. Redis runs with `--appendonly yes`.

**Ingress (Traefik IngressRoute):**
- `danwiki.local/api/*` → `backend:5000`
- `danwiki.local/*` → `frontend:80`
- Frontend Nginx also proxies `/api/` internally for SSR fallback (defense in depth).

**Secrets (created manually, not in chart):**
- `danwiki-db-credentials` — `DATABASE_URL`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- `danwiki-app-secrets` — `SECRET_KEY`, `JWT_SECRET_KEY`
- `danwiki-tagging-secrets` — `TAGGING_API_TOKEN` (only needed if `tagging.enabled: true`)

**CORS fix required:** `app/__init__.py` line 34 — replace hardcoded origin list with `os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')`.

### ArgoCD Manifests (`cluster_config/argocd/`)

`danwiki.yaml`:
```yaml
source:
  repoURL: https://github.com/dwilson2547/DanWiki.git
  targetRevision: main
  path: helm/danwiki
destination:
  namespace: danwiki
```

`danwiki-dev.yaml`:
```yaml
source:
  targetRevision: dev
  path: helm/danwiki
  helm:
    valueFiles:
      - values.yaml
      - values-dev.yaml
destination:
  namespace: danwiki-dev
```

`values-dev.yaml` overrides: smaller storage sizes, dev DB host (`postgres-pgvector-dev`), `DEBUG=true`, reduced resource requests.

---

## Part 2: Semantic Search Improvements

### 1. Heading Context in Chunk Embeddings

**File:** `app/services/chunking.py`

In `chunk_page()`, when finalizing `chunk_text` for each chunk, prepend the heading path if one exists:

```python
if heading_path:
    chunk_text = f"[{heading_path}]\n\n{chunk_text}"
```

This is stored in `page_embeddings.chunk_text`. No changes to the embedding service — it receives richer text and produces better-calibrated vectors.

**Migration side effect:** All existing `page_embeddings` rows are stale after this change. A new admin endpoint triggers bulk re-embedding as a background task (see below).

### 2. Admin Bulk Re-embed Endpoint

**File:** `app/routes/admin.py`

New endpoint: `POST /api/admin/reembed-all`

Enqueues an RQ task that iterates all pages, deletes their existing embeddings, sets `embeddings_status = 'pending'`, and re-queues each page for embedding. Admin-only, JWT-protected. Returns `{ "queued": N }`.

**File:** `app/tasks/embedding_tasks.py`

New task: `reembed_all_pages()` — queries all pages, calls existing embedding task per page.

### 3. Page-Level Result Grouping

**File:** `app/routes/semantic_search.py` — `semantic_search()` function

Replace the current flat chunk query with a `DISTINCT ON (p.id)` subquery that returns one row per page (the best-scoring chunk). Drop the separate count query entirely; fetch `limit + 1` rows and set `has_more: bool` in the response.

New response shape:
```json
{
  "results": [
    {
      "page_id": 42,
      "page_title": "Kubernetes Deployments",
      "page_slug": "kubernetes-deployments",
      "wiki_id": 1,
      "wiki_name": "Ops Runbook",
      "wiki_slug": "ops-runbook",
      "similarity_score": 0.61,
      "relative_score": 100.0,
      "excerpt": "Rolling updates allow...",
      "heading_path": "Deployment Strategies > Rolling Updates",
      "page_url": "/wikis/1/pages/42"
    }
  ],
  "has_more": false,
  "query": "kubernetes rolling update"
}
```

Remove `total_chunks`, `total_pages`, `unique_pages` from response (replaced by `has_more`).

### 4. Relative Score Normalization

Both `/semantic` and `/hybrid` endpoints: after collecting results, compute `max_score = max(r['similarity_score'] for r in results)`, then add `relative_score = round((r['similarity_score'] / max_score) * 100, 1)` to each result. If `max_score == 0`, set all relative scores to 0.

### 5. Reciprocal Rank Fusion for Hybrid Search

**File:** `app/routes/semantic_search.py` — `hybrid_search()` function

Replace the weighted sum merge with RRF (`k=60`):

```python
def rrf_score(rank: int, k: int = 60) -> float:
    return 1.0 / (rank + k)
```

Assign ranks independently from keyword and semantic result lists, sum RRF scores, sort descending. Remove `semantic_weight` and `keyword_weight` params from the endpoint and response. Both signals contribute equally by rank position, not by raw score magnitude.

---

## Deferred

- `nvidia/llama-nemotron-embed-vl-1b-v2` embedding model evaluation
- HyDE (Hypothetical Document Embeddings) for query expansion
- Tagging API quality review
- S3 storage backend
- GPU node provisioning
