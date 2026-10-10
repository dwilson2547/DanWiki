# OIDC cutover findings (2026-10-10)

Found while moving DanWiki to authentik sign-in and danwiki.danwils.com.

## 1. Backend could not reach auth.danwils.com
- **Symptom:** `GET /api/auth/oidc/login` → 500; `requests.ConnectionError ... [Errno 101] Network is unreachable` fetching `/.well-known/openid-configuration`.
- **Cause:** inside the pod, `auth.danwils.com` resolved only to Cloudflare IPv6 addresses (verified with `getaddrinfo`), and pods have no IPv6 route.
- **Fix:** `oidc.hostAliases` in `helm/danwiki/values.yaml` pins the host to traefik-public (192.168.0.65). TLS is still valid, and there is no Cloudflare hop. Photo-dump uses the same fix (`helm/photo-dump/values-prod.yaml`).
- **Applies to:** any in-cluster OIDC client that uses the public authentik URL.

## 2. `SQLAlchemy<2.1` pin
SQLAlchemy 2.1 maps `postgresql://` to psycopg 3. The image installs psycopg2, so a rebuild without the pin cannot connect. Prod ran 2.0.50.

## 3. Placeholder `SECRET_KEY` in prod
The `danwiki-app-secrets` `SECRET_KEY` was still `CHANGE_ME`. It became load-bearing once it started signing the OIDC state cookie, so it was rotated. `JWT_SECRET_KEY` was already real and was not changed.

## 4. Flask debug server in production
The image ran `python run.py`, which is Werkzeug's debug server. It now runs gunicorn (`Dockerfile`).

## 5. Migrations are manual
Run `kubectl -n danwiki exec deploy/danwiki-backend -- flask --app run db upgrade` after any deploy that adds a migration. `3b7e1f0a9c21` was applied this way.
