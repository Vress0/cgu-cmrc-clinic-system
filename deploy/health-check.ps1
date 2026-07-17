$ErrorActionPreference = "Continue"
. "$PSScriptRoot\common.ps1"

if (-not (Test-Path $EnvFile)) {
  Fail ".env.production was not found. Run .\install.ps1 first."
}

$failed = $false
function Check {
  param([string]$Label, [scriptblock]$Block)
  try {
    & $Block *> $null
    Write-Host "$Label`: ok"
  } catch {
    Write-Host "$Label`: failed" -ForegroundColor Red
    $script:failed = $true
  }
}

Check "Docker daemon" { docker info }
Check "Compose config" { Invoke-Compose config --quiet }
Check "PostgreSQL" {
  & docker compose --env-file $EnvFile -f $ComposeFile exec -T postgres pg_isready -U "$(Get-EnvValue POSTGRES_USER)" -d "$(Get-EnvValue POSTGRES_DB)"
  if ($LASTEXITCODE -ne 0) { throw "pg_isready failed" }
}
Check "Backend Health API" { Invoke-Compose exec -T backend python -c "import json, urllib.request; data=json.load(urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health', timeout=5)); raise SystemExit(0 if data.get('status') == 'ok' and data.get('database') == 'ok' else 1)" }
Check "Nginx health endpoint" { if (-not (Wait-Health -Attempts 3)) { throw "health failed" } }
Check "Alembic current" { Invoke-Compose exec -T backend alembic current }

Write-Host "Disk usage:"
Get-PSDrive -PSProvider FileSystem | Format-Table -AutoSize | Out-String | Write-Host

Write-Host "Recent backups:"
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null
Get-ChildItem $BackupDir -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 5 | Format-Table Name, Length, LastWriteTime -AutoSize

if ($failed) {
  exit 1
}
