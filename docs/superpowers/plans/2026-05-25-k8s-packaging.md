# DanWiki K8s Packaging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Package DanWiki as four Docker images and a self-contained Helm chart following the scrape-stack/gyopart cluster pattern, plus pgvector PostgreSQL instances and ArgoCD Application manifests in the cluster_config repo.

**Architecture:** 4 Dockerfiles → 5 Deployments (backend + worker share one image; tagging API + tagging worker share another). Helm chart at `helm/danwiki/` in this repo. ArgoCD Applications in `cluster_config/argocd/`. pgvector StatefulSets appended to `cluster_config/postgres/postgres.yaml`. NFS-backed PVCs for uploads and Redis. Tagging services gated behind `tagging.enabled: false`.

**Tech Stack:** Docker, Helm 3, Traefik IngressRoute, Kubernetes 1.28+, NFS storage class, pgvector/pgvector:pg16

---

## Repo split

Tasks 1–4 and 5–14 are in the **DanWiki repo** (`/home/daniel/documents/workspace/DanWiki`).  
Tasks 15–16 are in the **cluster_config repo** (`/home/daniel/documents/workspace/cluster_config`).

## File Map — DanWiki repo

| Action | File |
|---|---|
| Create | `Dockerfile` |
| Create | `frontend/Dockerfile` |
| Create | `frontend/nginx.conf` |
| Create | `embedding_service/Dockerfile` |
| Create | `tagging_api/Dockerfile` |
| Create | `helm/danwiki/Chart.yaml` |
| Create | `helm/danwiki/values.yaml` |
| Create | `helm/danwiki/values-dev.yaml` |
| Create | `helm/danwiki/templates/_helpers.tpl` |
| Create | `helm/danwiki/templates/configmap.yaml` |
| Create | `helm/danwiki/templates/uploads-pvc.yaml` |
| Create | `helm/danwiki/templates/redis/deployment.yaml` |
| Create | `helm/danwiki/templates/redis/service.yaml` |
| Create | `helm/danwiki/templates/redis/pvc.yaml` |
| Create | `helm/danwiki/templates/backend/deployment.yaml` |
| Create | `helm/danwiki/templates/backend/service.yaml` |
| Create | `helm/danwiki/templates/worker/deployment.yaml` |
| Create | `helm/danwiki/templates/frontend/deployment.yaml` |
| Create | `helm/danwiki/templates/frontend/service.yaml` |
| Create | `helm/danwiki/templates/embedding-service/deployment.yaml` |
| Create | `helm/danwiki/templates/embedding-service/service.yaml` |
| Create | `helm/danwiki/templates/tagging/api-deployment.yaml` |
| Create | `helm/danwiki/templates/tagging/worker-deployment.yaml` |
| Create | `helm/danwiki/templates/tagging/service.yaml` |
| Create | `helm/danwiki/templates/ingress.yaml` |

## File Map — cluster_config repo

| Action | File |
|---|---|
| Modify | `postgres/postgres.yaml` (append pgvector StatefulSets) |
| Create | `postgres/init-pgvector.sql` |
| Create | `argocd/danwiki.yaml` |
| Create | `argocd/danwiki-dev.yaml` |
| Create | `example-secrets/danwiki-secrets.yml` |

---

### Task 1: Backend Dockerfile

The backend image is also used for the worker Deployment (different `command`).

**Files:**
- Create: `Dockerfile`

- [ ] **Step 1: Create `Dockerfile` at repo root**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

EXPOSE 5000

CMD ["python", "run.py"]
```

- [ ] **Step 2: Build and verify**

```bash
cd /home/daniel/documents/workspace/DanWiki
docker build -t danwiki-backend:test .
docker run --rm -e FLASK_ENV=testing -e DATABASE_URL=sqlite:///test.db \
  -e SECRET_KEY=test -e JWT_SECRET_KEY=test \
  danwiki-backend:test python -c "from app import create_app; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add Dockerfile
