# Deployment Guide

## Local Ports

Development compose exposes:

| Service | URL |
| --- | --- |
| Frontend | `http://localhost:3000` |
| Nginx | `http://localhost:8080` |
| Backend direct health | `http://localhost:8081/api/v1/health` |
| PostgreSQL | `localhost:5432` |

For normal local use, enter through Nginx: `http://localhost:8080`.

## Production Compose

Use `docker-compose.production.yml` as the production-oriented baseline. It does not expose PostgreSQL or backend debug ports to the host. Nginx is the public entrypoint.

Required environment variables:

```text
POSTGRES_DB
POSTGRES_USER
POSTGRES_PASSWORD
DATABASE_URL
BACKEND_CORS_ORIGINS
SECRET_KEY
DEFAULT_ADMIN_USERNAME
DEFAULT_ADMIN_EMAIL
DEFAULT_ADMIN_PASSWORD
NEXT_PUBLIC_API_BASE_URL
```

Recommended optional variables:

```text
DATABASE_CONNECT_TIMEOUT_SECONDS=5
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=14
DEFAULT_ADMIN_FULL_NAME=System Administrator
```

Start production-style services:

```powershell
docker compose -f docker-compose.production.yml up --build -d
docker compose -f docker-compose.production.yml ps
```

## Public Ports

For production, expose only:

- `80` for HTTP
- `443` for HTTPS after TLS is configured

Do not expose these ports publicly:

- PostgreSQL `5432`
- Backend `8000`
- Frontend `3000`

## TLS And HSTS

The current Nginx config includes security headers suitable for HTTP local and reverse-proxy deployments. Add `Strict-Transport-Security` only after HTTPS is enabled and verified end to end.

## Release Candidate Flow

After the Phase 4 PR is merged:

```powershell
git switch main
git pull --ff-only
git switch -c release/mvp-rc1
```

Only accept bug fixes, documentation corrections, deployment hardening, and test fixes on the RC branch.
