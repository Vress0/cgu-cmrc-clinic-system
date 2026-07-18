$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$EnvFile = Join-Path $RepoRoot ".env.production"
$ComposeFile = Join-Path $PSScriptRoot "docker-compose.production.yml"
$BackupDir = Join-Path $RepoRoot "backups"

function Write-Info {
  param([string]$Message)
  Write-Host "[INFO] $Message"
}

function Write-Warn {
  param([string]$Message)
  Write-Warning $Message
}

function Fail {
  param([string]$Message)
  throw $Message
}

function Invoke-Compose {
  param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
  & docker compose --env-file $EnvFile -f $ComposeFile @Args
  if ($LASTEXITCODE -ne 0) {
    Fail "docker compose failed: $($Args -join ' ')"
  }
}

function Test-CommandExists {
  param([string]$Name)
  return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function New-RandomToken {
  param([int]$Bytes = 48)
  $buffer = New-Object byte[] $Bytes
  $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
  try {
    $rng.GetBytes($buffer)
  } finally {
    $rng.Dispose()
  }
  return [Convert]::ToBase64String($buffer).TrimEnd("=")
}

function New-RandomPassword {
  $chars = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789"
  $bytes = New-Object byte[] 24
  $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
  try {
    $rng.GetBytes($bytes)
  } finally {
    $rng.Dispose()
  }
  $out = New-Object System.Text.StringBuilder
  foreach ($b in $bytes) {
    [void]$out.Append($chars[$b % $chars.Length])
  }
  return $out.ToString()
}

function Get-EnvValue {
  param([string]$Key)
  if (-not (Test-Path $EnvFile)) {
    return $null
  }
  $line = Get-Content $EnvFile | Where-Object { $_ -match "^$([Regex]::Escape($Key))=" } | Select-Object -Last 1
  if (-not $line) {
    return $null
  }
  return ($line -replace "^$([Regex]::Escape($Key))=", "")
}

function Test-DockerReady {
  if (-not (Test-CommandExists docker)) {
    Fail "Docker is required but was not found."
  }
  & docker compose version *> $null
  if ($LASTEXITCODE -ne 0) {
    Fail "docker compose is required."
  }
  & docker info *> $null
  if ($LASTEXITCODE -ne 0) {
    Fail "Docker Desktop is not running. Start Docker Desktop and retry."
  }
}

function Test-PortAvailable {
  param([int]$Port)
  $listeners = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
  if ($listeners) {
    Fail "Port $Port is already in use."
  }
}

function New-ProductionEnv {
  $composeProjectName = if ($env:COMPOSE_PROJECT_NAME) { $env:COMPOSE_PROJECT_NAME } else { "cgu_cmrc_clinic" }
  $postgresVolumeName = if ($env:POSTGRES_VOLUME_NAME) { $env:POSTGRES_VOLUME_NAME } else { "clinic_postgres_data" }
  $uploadsVolumeName = if ($env:UPLOADS_VOLUME_NAME) { $env:UPLOADS_VOLUME_NAME } else { "clinic_uploads" }
  $backupsVolumeName = if ($env:BACKUPS_VOLUME_NAME) { $env:BACKUPS_VOLUME_NAME } else { "clinic_backups" }
  $publicBase = if ($env:PUBLIC_BASE_URL) { $env:PUBLIC_BASE_URL } else { "http://localhost" }
  $httpPort = if ($env:HTTP_PORT) { $env:HTTP_PORT } else { "80" }
  $postgresDb = if ($env:POSTGRES_DB) { $env:POSTGRES_DB } else { "clinic_system" }
  $postgresUser = if ($env:POSTGRES_USER) { $env:POSTGRES_USER } else { "clinic_system" }
  $postgresPassword = if ($env:POSTGRES_PASSWORD) { $env:POSTGRES_PASSWORD } else { New-RandomPassword }
  $secretKey = if ($env:SECRET_KEY) { $env:SECRET_KEY } else { New-RandomToken }
  $adminUsername = if ($env:DEFAULT_ADMIN_USERNAME) { $env:DEFAULT_ADMIN_USERNAME } else { "admin" }
  $adminEmail = if ($env:DEFAULT_ADMIN_EMAIL) { $env:DEFAULT_ADMIN_EMAIL } else { "admin@example.com" }
  $adminFullName = if ($env:DEFAULT_ADMIN_FULL_NAME) { $env:DEFAULT_ADMIN_FULL_NAME } else { "System Administrator" }
  $adminPassword = if ($env:DEFAULT_ADMIN_PASSWORD) { $env:DEFAULT_ADMIN_PASSWORD } else { New-RandomPassword }
  $databaseUrl = "postgresql+psycopg://${postgresUser}:${postgresPassword}@postgres:5432/${postgresDb}"

  @"
COMPOSE_PROJECT_NAME=$composeProjectName
POSTGRES_VOLUME_NAME=$postgresVolumeName
UPLOADS_VOLUME_NAME=$uploadsVolumeName
BACKUPS_VOLUME_NAME=$backupsVolumeName
APP_ENV=production
APP_NAME=CGU CMRC Clinic System
PUBLIC_BASE_URL=$publicBase

POSTGRES_DB=$postgresDb
POSTGRES_USER=$postgresUser
POSTGRES_PASSWORD=$postgresPassword

DATABASE_URL=$databaseUrl
DATABASE_CONNECT_TIMEOUT_SECONDS=5

SECRET_KEY=$secretKey
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=14

DEFAULT_ADMIN_USERNAME=$adminUsername
DEFAULT_ADMIN_EMAIL=$adminEmail
DEFAULT_ADMIN_FULL_NAME=$adminFullName
DEFAULT_ADMIN_PASSWORD=$adminPassword
ENABLE_DEMO_MODE=$(if ($env:ENABLE_DEMO_MODE) { $env:ENABLE_DEMO_MODE } else { "true" })
DEFAULT_DATA_MODE=$(if ($env:DEFAULT_DATA_MODE) { $env:DEFAULT_DATA_MODE } else { "LIVE" })
ALLOW_DEMO_RESET=$(if ($env:ALLOW_DEMO_RESET) { $env:ALLOW_DEMO_RESET } else { "true" })

BACKEND_CORS_ORIGINS=$publicBase
NEXT_PUBLIC_API_BASE_URL=$publicBase/api/v1
INTERNAL_API_BASE_URL=http://backend:8000/api/v1

HTTP_PORT=$httpPort
HTTPS_PORT=443
"@ | Set-Content -Path $EnvFile -Encoding UTF8
  return $adminPassword
}

function Wait-Health {
  param([int]$Attempts = 60)
  $url = "$(Get-EnvValue PUBLIC_BASE_URL)/api/v1/health"
  for ($i = 1; $i -le $Attempts; $i++) {
    try {
      $response = Invoke-RestMethod -Uri $url -TimeoutSec 5
      if ($response.status -eq "ok" -and $response.database -eq "ok") {
        return $true
      }
    } catch {
    }
    Start-Sleep -Seconds 3
  }
  return $false
}

function Wait-Postgres {
  param([int]$Attempts = 30)
  for ($i = 1; $i -le $Attempts; $i++) {
    & docker compose --env-file $EnvFile -f $ComposeFile exec -T postgres pg_isready -U "$(Get-EnvValue POSTGRES_USER)" -d "$(Get-EnvValue POSTGRES_DB)" *> $null
    if ($LASTEXITCODE -eq 0) {
      return $true
    }
    Start-Sleep -Seconds 2
  }
  return $false
}
