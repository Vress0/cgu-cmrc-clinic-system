#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$SCRIPT_DIR/common.sh"

printf 'SECRET_KEY=%s\n' "$(random_secret)"
printf 'POSTGRES_PASSWORD=%s\n' "$(random_password)"
printf 'DEFAULT_ADMIN_PASSWORD=%s\n' "$(random_password)"

