#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$SCRIPT_DIR/common.sh"

[ -f "$ENV_FILE" ] || fail ".env.production was not found."
check_docker

printf 'This stops containers but keeps all Docker volumes by default.\n'
printf 'Run a backup first with ./deploy/backup.sh.\n'
printf 'Type DELETE ALL CLINIC DATA to also remove volumes, or press Enter to keep data: '
read -r confirmation

if [ "$confirmation" = "DELETE ALL CLINIC DATA" ]; then
  compose down --volumes
  info "Containers and volumes removed."
else
  compose down
  info "Containers stopped. Volumes were kept."
fi

