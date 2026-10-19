$ErrorActionPreference = 'Stop'
$taskRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Push-Location (Join-Path $taskRoot 'frontend')
try { & npm.cmd run dev }
finally { Pop-Location }
