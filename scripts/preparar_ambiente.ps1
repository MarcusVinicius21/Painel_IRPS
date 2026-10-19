param([string]$PythonExe = 'python')
$ErrorActionPreference = 'Stop'
$taskRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$taskPython = Join-Path $taskRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) { & $PythonExe -m venv (Join-Path $taskRoot '.venv'); if ($LASTEXITCODE) { throw 'Falha na criação do ambiente Python.' } }
& $taskPython -m pip install 'pip==26.2.1'
if ($LASTEXITCODE) { throw 'Falha na atualização do instalador isolado.' }
& $taskPython -m pip install --requirement (Join-Path $taskRoot 'backend/requirements.lock')
if ($LASTEXITCODE) { throw 'Falha na instalação Python.' }
Push-Location (Join-Path $taskRoot 'frontend')
try { & npm.cmd ci --include=dev --ignore-scripts; if ($LASTEXITCODE) { throw 'Falha na instalação do frontend.' } }
finally { Pop-Location }
if (-not (Test-Path -LiteralPath (Join-Path $taskRoot '_tools/postgresql/bin/postgres.exe'))) { & $taskPython (Join-Path $PSScriptRoot 'obter_postgres.py'); if ($LASTEXITCODE) { throw 'Falha na obtenção dos binários locais.' } }
& $taskPython (Join-Path $PSScriptRoot 'iniciar_postgres.py')
if ($LASTEXITCODE) { throw 'Falha no PostgreSQL local.' }
$env:IRPS_LOCAL_CONFIG = Join-Path $taskRoot '.runtime/config-local.json'
Push-Location (Join-Path $taskRoot 'backend')
try { & $taskPython -m alembic upgrade head; if ($LASTEXITCODE) { throw 'Falha nas migrações.' }; & $taskPython -m app.seed; if ($LASTEXITCODE) { throw 'Falha na carga de testes.' }; & $taskPython -m app.opportunity_demo; if ($LASTEXITCODE) { throw 'Falha na carga do exemplo controlado de oportunidades.' } }
finally { Pop-Location }
Write-Output 'Ambiente local preparado. Inicie a API e o frontend em terminais separados.'
