$ErrorActionPreference = "Stop"
. "$PSScriptRoot\common.ps1"

Write-Info "Starting one-click production install."
Test-DockerReady

$adminPassword = $null
if (Test-Path $EnvFile) {
  Write-Info ".env.production already exists; reusing it."
} else {
  $httpPort = if ($env:HTTP_PORT) { [int]$env:HTTP_PORT } else { 80 }
  Test-PortAvailable -Port $httpPort
  Write-Info "Creating .env.production with generated secrets."
  $adminPassword = New-ProductionEnv
}

New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

Write-Info "Validating production compose file."
Invoke-Compose config --quiet

Write-Info "Building and starting services."
Invoke-Compose up --build --detach

Write-Info "Waiting for health endpoint."
if (-not (Wait-Health -Attempts 80)) {
  Fail "Health check failed after startup."
}

Write-Info "Current migration:"
Invoke-Compose exec -T backend alembic current

Write-Host "========================================"
Write-Host "Clinic system deployment complete"
Write-Host "========================================"
Write-Host ""
Write-Host "Application URL: $(Get-EnvValue PUBLIC_BASE_URL)"
Write-Host "Admin username: $(Get-EnvValue DEFAULT_ADMIN_USERNAME)"
if ($adminPassword) {
  Write-Host "Generated admin password: $adminPassword"
  Write-Host "This password is shown once. Store it securely, then change it after first login."
} else {
  Write-Host "Admin password: existing .env.production value was reused."
}
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Log in and create named administrator accounts."
Write-Host "2. Configure HTTPS before production use."
Write-Host "3. Run .\deploy\backup.ps1 and store the backup securely."
Write-Host "4. Run .\deploy\health-check.ps1 after any update."
