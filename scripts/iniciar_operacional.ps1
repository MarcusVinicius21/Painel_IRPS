param([int]$ApiPort=5295,[int]$FrontendPort=5296)
$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
$configPath=Join-Path $projectRoot '.runtime/operacional-local/config.json'
if (-not (Test-Path -LiteralPath $configPath)) { throw 'Prepare primeiro o ambiente operacional separado.' }
$env:IRPS_LOCAL_CONFIG=$configPath
$env:IRPS_API_PORT="$ApiPort"
$env:IRPS_FRONTEND_PORT="$FrontendPort"
$runtimePath=Join-Path $projectRoot '.runtime/operacional-local'
Start-Process -FilePath (Join-Path $projectRoot '.venv/Scripts/python.exe') -ArgumentList '-m','uvicorn','app.main:create_app','--factory','--host','127.0.0.1','--port',"$ApiPort",'--app-dir','backend' -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $runtimePath 'api.out.log') -RedirectStandardError (Join-Path $runtimePath 'api.err.log')
Start-Process -FilePath 'cmd.exe' -ArgumentList '/c','npm.cmd run dev' -WorkingDirectory (Join-Path $projectRoot 'frontend') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $runtimePath 'frontend.out.log') -RedirectStandardError (Join-Path $runtimePath 'frontend.err.log')
Write-Output "IRPS local: http://127.0.0.1:$FrontendPort"
