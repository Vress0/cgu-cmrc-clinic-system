$ErrorActionPreference = "Stop"
. "$PSScriptRoot\common.ps1"

if (-not (Test-Path $EnvFile)) {
  Fail ".env.production was not found."
}
Test-DockerReady

Write-Info "Creating pre-update backup."
& "$PSScriptRoot\backup.ps1"

if (Test-CommandExists git) {
  if (Test-Path (Join-Path $RepoRoot ".git")) {
    Write-Info "Pulling latest Git changes with --ff-only."
    git -C $RepoRoot pull --ff-only
    if ($LASTEXITCODE -ne 0) {
      Fail "git pull --ff-only failed."
    }
  }
}

Write-Info "Building updated images and applying migrations through backend startup."
Invoke-Compose up --build --detach
if (-not (Wait-Health -Attempts 80)) {
  Fail "Health check failed after update."
}
Write-Info "Update complete."
