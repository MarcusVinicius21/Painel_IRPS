param([int]$Port = 5211)
$ErrorActionPreference = 'Stop'
$taskRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$env:IRPS_LOCAL_CONFIG = Join-Path $taskRoot '.runtime/config-local.json'
if (-not (Test-Path -LiteralPath $env:IRPS_LOCAL_CONFIG)) { throw 'Prepare o ambiente local antes de iniciar.' }
Push-Location (Join-Path $taskRoot 'backend')
try { & (Join-Path $taskRoot '.venv/Scripts/python.exe') -m uvicorn app.main:app --host 127.0.0.1 --port $Port --no-access-log }
finally { Pop-Location }
