param(
  [string]$ConfirmText = ""
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\common.ps1"

if (-not (Test-Path $EnvFile)) {
  Fail ".env.production was not found."
}
Test-DockerReady

Write-Host "This stops containers but keeps Docker volumes by default."
Write-Host "Run a backup first with .\deploy\backup.ps1."
$confirmation = if ($ConfirmText) { $ConfirmText } else { Read-Host "Type DELETE ALL CLINIC DATA to also remove volumes, or press Enter to keep data" }
if ($confirmation -eq "DELETE ALL CLINIC DATA") {
  Invoke-Compose down --volumes
  Write-Info "Containers and volumes removed."
} else {
  Invoke-Compose down
  Write-Info "Containers stopped. Volumes were kept."
}
