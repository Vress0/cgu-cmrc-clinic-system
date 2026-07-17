#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$SCRIPT_DIR/common.sh"

trap 'fail "Update failed. Existing Docker volumes were not removed. Inspect logs and rerun after fixing the issue."' ERR

[ -f "$ENV_FILE" ] || fail ".env.production was not found."
check_docker

info "Creating pre-update backup."
"$SCRIPT_DIR/backup.sh"

if command -v git >/dev/null 2>&1 && [ -d "$ROOT_DIR/.git" ]; then
  info "Pulling latest Git changes with --ff-only."
  git -C "$ROOT_DIR" pull --ff-only
else
  warn "Git repository not found; skipping git pull."
fi

info "Building updated images and applying migrations through backend startup."
compose up --build -d

info "Waiting for health endpoint."
wait_for_health 80 || fail "Health check failed after update."

info "Update complete."
