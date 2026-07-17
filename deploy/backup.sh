#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$SCRIPT_DIR/common.sh"

[ -f "$ENV_FILE" ] || fail ".env.production was not found."
check_docker
mkdir -p "$BACKUP_DIR"

timestamp=$(date +%Y%m%d%H%M%S)
name="clinic-backup-${timestamp}.dump"

info "Creating PostgreSQL backup ${name}."
compose exec -T postgres pg_dump -U "$(load_env_value POSTGRES_USER)" -d "$(load_env_value POSTGRES_DB)" -Fc -f "/backups/${name}"
postgres_container=$(docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" ps -q postgres)
[ -n "$postgres_container" ] || fail "Postgres container was not found."
docker cp "${postgres_container}:/backups/${name}" "$BACKUP_DIR/${name}" >/dev/null

info "Backup written to $BACKUP_DIR/$name"
