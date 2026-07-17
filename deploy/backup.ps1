$ErrorActionPreference = "Stop"
. "$PSScriptRoot\common.ps1"

if (-not (Test-Path $EnvFile)) {
  Fail ".env.production was not found."
}
Test-DockerReady
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

$name = "clinic-backup-$(Get-Date -Format yyyyMMddHHmmss).dump"
Write-Info "Creating PostgreSQL backup $name."
Invoke-Compose exec -T postgres pg_dump -U (Get-EnvValue POSTGRES_USER) -d (Get-EnvValue POSTGRES_DB) -Fc -f "/backups/$name"
$postgresContainer = (& docker compose --env-file $EnvFile -f $ComposeFile ps -q postgres).Trim()
if (-not $postgresContainer) {
  Fail "Postgres container was not found."
}
& docker cp "${postgresContainer}:/backups/$name" (Join-Path $BackupDir $name)
if ($LASTEXITCODE -ne 0) {
  Fail "Failed to copy backup to host."
}
Write-Info "Backup written to $(Join-Path $BackupDir $name)"
