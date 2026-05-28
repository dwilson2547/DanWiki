# Six deployment blockers resolved during DanWiki initial Kubernetes bring-up

**Date:** 2026-05-27  
**Component:** `helm/danwiki/`, `frontend/nginx.conf`, `migrations/versions/`, `cluster_config/postgres/postgres.yaml`  
**Severity:** High — collectively prevented the stack from starting; none were individually obvious until the full deployment sequence was attempted

---

## Issue 1: Stuck terminating pods block ReplicaSet from creating replacements

### Observed symptom

After deleting a ReplicaSet to force a fresh rollout, the old backend and frontend pods stayed in `Terminating` state for 29+ minutes. The new ReplicaSet showed `DESIRED=1, CURRENT=0` and never created replacement pods.

### Root cause

### NFS volume fails to unmount cleanly on pod termination

The backend pod mounts the `danwiki-uploads` NFS PVC. When the pod was deleted, the NFS client on the node failed to unmount the volume, causing the pod to hang in `Terminating`. Kubernetes does not create replacement pods until the terminating pod is fully gone (or force-deleted), so the ReplicaSet was effectively stuck with zero running replicas.

### Troubleshooting steps taken

1. **Checked pod status** — `kubectl get pods -n danwiki` showed backend and frontend stuck in `Terminating` with AGE of 29m; ReplicaSet events were empty.
2. **Checked ReplicaSet state** — `DESIRED=1, CURRENT=0` confirmed the RS controller was aware of the deletion but couldn't create a new pod while the terminating pod still existed.
3. **Identified NFS as the cause** — the backend pod has an `uploads` PVC mount; frontend has none but was also stuck (cascading from the same underlying node NFS issue).

### Fix

### Force-delete stuck pods

```bash
kubectl delete pod danwiki-backend-78c77bfc5f-z5mxq danwiki-frontend-69ddff69f8-mzgh9 \
  -n danwiki --force --grace-period=0
```

This bypasses the graceful termination wait. The ReplicaSets immediately created replacement pods.

### Files changed

- None — operational fix only

---

## Issue 2: Frontend nginx crashes on startup due to unresolvable upstream hostname

### Observed symptom

Frontend pod was in `CrashLoopBackOff`. Logs showed:

```
[emerg] 1#1: host not found in upstream "backend" in /etc/nginx/conf.d/default.conf:12
nginx: [emerg] host not found in upstream "backend" in /etc/nginx/conf.d/default.conf:12
```

### Root cause

### nginx resolves upstream hostnames at startup, not at request time

`frontend/nginx.conf` contained a `proxy_pass http://backend:5000` block for `/api/` routes. nginx resolves upstream hostnames at startup and refuses to start if any upstream can't be resolved. In Kubernetes, the backend service is named `danwiki-backend`, not `backend`, so resolution failed.

### The proxy block was dead code in Kubernetes

The Traefik IngressRoute routes `/api/*` directly to `danwiki-backend:5000` before requests ever reach the frontend nginx container. The proxy block would never have handled any traffic even if the hostname resolved.

### Troubleshooting steps taken

1. **Read pod logs** — confirmed the exact nginx startup error.
2. **Checked the IngressRoute** — `helm/danwiki/templates/ingress.yaml` confirmed Traefik routes `PathPrefix("/api")` to the backend service; nginx never sees API traffic.
3. **Concluded the block was both broken and unnecessary** — removing it is the correct fix.

### Fix

### `frontend/nginx.conf` — removed dead `/api/` proxy block

Before:
```nginx
location /api/ {
    proxy_pass http://backend:5000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}
```

After: block removed entirely. Traefik handles all `/api/*` routing.

### Files changed

- `frontend/nginx.conf` — removed `/api/` location block

---

## Issue 3: `pullPolicy: IfNotPresent` prevents nodes from picking up new `latest` images

### Observed symptom

After rebuilding and pushing a new `dwilson2547/danwiki-frontend:latest` image, `kubectl rollout restart` continued to run the old image. The nginx crash persisted even after the push completed.

### Root cause

### `IfNotPresent` skips the pull when `latest` is cached

`helm/danwiki/values.yaml` had `pullPolicy: IfNotPresent`. Once a node has any image with the `latest` tag cached, it never pulls again regardless of whether the registry has a newer digest. Using `latest` as the image tag requires `Always` pull policy; otherwise nodes are permanently stuck on the first version they pulled.

### Troubleshooting steps taken

1. **Checked files inside the running pod** — `kubectl exec ... ls /app/migrations/versions/` confirmed the pod was running an old image (missing `0001_initial_schema.py`) despite a successful push.
2. **Patched deployment to `Always`** — `kubectl patch deployment danwiki-frontend -n danwiki -p '{"spec":{"template":{"spec":{"containers":[{"name":"frontend","imagePullPolicy":"Always"}]}}}}'` caused the next rollout to pull the fresh image.

### Fix

### `helm/danwiki/values.yaml` — changed pullPolicy to Always

```yaml
image:
  pullPolicy: Always
```

### Files changed

- `helm/danwiki/values.yaml` — `image.pullPolicy: IfNotPresent` → `Always`

---

## Issue 4: pgvector extension not enabled in wiki_db

### Observed symptom

`flask db upgrade` failed with:

```
psycopg2.errors.UndefinedObject: type "vector" does not exist
LINE 9:  embedding VECTOR(384),
```

### Root cause

### Extension must be created per-database; initdb scripts only run once on first init

