$ErrorActionPreference = "Stop"
. "$PSScriptRoot\common.ps1"

Write-Output "SECRET_KEY=$(New-RandomToken)"
Write-Output "POSTGRES_PASSWORD=$(New-RandomPassword)"
Write-Output "DEFAULT_ADMIN_PASSWORD=$(New-RandomPassword)"