git commit -m "build: add backend Dockerfile"
```

---

### Task 2: Frontend Dockerfile + Nginx config

**Files:**
- Create: `frontend/Dockerfile`
- Create: `frontend/nginx.conf`

- [ ] **Step 1: Create `frontend/nginx.conf`**

```nginx
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://backend:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
}
```

Note: In K8s the Traefik IngressRoute routes `/api/*` to the backend service before Nginx sees it, so the `proxy_pass` above is active only in Docker Compose or local Docker setups.

- [ ] **Step 2: Create `frontend/Dockerfile`**

```dockerfile
FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

- [ ] **Step 3: Build and verify**

```bash
cd /home/daniel/documents/workspace/DanWiki/frontend
docker build -t danwiki-frontend:test .
docker run --rm -d -p 8080:80 --name fw-test danwiki-frontend:test
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/
docker stop fw-test
```

Expected: `200`

- [ ] **Step 4: Commit**

```bash
git add frontend/Dockerfile frontend/nginx.conf
git commit -m "build: add frontend Dockerfile with Nginx SPA config"
```

---

### Task 3: Embedding service Dockerfile

**Files:**
- Create: `embedding_service/Dockerfile`

- [ ] **Step 1: Create `embedding_service/Dockerfile`**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

ENV EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
ENV DEVICE=cpu
ENV BATCH_SIZE=32
ENV MAX_SEQ_LENGTH=256
ENV PORT=8001
ENV HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1

EXPOSE 8001

CMD ["python", "app.py"]
```

The model downloads from HuggingFace Hub on first start. Subsequent starts reuse the cached download (mount a volume at `/root/.cache/huggingface` to persist across pod restarts if needed).

- [ ] **Step 2: Build and verify**

```bash
cd /home/daniel/documents/workspace/DanWiki/embedding_service
docker build -t danwiki-embedding:test .
docker run --rm danwiki-embedding:test python -c \
  "from sentence_transformers import SentenceTransformer; print('OK')"
```

Expected: `OK` (may take 30–60s on first run while downloading model)

- [ ] **Step 3: Commit**

```bash
git add embedding_service/Dockerfile
git commit -m "build: add embedding service Dockerfile (CPU default)"
```

---

### Task 4: Tagging API Dockerfile

**Files:**
- Create: `tagging_api/Dockerfile`

- [ ] **Step 1: Create `tagging_api/Dockerfile`**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV DEVICE=cpu
ENV PYTHONUNBUFFERED=1
ENV PORT=8002
ENV HOST=0.0.0.0

EXPOSE 8002

CMD ["python", "app.py"]
```

This image is ~3–4 GB due to torch. It is only built/deployed when `tagging.enabled: true`. The `CMD` runs the FastAPI server; the tagging worker Deployment overrides this with `["python", "worker.py"]`.

- [ ] **Step 2: Build and verify**

```bash
cd /home/daniel/documents/workspace/DanWiki/tagging_api
docker build -t danwiki-tagging:test .
docker run --rm danwiki-tagging:test python -c \
  "import fastapi, torch; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add tagging_api/Dockerfile
git commit -m "build: add tagging API Dockerfile"
```

---

### Task 5: Helm chart scaffolding — Chart.yaml, values, helpers

**Files:**
- Create: `helm/danwiki/Chart.yaml`
- Create: `helm/danwiki/values.yaml`
- Create: `helm/danwiki/values-dev.yaml`
- Create: `helm/danwiki/templates/_helpers.tpl`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p /home/daniel/documents/workspace/DanWiki/helm/danwiki/templates/{backend,frontend,embedding-service,worker,redis,tagging}
```

- [ ] **Step 2: Create `helm/danwiki/Chart.yaml`**

```yaml
apiVersion: v2
name: danwiki
description: AI-powered wiki with semantic search
type: application
version: 0.1.0
appVersion: "1.0.0"
```

- [ ] **Step 3: Create `helm/danwiki/values.yaml`**

```yaml
image:
  repository: ghcr.io/dwilson2547
  tag: latest
  pullPolicy: IfNotPresent

ingress:
  host: danwiki.local

database:
  host: postgres-pgvector.postgres.svc.cluster.local
  port: 5432
  name: wiki_db
  secretName: danwiki-db-credentials   # key: DATABASE_URL

appSecrets:
  secretName: danwiki-app-secrets       # keys: SECRET_KEY, JWT_SECRET_KEY

cors:
  origins: "https://danwiki.local"

embedding:
  model: sentence-transformers/all-MiniLM-L6-v2
  device: cpu
  dimension: "384"
  serviceUrl: ""   # auto-set to http://<release>-embedding-service:8001 via configmap

uploads:
  storageClass: nfs-client
  storageSize: 20Gi

redis:
  storageClass: nfs-client
  storageSize: 1Gi

tagging:
  enabled: false
  secretName: danwiki-tagging-secrets   # key: API_TOKEN

backend:
  resources:
    requests:
      cpu: 200m
      memory: 256Mi
    limits:
      cpu: 1
      memory: 512Mi

worker:
  resources:
    requests:
      cpu: 100m
      memory: 256Mi
    limits:
      cpu: 500m
      memory: 512Mi

frontend:
  resources:
    requests:
      cpu: 50m
      memory: 64Mi
    limits:
      cpu: 200m
      memory: 128Mi

embeddingService:
  resources:
    requests:
      cpu: 200m
      memory: 512Mi
    limits:
      cpu: 1
      memory: 1Gi
```

- [ ] **Step 4: Create `helm/danwiki/values-dev.yaml`**

```yaml
ingress:
  host: danwiki-dev.local

database:
  host: postgres-pgvector-dev.postgres.svc.cluster.local
  name: wiki_db_dev

cors:
  origins: "http://danwiki-dev.local"

uploads:
  storageSize: 5Gi

redis:
  storageSize: 512Mi

backend:
  resources:
    requests:
      cpu: 100m
      memory: 128Mi
    limits:
      cpu: 500m
      memory: 256Mi

worker:
  resources:
    requests:
      cpu: 50m
      memory: 128Mi
    limits:
      cpu: 200m
      memory: 256Mi

embeddingService:
  resources:
    requests:
      cpu: 100m
      memory: 256Mi
    limits:
      cpu: 500m
      memory: 512Mi
```

- [ ] **Step 5: Create `helm/danwiki/templates/_helpers.tpl`**

```
{{/*
Expand the name of the chart.
*/}}
{{- define "danwiki.name" -}}
{{- .Chart.Name | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "danwiki.fullname" -}}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- printf "%s" $name | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "danwiki.labels" -}}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
app.kubernetes.io/name: {{ include "danwiki.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "danwiki.selectorLabels" -}}
app.kubernetes.io/name: {{ include "danwiki.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
```

- [ ] **Step 6: Lint the chart skeleton**

```bash
helm lint /home/daniel/documents/workspace/DanWiki/helm/danwiki
```

Expected: `1 chart(s) linted, 0 chart(s) failed`

- [ ] **Step 7: Commit**

```bash
git add helm/
git commit -m "build: helm chart scaffolding — Chart.yaml, values, helpers"
```

---

### Task 6: ConfigMap

**Files:**
- Create: `helm/danwiki/templates/configmap.yaml`

- [ ] **Step 1: Create `helm/danwiki/templates/configmap.yaml`**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "danwiki.fullname" . }}-config
  namespace: {{ .Release.Namespace }}
  labels:
    {{- include "danwiki.labels" . | nindent 4 }}
data:
  FLASK_ENV: "production"
  CORS_ORIGINS: {{ .Values.cors.origins | quote }}
  EMBEDDING_SERVICE_URL: "http://{{ include "danwiki.fullname" . }}-embedding-service:8001"
  EMBEDDING_MODEL: {{ .Values.embedding.model | quote }}
  EMBEDDING_DIMENSION: {{ .Values.embedding.dimension | quote }}
  REDIS_URL: "redis://{{ include "danwiki.fullname" . }}-redis:6379/0"
  DATABASE_NAME: {{ .Values.database.name | quote }}
```

- [ ] **Step 2: Lint**

```bash
helm lint /home/daniel/documents/workspace/DanWiki/helm/danwiki
```

Expected: `0 chart(s) failed`

- [ ] **Step 3: Commit**

```bash
git add helm/danwiki/templates/configmap.yaml
git commit -m "build: helm ConfigMap for non-secret env vars"
```

---

### Task 7: PVCs — uploads and Redis

**Files:**
- Create: `helm/danwiki/templates/uploads-pvc.yaml`
- Create: `helm/danwiki/templates/redis/pvc.yaml`

- [ ] **Step 1: Create `helm/danwiki/templates/uploads-pvc.yaml`**

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ include "danwiki.fullname" . }}-uploads
  namespace: {{ .Release.Namespace }}
  labels:
    {{- include "danwiki.labels" . | nindent 4 }}
spec:
  storageClassName: {{ .Values.uploads.storageClass }}
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: {{ .Values.uploads.storageSize }}
```

- [ ] **Step 2: Create `helm/danwiki/templates/redis/pvc.yaml`**

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ include "danwiki.fullname" . }}-redis-data
  namespace: {{ .Release.Namespace }}
  labels:
    {{- include "danwiki.labels" . | nindent 4 }}
spec:
  storageClassName: {{ .Values.redis.storageClass }}
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: {{ .Values.redis.storageSize }}
```

- [ ] **Step 3: Lint**

```bash
helm lint /home/daniel/documents/workspace/DanWiki/helm/danwiki
```

- [ ] **Step 4: Commit**

```bash
git add helm/danwiki/templates/uploads-pvc.yaml helm/danwiki/templates/redis/pvc.yaml
git commit -m "build: helm PVCs for uploads (RWX) and redis (RWO)"
```

---

### Task 8: Redis Deployment + Service

**Files:**
- Create: `helm/danwiki/templates/redis/deployment.yaml`
- Create: `helm/danwiki/templates/redis/service.yaml`

- [ ] **Step 1: Create `helm/danwiki/templates/redis/deployment.yaml`**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "danwiki.fullname" . }}-redis
  namespace: {{ .Release.Namespace }}
  labels:
    {{- include "danwiki.labels" . | nindent 4 }}
    app.kubernetes.io/component: redis