`CREATE EXTENSION IF NOT EXISTS vector` is included in the postgres-pgvector StatefulSet's initdb ConfigMap. However, initdb scripts only execute when the PostgreSQL data directory is first initialized — they do not re-run against existing databases. The `postgres-pgvector` StatefulSet had already been initialized (for other databases) before the `wiki_db` database existed, so the extension was never enabled in `wiki_db`.

### Troubleshooting steps taken

1. **Read the migration error** — confirmed `type "vector" does not exist` rather than a connection or permission error.
2. **Checked the StatefulSet init config** — `cluster_config/postgres/postgres.yaml` confirmed `CREATE EXTENSION` is in the initdb ConfigMap, but initdb had already run before `wiki_db` was created.

### Fix

### Manual extension creation in wiki_db

```bash
kubectl exec -n postgres -it statefulset/postgres-pgvector -- \
  psql -U postgres -c "CREATE EXTENSION IF NOT EXISTS vector;" -d wiki_db
```

For future fresh deployments, the Helm chart or a pre-migration hook should ensure the extension is enabled in the target database before migrations run.

### Files changed

- None — operational fix; future deployments need a pre-migration extension check

---

## Issue 5: Missing initial Alembic migration for core schema tables

### Observed symptom

After fixing the pgvector extension, `flask db upgrade` failed with:

```
psycopg2.errors.UndefinedTable: relation "pages" does not exist
```

The first migration (`2d34c8159fd3`, `down_revision = None`) attempted to create `page_embeddings` with a foreign key to `pages`, but `pages` didn't exist.

### Root cause

### App was originally bootstrapped with `db.create_all()`, not Alembic

The core tables (users, wikis, wiki_members, pages, page_revisions, attachments) were created directly via SQLAlchemy's `db.create_all()` on the development database. No Alembic migration was ever generated for this initial schema. All existing migrations were written against a pre-existing database and assumed the core tables were already present.

The full migration chain before the fix:

```
2d34c8159fd3 (root, down_revision=None)  ← assumed pages existed
  └── 141443313e0d  (add tags for bulk import)
        └── 7a20e2d1e99d  (Tag model + page_tags)
              └── 2c56258041a7  (add is_approved to User)
```

### Fix

### `migrations/versions/0001_initial_schema.py` — new migration root for core tables

Created a new initial migration that creates all core tables (without columns added by later migrations: no `embeddings_status`/`embeddings_updated_at` on pages, no `is_approved` on users). Also runs `CREATE EXTENSION IF NOT EXISTS vector` as a safety measure.

```python
revision = '0001_initial_schema'
down_revision = None
```

### `migrations/versions/2d34c8159fd3_add_embeddings_support.py` — wired to new root

```python
# Before
down_revision = None

# After
down_revision = '0001_initial_schema'
```

The full chain after the fix:

```
0001_initial_schema (new root)
  └── 2d34c8159fd3  (add page_embeddings + embeddings columns on pages)
        └── 141443313e0d  (add tags for bulk import)
              └── 7a20e2d1e99d  (Tag model + page_tags)
                    └── 2c56258041a7  (add is_approved to User)
```

### Files changed

- `migrations/versions/0001_initial_schema.py` — created; initial schema migration
- `migrations/versions/2d34c8159fd3_add_embeddings_support.py` — `down_revision` updated

---

## Issue 6: k8s-main pods stuck in ContainerCreating indefinitely after NFS CSI node unhealthy

### Observed symptom

Pods scheduled to `k8s-main` showed `ContainerCreating` status for 9+ minutes with `PodReadyToStartContainers: False` and no events. Pods on `k8s-worker1` and `k8s-worker2` started normally.

### Root cause

### NFS CSI node pod on k8s-main became unhealthy

The `csi-nfs-node-87zr7` pod (the NFS CSI driver daemonset instance on k8s-main) had become unresponsive. The container runtime on k8s-main could not set up pod sandboxes because the CSI driver was needed to satisfy volume mounts for pods with PVCs. Even pods without PVCs (like the frontend) were affected because the node's container runtime state was degraded.

The symptom `PodReadyToStartContainers: False` with zero events means the kubelet accepted the pod but the container runtime never progressed past sandbox creation.

This was a recurring issue on k8s-main — the user noted they had seen it before and that restarting the NFS pod resolves it.

### Troubleshooting steps taken

1. **Compared nodes** — all stuck pods were on k8s-main; all running pods were on k8s-worker1/worker2.
2. **Checked node conditions** — `kubectl describe node k8s-main` showed all conditions healthy (Ready=True, no pressure), ruling out a node-level hardware/resource issue.
3. **Checked NFS CSI pods** — `kubectl get pods -A -o wide | grep nfs | grep k8s-main` identified `csi-nfs-node-87zr7` on k8s-main.
4. **Restarted CSI pod** — `kubectl delete pod csi-nfs-node-87zr7 -n kube-system`.
5. **Cordoned k8s-main and force-rescheduled** — pods still stuck after CSI restart; cordoned k8s-main to prevent re-scheduling there, force-deleted stuck pods so they landed on healthy workers.

### Fix

### Restart NFS CSI node pod on k8s-main

```bash
kubectl delete pod csi-nfs-node-87zr7 -n kube-system
```

### Cordon, force-delete, reschedule

```bash
kubectl cordon k8s-main
kubectl delete pod danwiki-frontend-5ccfc5f999-gqpl5 \
  danwiki-embedding-service-57f989cd48-86zmc \
  -n danwiki --force --grace-period=0
kubectl uncordon k8s-main
```

If the NFS CSI pod is unhealthy on k8s-main again, the same sequence resolves it. Consider adding a liveness probe or watchdog to the CSI daemonset to auto-restart on unhealthy state.

### Files changed

- None — operational fix only
