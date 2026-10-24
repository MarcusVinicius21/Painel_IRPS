param([ValidateRange(1024,65535)][int]$ApiPort=5297,[ValidateRange(1024,65535)][int]$FrontendPort=5298)
$ErrorActionPreference='Stop'
if ($ApiPort -eq $FrontendPort) { throw 'Use portas diferentes para API e interface.' }
$projectRoot=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$sourceConfig=Join-Path $projectRoot '.runtime/operacional-local/config.json'
if (-not (Test-Path -LiteralPath $sourceConfig)) { throw 'Configure primeiro o operador e o banco local.' }
$runtimePath=Join-Path $projectRoot '.runtime/irps-fcp'
New-Item -ItemType Directory -Force $runtimePath | Out-Null
$config=Get-Content -LiteralPath $sourceConfig -Raw | ConvertFrom-Json
if ($config.auth_mode -ne 'operational_local' -or $config.ai_enabled) { throw 'Use somente o operador local, sem IA paga.' }
$config.allowed_origins=@(@($config.allowed_origins)+"http://127.0.0.1:$FrontendPort" | Sort-Object -Unique)
$configPath=Join-Path $runtimePath 'operational-preview-config.json'
[System.IO.File]::WriteAllText($configPath,($config | ConvertTo-Json -Depth 20),[System.Text.UTF8Encoding]::new($false))
$env:IRPS_LOCAL_CONFIG=$configPath
$env:IRPS_API_PORT="$ApiPort"
$env:IRPS_FRONTEND_PORT="$FrontendPort"
$apiListening=Get-NetTCPConnection -LocalPort $ApiPort -State Listen -ErrorAction SilentlyContinue
if ($apiListening) {
 $schema=Invoke-RestMethod -Uri "http://127.0.0.1:$ApiPort/openapi.json" -TimeoutSec 10
 if (-not $schema.paths.PSObject.Properties['/api/v1/portfolio/groups']) { throw 'A porta da API está ocupada por outra versão. Escolha outra porta; nenhum processo foi encerrado.' }
} else {
 Start-Process -FilePath (Join-Path $projectRoot '.venv/Scripts/python.exe') -ArgumentList '-m','uvicorn','app.main:create_app','--factory','--host','127.0.0.1','--port',"$ApiPort",'--app-dir','backend','--no-access-log' -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $runtimePath 'api.out.log') -RedirectStandardError (Join-Path $runtimePath 'api.err.log') | Out-Null
}
if (-not (Get-NetTCPConnection -LocalPort $FrontendPort -State Listen -ErrorAction SilentlyContinue)) {
 Start-Process -FilePath 'cmd.exe' -ArgumentList '/c','npm.cmd run dev' -WorkingDirectory (Join-Path $projectRoot 'frontend') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $runtimePath 'frontend.out.log') -RedirectStandardError (Join-Path $runtimePath 'frontend.err.log') | Out-Null
}
Write-Output "Portfólio local: http://127.0.0.1:$FrontendPort/#/portfolio"
Write-Output 'Nenhum coletor, banco ou processo anterior foi encerrado. Use a senha operacional existente.'