spec:
  replicas: 1
  selector:
    matchLabels:
      {{- include "danwiki.selectorLabels" . | nindent 6 }}
      app.kubernetes.io/component: redis
  template:
    metadata:
      labels:
        {{- include "danwiki.selectorLabels" . | nindent 8 }}
        app.kubernetes.io/component: redis
    spec:
      containers:
        - name: redis
          image: redis:7-alpine
          imagePullPolicy: IfNotPresent
          command: ["redis-server", "--appendonly", "yes"]
          ports:
            - containerPort: 6379
          readinessProbe:
            exec:
              command: ["redis-cli", "ping"]
            initialDelaySeconds: 5
            periodSeconds: 5
          livenessProbe:
            exec:
              command: ["redis-cli", "ping"]
            initialDelaySeconds: 15
            periodSeconds: 10
          volumeMounts:
            - name: data
              mountPath: /data
          resources:
            requests:
              cpu: 50m
              memory: 64Mi
            limits:
              cpu: 200m
              memory: 256Mi
      volumes:
        - name: data
          persistentVolumeClaim:
            claimName: {{ include "danwiki.fullname" . }}-redis-data
```

- [ ] **Step 2: Create `helm/danwiki/templates/redis/service.yaml`**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "danwiki.fullname" . }}-redis
  namespace: {{ .Release.Namespace }}
  labels:
    {{- include "danwiki.labels" . | nindent 4 }}
    app.kubernetes.io/component: redis
spec:
  selector:
    {{- include "danwiki.selectorLabels" . | nindent 4 }}
    app.kubernetes.io/component: redis
  ports:
    - port: 6379
      targetPort: 6379
```

