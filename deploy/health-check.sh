#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$SCRIPT_DIR/common.sh"

[ -f "$ENV_FILE" ] || fail ".env.production was not found. Run ./install.sh first."
check_docker

status=0
check() {
  label="$1"
  shift
  if "$@" >/dev/null 2>&1; then
    printf '%s: ok\n' "$label"
  else
    printf '%s: failed\n' "$label" >&2
    status=1
  fi
}

check "Docker daemon" docker info
check "Compose config" compose config --quiet
check "PostgreSQL" compose exec -T postgres pg_isready -U "$(load_env_value POSTGRES_USER)" -d "$(load_env_value POSTGRES_DB)"
check "Backend container" compose exec -T backend python -c "import json, urllib.request; data=json.load(urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health', timeout=5)); raise SystemExit(0 if data.get('status') == 'ok' and data.get('database') == 'ok' else 1)"
check "Nginx health endpoint" wait_for_health 3
check "Alembic current" compose exec -T backend alembic current

printf 'Disk usage:\n'
df -h "$ROOT_DIR" || true

printf 'Recent backups:\n'
mkdir -p "$BACKUP_DIR"
ls -1 "$BACKUP_DIR" 2>/dev/null | tail -5 || true

exit "$status"

