param(
  [Parameter(Mandatory = $true)][string]$BackupPath,
  [string]$ConfirmText = "",
  [switch]$Force
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\common.ps1"

if (-not (Test-Path $EnvFile)) {
  Fail ".env.production was not found."
}
if (-not (Test-Path $BackupPath)) {
  Fail "Backup file not found: $BackupPath"
}
Test-DockerReady

$confirmation = if ($Force) { "RESTORE CLINIC DATA" } elseif ($ConfirmText) { $ConfirmText } else { Read-Host "Type RESTORE CLINIC DATA to restore this backup" }
if ($confirmation -ne "RESTORE CLINIC DATA") {
  Fail "Restore cancelled."
}

Write-Info "Ensuring postgres service is running."
Invoke-Compose up --detach postgres
if (-not (Wait-Postgres -Attempts 45)) {
  Fail "Postgres was not ready for restore."
}

Write-Info "Stopping application services before restore."
$previousErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& docker compose --env-file $EnvFile -f $ComposeFile stop nginx frontend backend
$stopExitCode = $LASTEXITCODE
$ErrorActionPreference = $previousErrorActionPreference
if ($stopExitCode -ne 0) {
  Fail "Failed to stop application services before restore."
}

Write-Info "Copying backup into postgres container."
$postgresContainer = (& docker compose --env-file $EnvFile -f $ComposeFile ps -q postgres).Trim()
if (-not $postgresContainer) {
  Fail "Postgres container was not found."
}
& docker cp $BackupPath "${postgresContainer}:/tmp/restore.dump"
if ($LASTEXITCODE -ne 0) {
  Fail "Failed to copy backup into container."
}

Write-Info "Restoring database."
$restoreCommand = @'
set -eu
psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$POSTGRES_DB' AND pid != pg_backend_pid();"
dropdb --if-exists -U "$POSTGRES_USER" "$POSTGRES_DB"
createdb -U "$POSTGRES_USER" "$POSTGRES_DB"
pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner /tmp/restore.dump
rm -f /tmp/restore.dump
'@
& docker compose --env-file $EnvFile -f $ComposeFile exec -T postgres sh -c $restoreCommand
if ($LASTEXITCODE -ne 0) {
  Fail "Database restore command failed."
}
Write-Info "Restarting application services."
Invoke-Compose up --detach --no-build
if (-not (Wait-Health -Attempts 60)) {
  Fail "Health check failed after restore."
}
Write-Info "Restore complete."
