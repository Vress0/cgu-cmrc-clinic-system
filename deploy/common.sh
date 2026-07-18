#!/usr/bin/env sh

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
DEPLOY_DIR="$ROOT_DIR/deploy"
ENV_FILE="$ROOT_DIR/.env.production"
COMPOSE_FILE="$DEPLOY_DIR/docker-compose.production.yml"
BACKUP_DIR="$ROOT_DIR/backups"

compose() {
  docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@"
}

info() {
  printf '[INFO] %s\n' "$*"
}

warn() {
  printf '[WARN] %s\n' "$*" >&2
}

fail() {
  printf '[ERROR] %s\n' "$*" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || fail "$1 is required but was not found."
}

random_secret() {
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -base64 48 | tr -d '\n'
    return
  fi
  if command -v python3 >/dev/null 2>&1; then
    python3 -c 'import secrets; print(secrets.token_urlsafe(48))'
    return
  fi
  if command -v python >/dev/null 2>&1; then
    python -c 'import secrets; print(secrets.token_urlsafe(48))'
    return
  fi
  fail "openssl or python is required to generate secrets."
}

random_password() {
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -base64 24 | tr -dc 'A-Za-z0-9' | head -c 24
    printf '\n'
    return
  fi
  if command -v python3 >/dev/null 2>&1; then
    python3 -c 'import secrets,string; alphabet=string.ascii_letters+string.digits; print("".join(secrets.choice(alphabet) for _ in range(24)))'
    return
  fi
  if command -v python >/dev/null 2>&1; then
    python -c 'import secrets,string; alphabet=string.ascii_letters+string.digits; print("".join(secrets.choice(alphabet) for _ in range(24)))'
    return
  fi
  fail "openssl or python is required to generate passwords."
}

load_env_value() {
  key="$1"
  if [ ! -f "$ENV_FILE" ]; then
    return 1
  fi
  grep -E "^${key}=" "$ENV_FILE" | tail -n 1 | sed "s/^${key}=//"
}

health_url() {
  public_base=$(load_env_value PUBLIC_BASE_URL || printf 'http://localhost')
  printf '%s/api/v1/health' "$public_base"
}

check_docker() {
  require_command docker
  docker compose version >/dev/null 2>&1 || fail "docker compose is required."
  docker info >/dev/null 2>&1 || fail "Docker daemon is not running. Start Docker Desktop or the Docker service and retry."
}

check_port_available() {
  port="$1"
  if command -v lsof >/dev/null 2>&1; then
    if lsof -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
      fail "Port $port is already in use."
    fi
  elif command -v netstat >/dev/null 2>&1; then
    if netstat -an | grep -E "[.:]${port}[[:space:]].*LISTEN" >/dev/null 2>&1; then
      fail "Port $port is already in use."
    fi
  else
    warn "Cannot check port $port because neither lsof nor netstat is available."
  fi
}

write_env_file() {
  compose_project_name="${COMPOSE_PROJECT_NAME:-cgu_cmrc_clinic}"
  public_base="${PUBLIC_BASE_URL:-http://localhost}"
  http_port="${HTTP_PORT:-80}"
  postgres_db="${POSTGRES_DB:-clinic_system}"
  postgres_user="${POSTGRES_USER:-clinic_system}"
  postgres_password="${POSTGRES_PASSWORD:-$(random_password)}"
  secret_key="${SECRET_KEY:-$(random_secret)}"
  admin_username="${DEFAULT_ADMIN_USERNAME:-admin}"
  admin_email="${DEFAULT_ADMIN_EMAIL:-admin@example.com}"
  admin_full_name="${DEFAULT_ADMIN_FULL_NAME:-System Administrator}"
  admin_password="${DEFAULT_ADMIN_PASSWORD:-$(random_password)}"
  database_url="postgresql+psycopg://${postgres_user}:${postgres_password}@postgres:5432/${postgres_db}"

  cat > "$ENV_FILE" <<EOF
COMPOSE_PROJECT_NAME=${compose_project_name}
POSTGRES_VOLUME_NAME=${POSTGRES_VOLUME_NAME:-clinic_postgres_data}
UPLOADS_VOLUME_NAME=${UPLOADS_VOLUME_NAME:-clinic_uploads}
BACKUPS_VOLUME_NAME=${BACKUPS_VOLUME_NAME:-clinic_backups}
APP_ENV=production
APP_NAME=CGU CMRC Clinic System
PUBLIC_BASE_URL=${public_base}

POSTGRES_DB=${postgres_db}
POSTGRES_USER=${postgres_user}
POSTGRES_PASSWORD=${postgres_password}

DATABASE_URL=${database_url}
DATABASE_CONNECT_TIMEOUT_SECONDS=5

SECRET_KEY=${secret_key}
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=14

DEFAULT_ADMIN_USERNAME=${admin_username}
DEFAULT_ADMIN_EMAIL=${admin_email}
DEFAULT_ADMIN_FULL_NAME=${admin_full_name}
DEFAULT_ADMIN_PASSWORD=${admin_password}
ENABLE_DEMO_MODE=${ENABLE_DEMO_MODE:-true}
DEFAULT_DATA_MODE=${DEFAULT_DATA_MODE:-LIVE}
ALLOW_DEMO_RESET=${ALLOW_DEMO_RESET:-true}

BACKEND_CORS_ORIGINS=${public_base}
NEXT_PUBLIC_API_BASE_URL=${public_base}/api/v1
INTERNAL_API_BASE_URL=http://backend:8000/api/v1

HTTP_PORT=${http_port}
HTTPS_PORT=443
EOF

  chmod 600 "$ENV_FILE" 2>/dev/null || true
  printf '%s\n' "$admin_password"
}

wait_for_health() {
  url=$(health_url)
  max_attempts="${1:-60}"
  attempt=1
  while [ "$attempt" -le "$max_attempts" ]; do
    if command -v curl >/dev/null 2>&1; then
      if curl -fsS "$url" >/dev/null 2>&1; then
        return 0
      fi
    elif command -v python3 >/dev/null 2>&1; then
      if python3 - "$url" <<'PY' >/dev/null 2>&1
import sys, urllib.request
urllib.request.urlopen(sys.argv[1], timeout=5).read()
PY
      then
        return 0
      fi
    else
      compose exec -T backend python -c "import json, urllib.request; data=json.load(urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health', timeout=5)); raise SystemExit(0 if data.get('status') == 'ok' and data.get('database') == 'ok' else 1)" >/dev/null 2>&1 && return 0
    fi
    attempt=$((attempt + 1))
    sleep 3
  done
  return 1
}

wait_for_postgres() {
  max_attempts="${1:-30}"
  attempt=1
  while [ "$attempt" -le "$max_attempts" ]; do
    if compose exec -T postgres pg_isready -U "$(load_env_value POSTGRES_USER)" -d "$(load_env_value POSTGRES_DB)" >/dev/null 2>&1; then
      return 0
    fi
    attempt=$((attempt + 1))
    sleep 2
  done
  return 1
}
