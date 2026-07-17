#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$SCRIPT_DIR/common.sh"

trap 'fail "Install failed. Check Docker logs with: docker compose --env-file .env.production -f deploy/docker-compose.production.yml logs --tail=200"' ERR

info "Starting one-click production install."
check_docker

if [ -f "$ENV_FILE" ]; then
  info ".env.production already exists; reusing it."
  admin_password=""
else
  http_port="${HTTP_PORT:-80}"
  check_port_available "$http_port"
  info "Creating .env.production with generated secrets."
  admin_password=$(write_env_file)
fi

mkdir -p "$BACKUP_DIR"

info "Validating production compose file."
compose config --quiet

info "Building and starting services."
compose up --build -d

info "Waiting for health endpoint."
wait_for_health 80 || fail "Health check failed after startup."

info "Current migration:"
compose exec -T backend alembic current

cat <<EOF
========================================
Clinic system deployment complete
========================================

Application URL: $(load_env_value PUBLIC_BASE_URL)
Admin username: $(load_env_value DEFAULT_ADMIN_USERNAME)
EOF

if [ -n "${admin_password:-}" ]; then
  cat <<EOF
Generated admin password: ${admin_password}

This password is shown once. Store it securely, then change it after first login.
EOF
else
  cat <<EOF
Admin password: existing .env.production value was reused.
EOF
fi

cat <<EOF

Next steps:
1. Log in and create named administrator accounts.
2. Configure HTTPS before production use.
3. Run ./deploy/backup.sh and store the backup securely.
4. Run ./deploy/health-check.sh after any update.
EOF
