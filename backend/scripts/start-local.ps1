$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path "$PSScriptRoot\..\.."
$backendRoot = Resolve-Path "$PSScriptRoot\.."

Set-Location $repoRoot

$postgresListener = Get-NetTCPConnection -LocalPort 5432 -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $postgresListener) {
    Write-Host "Starting PostgreSQL via Docker Compose..."
    docker compose up -d postgres
}

Set-Location $backendRoot

Write-Host "Running database migrations..."
alembic upgrade head

Write-Host "Starting FastAPI on http://localhost:8000 ..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