- [ ] **Step 3: Lint + template render check**

```bash
helm lint /home/daniel/documents/workspace/DanWiki/helm/danwiki
helm template danwiki /home/daniel/documents/workspace/DanWiki/helm/danwiki | grep -A5 "kind: Deployment"
```

Expected: lint passes; redis Deployment appears in output

- [ ] **Step 4: Commit**

```bash
git add helm/danwiki/templates/redis/
git commit -m "build: helm Redis deployment and service"
```

---

### Task 9: Backend Deployment + Service

**Files:**
- Create: `helm/danwiki/templates/backend/deployment.yaml`
- Create: `helm/danwiki/templates/backend/service.yaml`

- [ ] **Step 1: Create `helm/danwiki/templates/backend/deployment.yaml`**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "danwiki.fullname" . }}-backend
  namespace: {{ .Release.Namespace }}
  labels:
    {{- include "danwiki.labels" . | nindent 4 }}
    app.kubernetes.io/component: backend
spec:
  replicas: 1
  selector:
    matchLabels:
      {{- include "danwiki.selectorLabels" . | nindent 6 }}
      app.kubernetes.io/component: backend
  template:
    metadata:
      labels:
        {{- include "danwiki.selectorLabels" . | nindent 8 }}
        app.kubernetes.io/component: backend
      annotations:
        checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
    spec:
      containers:
        - name: backend
          image: "{{ .Values.image.repository }}/danwiki-backend:{{ .Values.image.tag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - containerPort: 5000
          envFrom:
            - configMapRef:
                name: {{ include "danwiki.fullname" . }}-config
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: {{ .Values.database.secretName }}
                  key: DATABASE_URL
            - name: SECRET_KEY
              valueFrom:
                secretKeyRef:
                  name: {{ .Values.appSecrets.secretName }}
                  key: SECRET_KEY
            - name: JWT_SECRET_KEY
              valueFrom:
                secretKeyRef:
                  name: {{ .Values.appSecrets.secretName }}
                  key: JWT_SECRET_KEY
          readinessProbe:
            httpGet:
              path: /api/health
              port: 5000
            initialDelaySeconds: 10
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /api/health
              port: 5000
            initialDelaySeconds: 30
            periodSeconds: 15
          volumeMounts:
            - name: uploads
              mountPath: /app/uploads
          resources:
            {{- toYaml .Values.backend.resources | nindent 12 }}
      volumes:
        - name: uploads
          persistentVolumeClaim:
            claimName: {{ include "danwiki.fullname" . }}-uploads
```

- [ ] **Step 2: Create `helm/danwiki/templates/backend/service.yaml`**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "danwiki.fullname" . }}-backend
  namespace: {{ .Release.Namespace }}
  labels:
    {{- include "danwiki.labels" . | nindent 4 }}
    app.kubernetes.io/component: backend
spec:
  selector:
    {{- include "danwiki.selectorLabels" . | nindent 4 }}
    app.kubernetes.io/component: backend
  ports:
    - port: 5000
      targetPort: 5000
```

- [ ] **Step 3: Lint**

```bash
helm lint /home/daniel/documents/workspace/DanWiki/helm/danwiki
```

- [ ] **Step 4: Commit**

```bash
git add helm/danwiki/templates/backend/
git commit -m "build: helm backend deployment and service"
```

---

### Task 10: Worker Deployment

Reuses the backend image with a different `command`.

**Files:**
- Create: `helm/danwiki/templates/worker/deployment.yaml`

- [ ] **Step 1: Create `helm/danwiki/templates/worker/deployment.yaml`**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "danwiki.fullname" . }}-worker
  namespace: {{ .Release.Namespace }}
  labels:
    {{- include "danwiki.labels" . | nindent 4 }}
    app.kubernetes.io/component: worker
spec:
  replicas: 1
  selector:
    matchLabels:
      {{- include "danwiki.selectorLabels" . | nindent 6 }}
      app.kubernetes.io/component: worker
  template:
    metadata:
      labels:
        {{- include "danwiki.selectorLabels" . | nindent 8 }}
        app.kubernetes.io/component: worker
      annotations:
        checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
    spec:
      containers:
        - name: worker
          image: "{{ .Values.image.repository }}/danwiki-backend:{{ .Values.image.tag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          command: ["python", "worker/worker.py"]
          envFrom:
            - configMapRef:
                name: {{ include "danwiki.fullname" . }}-config
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: {{ .Values.database.secretName }}
                  key: DATABASE_URL
            - name: SECRET_KEY
              valueFrom:
                secretKeyRef:
                  name: {{ .Values.appSecrets.secretName }}
                  key: SECRET_KEY
            - name: JWT_SECRET_KEY
              valueFrom:
                secretKeyRef:
                  name: {{ .Values.appSecrets.secretName }}
                  key: JWT_SECRET_KEY
          volumeMounts:
            - name: uploads
              mountPath: /app/uploads
          resources:
            {{- toYaml .Values.worker.resources | nindent 12 }}
      volumes:
        - name: uploads
          persistentVolumeClaim:
            claimName: {{ include "danwiki.fullname" . }}-uploads
