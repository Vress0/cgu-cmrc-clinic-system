#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$SCRIPT_DIR/common.sh"

[ -f "$ENV_FILE" ] || fail ".env.production was not found."
[ $# -eq 1 ] || fail "Usage: ./deploy/restore.sh <backup.dump>"
[ -f "$1" ] || fail "Backup file not found: $1"

check_docker

printf 'This will restore backup data into the production database.\n'
printf 'Type RESTORE CLINIC DATA to continue: '
read -r confirmation
[ "$confirmation" = "RESTORE CLINIC DATA" ] || fail "Restore cancelled."

info "Ensuring postgres service is running."
compose up -d postgres
wait_for_postgres 45 || fail "Postgres was not ready for restore."

info "Stopping application services before restore."
compose stop nginx frontend backend >/dev/null 2>&1 || true

info "Copying backup into postgres container."
postgres_container=$(docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" ps -q postgres)
[ -n "$postgres_container" ] || fail "Postgres container was not found."
docker cp "$1" "${postgres_container}:/tmp/restore.dump" >/dev/null

info "Restoring database."
compose exec -T postgres sh -c '
set -eu
psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '\''$POSTGRES_DB'\'' AND pid != pg_backend_pid();"
dropdb --if-exists -U "$POSTGRES_USER" "$POSTGRES_DB"
createdb -U "$POSTGRES_USER" "$POSTGRES_DB"
pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner /tmp/restore.dump
rm -f /tmp/restore.dump
'

info "Restarting application services."
compose up -d --no-build
wait_for_health 60 || fail "Health check failed after restore."
info "Restore complete."
