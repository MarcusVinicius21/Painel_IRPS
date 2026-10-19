$ErrorActionPreference = 'Stop'
$taskRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$env:IRPS_LOCAL_CONFIG = Join-Path $taskRoot '.runtime/config-local.json'
Push-Location (Join-Path $taskRoot 'backend')
try { & (Join-Path $taskRoot '.venv/Scripts/python.exe') -m app.opportunity_demo; if ($LASTEXITCODE) { throw 'Não foi possível preparar os exemplos fictícios.' } }
finally { Pop-Location }