```

- [ ] **Step 2: Lint + commit**

```bash
helm lint /home/daniel/documents/workspace/DanWiki/helm/danwiki
git add helm/danwiki/templates/worker/
git commit -m "build: helm worker deployment (reuses backend image)"
```

---

### Task 11: Frontend Deployment + Service

**Files:**
- Create: `helm/danwiki/templates/frontend/deployment.yaml`
- Create: `helm/danwiki/templates/frontend/service.yaml`

- [ ] **Step 1: Create `helm/danwiki/templates/frontend/deployment.yaml`**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "danwiki.fullname" . }}-frontend
  namespace: {{ .Release.Namespace }}
  labels:
    {{- include "danwiki.labels" . | nindent 4 }}
    app.kubernetes.io/component: frontend
spec:
  replicas: 1
  selector:
    matchLabels:
      {{- include "danwiki.selectorLabels" . | nindent 6 }}
      app.kubernetes.io/component: frontend
  template:
    metadata:
      labels:
        {{- include "danwiki.selectorLabels" . | nindent 8 }}
        app.kubernetes.io/component: frontend
    spec:
      containers:
        - name: frontend
          image: "{{ .Values.image.repository }}/danwiki-frontend:{{ .Values.image.tag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - containerPort: 80
          readinessProbe:
            httpGet:
              path: /
              port: 80
            initialDelaySeconds: 5
            periodSeconds: 10
          resources:
            {{- toYaml .Values.frontend.resources | nindent 12 }}
```

- [ ] **Step 2: Create `helm/danwiki/templates/frontend/service.yaml`**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "danwiki.fullname" . }}-frontend
  namespace: {{ .Release.Namespace }}
  labels:
    {{- include "danwiki.labels" . | nindent 4 }}
    app.kubernetes.io/component: frontend
spec:
  selector:
    {{- include "danwiki.selectorLabels" . | nindent 4 }}
    app.kubernetes.io/component: frontend
  ports:
    - port: 80
      targetPort: 80
```

- [ ] **Step 3: Lint + commit**

```bash
helm lint /home/daniel/documents/workspace/DanWiki/helm/danwiki
git add helm/danwiki/templates/frontend/
git commit -m "build: helm frontend deployment and service"
```

---

### Task 12: Embedding Service Deployment + Service

**Files:**
- Create: `helm/danwiki/templates/embedding-service/deployment.yaml`
- Create: `helm/danwiki/templates/embedding-service/service.yaml`

- [ ] **Step 1: Create `helm/danwiki/templates/embedding-service/deployment.yaml`**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "danwiki.fullname" . }}-embedding-service
  namespace: {{ .Release.Namespace }}
  labels:
    {{- include "danwiki.labels" . | nindent 4 }}
    app.kubernetes.io/component: embedding-service
spec:
  replicas: 1
  selector:
    matchLabels:
      {{- include "danwiki.selectorLabels" . | nindent 6 }}
      app.kubernetes.io/component: embedding-service
  template:
    metadata:
      labels:
        {{- include "danwiki.selectorLabels" . | nindent 8 }}
        app.kubernetes.io/component: embedding-service
    spec:
      containers:
        - name: embedding-service
          image: "{{ .Values.image.repository }}/danwiki-embedding:{{ .Values.image.tag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - containerPort: 8001
          env:
            - name: DEVICE
              value: {{ .Values.embedding.device | quote }}
            - name: EMBEDDING_MODEL
              value: {{ .Values.embedding.model | quote }}
          readinessProbe:
            httpGet:
              path: /health
              port: 8001
            initialDelaySeconds: 30
            periodSeconds: 10
            failureThreshold: 6
          livenessProbe:
            httpGet:
              path: /health
              port: 8001
            initialDelaySeconds: 60
            periodSeconds: 15
          resources:
            {{- toYaml .Values.embeddingService.resources | nindent 12 }}
```

- [ ] **Step 2: Create `helm/danwiki/templates/embedding-service/service.yaml`**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "danwiki.fullname" . }}-embedding-service
  namespace: {{ .Release.Namespace }}
  labels:
    {{- include "danwiki.labels" . | nindent 4 }}
    app.kubernetes.io/component: embedding-service
spec:
  selector:
    {{- include "danwiki.selectorLabels" . | nindent 4 }}
    app.kubernetes.io/component: embedding-service
  ports:
    - port: 8001
      targetPort: 8001
```

- [ ] **Step 3: Lint + commit**

```bash
helm lint /home/daniel/documents/workspace/DanWiki/helm/danwiki
git add helm/danwiki/templates/embedding-service/
git commit -m "build: helm embedding service deployment and service"
```

---

### Task 13: Tagging API + Worker (conditional)

Both gated behind `{{ if .Values.tagging.enabled }}`.

**Files:**
- Create: `helm/danwiki/templates/tagging/api-deployment.yaml`
- Create: `helm/danwiki/templates/tagging/worker-deployment.yaml`
- Create: `helm/danwiki/templates/tagging/service.yaml`

- [ ] **Step 1: Create `helm/danwiki/templates/tagging/api-deployment.yaml`**

```yaml
{{- if .Values.tagging.enabled }}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "danwiki.fullname" . }}-tagging-api
  namespace: {{ .Release.Namespace }}
  labels:
    {{- include "danwiki.labels" . | nindent 4 }}
    app.kubernetes.io/component: tagging-api
spec:
  replicas: 1
  selector:
    matchLabels:
      {{- include "danwiki.selectorLabels" . | nindent 6 }}
      app.kubernetes.io/component: tagging-api
  template:
    metadata:
      labels:
        {{- include "danwiki.selectorLabels" . | nindent 8 }}
        app.kubernetes.io/component: tagging-api
    spec:
      containers:
        - name: tagging-api
          image: "{{ .Values.image.repository }}/danwiki-tagging:{{ .Values.image.tag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - containerPort: 8002
          env:
            - name: REDIS_URL
              value: "redis://{{ include "danwiki.fullname" . }}-redis:6379/0"
            - name: API_TOKEN
              valueFrom:
                secretKeyRef:
                  name: {{ .Values.tagging.secretName }}
                  key: API_TOKEN
          readinessProbe:
            httpGet:
              path: /health
              port: 8002
            initialDelaySeconds: 60
            periodSeconds: 15
            failureThreshold: 10
          resources:
            requests:
              cpu: 500m
              memory: 4Gi
            limits:
              cpu: 2
              memory: 8Gi
{{- end }}
```

- [ ] **Step 2: Create `helm/danwiki/templates/tagging/worker-deployment.yaml`**

```yaml
{{- if .Values.tagging.enabled }}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "danwiki.fullname" . }}-tagging-worker
  namespace: {{ .Release.Namespace }}
  labels:
    {{- include "danwiki.labels" . | nindent 4 }}
    app.kubernetes.io/component: tagging-worker
spec:
  replicas: 1
  selector:
    matchLabels:
      {{- include "danwiki.selectorLabels" . | nindent 6 }}
      app.kubernetes.io/component: tagging-worker
  template:
    metadata:
      labels:
        {{- include "danwiki.selectorLabels" . | nindent 8 }}
        app.kubernetes.io/component: tagging-worker
    spec:
      containers:
        - name: tagging-worker
          image: "{{ .Values.image.repository }}/danwiki-tagging:{{ .Values.image.tag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          command: ["python", "worker.py"]
          env:
            - name: REDIS_URL
              value: "redis://{{ include "danwiki.fullname" . }}-redis:6379/0"
            - name: API_TOKEN
              valueFrom:
                secretKeyRef:
                  name: {{ .Values.tagging.secretName }}
                  key: API_TOKEN
          resources:
            requests:
              cpu: 500m
              memory: 4Gi
            limits:
              cpu: 2
              memory: 8Gi
{{- end }}
```

- [ ] **Step 3: Create `helm/danwiki/templates/tagging/service.yaml`**

```yaml
{{- if .Values.tagging.enabled }}
apiVersion: v1
kind: Service
metadata:
  name: {{ include "danwiki.fullname" . }}-tagging-api
  namespace: {{ .Release.Namespace }}
  labels:
    {{- include "danwiki.labels" . | nindent 4 }}
    app.kubernetes.io/component: tagging-api
spec:
  selector:
    {{- include "danwiki.selectorLabels" . | nindent 4 }}
    app.kubernetes.io/component: tagging-api
  ports:
    - port: 8002
      targetPort: 8002
{{- end }}
```

- [ ] **Step 4: Verify tagging resources do NOT render with default values**

```bash
helm template danwiki /home/daniel/documents/workspace/DanWiki/helm/danwiki | grep -c "tagging"
```

Expected: `0`

- [ ] **Step 5: Verify tagging resources DO render when enabled**

```bash
helm template danwiki /home/daniel/documents/workspace/DanWiki/helm/danwiki \
  --set tagging.enabled=true | grep "component: tagging" | wc -l
```

Expected: `3` or more (api-deployment, worker-deployment, service each contain the label)

- [ ] **Step 6: Lint + commit**

```bash
helm lint /home/daniel/documents/workspace/DanWiki/helm/danwiki
git add helm/danwiki/templates/tagging/
git commit -m "build: helm tagging API and worker (conditional on tagging.enabled)"
```

---

### Task 14: Ingress (Traefik IngressRoute)

**Files:**
- Create: `helm/danwiki/templates/ingress.yaml`

- [ ] **Step 1: Create `helm/danwiki/templates/ingress.yaml`**

```yaml
apiVersion: traefik.io/v1alpha1
kind: IngressRoute
metadata:
  name: {{ include "danwiki.fullname" . }}
  namespace: {{ .Release.Namespace }}
  labels:
    {{- include "danwiki.labels" . | nindent 4 }}
spec:
  entryPoints:
    - web
  routes:
    - match: Host(`{{ .Values.ingress.host }}`) && PathPrefix(`/api`)
      kind: Rule
      services:
        - name: {{ include "danwiki.fullname" . }}-backend
          port: 5000
    - match: Host(`{{ .Values.ingress.host }}`)
      kind: Rule
      services:
        - name: {{ include "danwiki.fullname" . }}-frontend
          port: 80
```

- [ ] **Step 2: Final lint + template render**

```bash
helm lint /home/daniel/documents/workspace/DanWiki/helm/danwiki
helm template danwiki /home/daniel/documents/workspace/DanWiki/helm/danwiki | grep -E "kind:|Host\("
```

Expected output includes:
```
kind: ConfigMap
kind: PersistentVolumeClaim
kind: PersistentVolumeClaim
kind: Deployment       # redis
kind: Service          # redis
kind: Deployment       # backend
kind: Service          # backend
kind: Deployment       # worker
kind: Deployment       # frontend
kind: Service          # frontend
kind: Deployment       # embedding-service
kind: Service          # embedding-service
kind: IngressRoute
Host(`danwiki.local`)
```

- [ ] **Step 3: Commit**

```bash
git add helm/danwiki/templates/ingress.yaml
git commit -m "build: helm Traefik IngressRoute for danwiki.local"
```

---

### Task 15: pgvector StatefulSets in cluster_config

Work in `/home/daniel/documents/workspace/cluster_config`.

**Files:**
- Create: `postgres/init-pgvector.sql`
- Modify: `postgres/postgres.yaml` (append pgvector StatefulSets + Services + ConfigMap)

- [ ] **Step 1: Create `postgres/init-pgvector.sql`**

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

- [ ] **Step 2: Append to `postgres/postgres.yaml`**

Add the following at the end of the file (after the existing `postgres-dev` Service):

```yaml
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: pgvector-init
  namespace: postgres
data:
  init.sql: |
    CREATE EXTENSION IF NOT EXISTS vector;
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres-pgvector
  namespace: postgres
  labels:
    app: postgres-pgvector
spec:
  serviceName: postgres-pgvector
  replicas: 1
  selector:
    matchLabels:
      app: postgres-pgvector
  template:
    metadata:
      labels:
        app: postgres-pgvector
    spec:
      securityContext:
        runAsUser: 999
        runAsGroup: 999
        fsGroup: 999
      containers:
        - name: postgres
          image: pgvector/pgvector:pg16
          imagePullPolicy: IfNotPresent
          env:
            - name: PGDATA
              value: /var/lib/postgresql/data/pgdata
            - name: POSTGRES_USER
              valueFrom:
                secretKeyRef:
                  name: postgres-pgvector-credentials
                  key: POSTGRES_USER
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-pgvector-credentials
                  key: POSTGRES_PASSWORD
          ports:
            - containerPort: 5432
          readinessProbe:
            exec:
              command: ["pg_isready", "-U", "postgres"]
            initialDelaySeconds: 5
            periodSeconds: 5
            failureThreshold: 10
          livenessProbe:
            exec:
              command: ["pg_isready", "-U", "postgres"]
            initialDelaySeconds: 15
            periodSeconds: 10
            failureThreshold: 6
          resources:
            requests:
              cpu: 1
              memory: 1Gi
            limits:
              cpu: 2
              memory: 2Gi
          volumeMounts:
            - name: data
              mountPath: /var/lib/postgresql/data
            - name: init-sql
              mountPath: /docker-entrypoint-initdb.d
      volumes:
        - name: init-sql
          configMap:
            name: pgvector-init
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        storageClassName: nfs-dataset
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 150Gi
---
apiVersion: v1
kind: Service
metadata:
  name: postgres-pgvector
  namespace: postgres
  labels:
    app: postgres-pgvector
spec:
  selector:
    app: postgres-pgvector
  ports:
    - port: 5432
      targetPort: 5432
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres-pgvector-dev
  namespace: postgres
  labels:
    app: postgres-pgvector-dev
spec:
  serviceName: postgres-pgvector-dev
  replicas: 1
  selector:
    matchLabels:
      app: postgres-pgvector-dev
  template:
    metadata:
      labels:
        app: postgres-pgvector-dev
    spec:
      securityContext:
        runAsUser: 999
        runAsGroup: 999
        fsGroup: 999
      containers:
        - name: postgres
          image: pgvector/pgvector:pg16
          imagePullPolicy: IfNotPresent
          env:
            - name: PGDATA
              value: /var/lib/postgresql/data/pgdata
            - name: POSTGRES_USER
              valueFrom:
                secretKeyRef:
                  name: postgres-pgvector-dev-credentials
                  key: POSTGRES_USER
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-pgvector-dev-credentials
                  key: POSTGRES_PASSWORD
          ports:
            - containerPort: 5432
          readinessProbe:
            exec:
              command: ["pg_isready", "-U", "postgres"]
            initialDelaySeconds: 5
            periodSeconds: 5
            failureThreshold: 10
          livenessProbe:
            exec:
              command: ["pg_isready", "-U", "postgres"]
            initialDelaySeconds: 15
            periodSeconds: 10
            failureThreshold: 6
          resources:
            requests:
              cpu: 1
              memory: 1Gi
            limits:
              cpu: 2
              memory: 2Gi
          volumeMounts:
            - name: data
              mountPath: /var/lib/postgresql/data
            - name: init-sql
              mountPath: /docker-entrypoint-initdb.d
      volumes:
        - name: init-sql
          configMap:
            name: pgvector-init
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        storageClassName: nfs-dataset
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 50Gi
---
apiVersion: v1
kind: Service
metadata:
  name: postgres-pgvector-dev
  namespace: postgres
  labels:
    app: postgres-pgvector-dev
spec:
  selector:
    app: postgres-pgvector-dev
  ports:
    - port: 5432
      targetPort: 5432
```

- [ ] **Step 3: Create secrets manually (before applying ArgoCD app)**

```bash
# In cluster_config repo — create example-secrets/danwiki-secrets.yml
# (real values applied manually, this file is the template)
```

Create `example-secrets/danwiki-secrets.yml`:

```yaml
# Copy to a local file, fill in real values, then:
#   kubectl create namespace danwiki
#   kubectl apply -f <your-filled-file>
# Do NOT commit the filled version.

apiVersion: v1
kind: Secret
metadata:
  name: danwiki-db-credentials
  namespace: danwiki
type: Opaque
stringData:
  DATABASE_URL: "postgresql://WIKI_USER:WIKI_PASSWORD@postgres-pgvector.postgres.svc.cluster.local:5432/wiki_db"
---
apiVersion: v1
kind: Secret
metadata:
  name: danwiki-app-secrets
  namespace: danwiki
type: Opaque
stringData:
  SECRET_KEY: "CHANGE_ME_strong_random_secret"
  JWT_SECRET_KEY: "CHANGE_ME_strong_random_jwt_secret"
---
# pgvector postgres credentials (applied in postgres namespace)
apiVersion: v1
kind: Secret
metadata:
  name: postgres-pgvector-credentials
  namespace: postgres
type: Opaque
stringData:
  POSTGRES_USER: "postgres"
  POSTGRES_PASSWORD: "CHANGE_ME_strong_password"
---
apiVersion: v1
kind: Secret
metadata:
  name: postgres-pgvector-dev-credentials
  namespace: postgres
type: Opaque
stringData:
  POSTGRES_USER: "postgres"
  POSTGRES_PASSWORD: "CHANGE_ME_dev_password"
```

- [ ] **Step 4: Commit cluster_config changes**

```bash
cd /home/daniel/documents/workspace/cluster_config
git add postgres/postgres.yaml postgres/init-pgvector.sql example-secrets/danwiki-secrets.yml
git commit -m "feat: add pgvector postgres StatefulSets (prod 150Gi, dev 50Gi)"
```

---

### Task 16: ArgoCD manifests in cluster_config

**Files:**
- Create: `argocd/danwiki.yaml`
- Create: `argocd/danwiki-dev.yaml`

- [ ] **Step 1: Create `argocd/danwiki.yaml`**

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: danwiki
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/dwilson2547/DanWiki.git
    targetRevision: main
    path: helm/danwiki
  destination:
    server: https://kubernetes.default.svc
    namespace: danwiki
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

- [ ] **Step 2: Create `argocd/danwiki-dev.yaml`**

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: danwiki-dev
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/dwilson2547/DanWiki.git
    targetRevision: dev
    path: helm/danwiki
    helm:
      valueFiles:
        - values.yaml
        - values-dev.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: danwiki-dev
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

- [ ] **Step 3: Commit**

```bash
cd /home/daniel/documents/workspace/cluster_config
git add argocd/danwiki.yaml argocd/danwiki-dev.yaml
git commit -m "feat: ArgoCD Application manifests for danwiki prod and dev"
```

- [ ] **Step 4: Create wiki_db and run migrations after pgvector is ready**

Once the `postgres-pgvector` StatefulSet is running and secrets are applied:

```bash
# Exec into the backend pod (or run locally pointing at the cluster DB)
kubectl exec -it -n danwiki deploy/danwiki-backend -- \
  flask --app run db upgrade
```

The init SQL only creates the `vector` extension. The `wiki_db` database and schema are created by the Flask migration (Alembic). If the database doesn't exist yet, create it first:

```bash
kubectl exec -it -n postgres statefulset/postgres-pgvector -- \
  psql -U postgres -c "CREATE DATABASE wiki_db;"
```

Then run migrations. The HNSW index on `page_embeddings.embedding` is created via migration — verify it exists after upgrade:

```bash
kubectl exec -it -n postgres statefulset/postgres-pgvector -- \
  psql -U postgres -d wiki_db -c "\d page_embeddings"
```

- [ ] **Step 5: Apply secrets manually, then apply ArgoCD apps**

```bash
# Apply secrets first (both namespaces)
kubectl apply -f <your-filled-danwiki-secrets.yml>

# Apply ArgoCD apps — ArgoCD retries if secrets aren't ready yet
kubectl apply -f argocd/danwiki.yaml
# dev when ready:
# kubectl apply -f argocd/danwiki-dev.yaml
```

After applying, ArgoCD syncs automatically on every push to `main` in the DanWiki repo.
