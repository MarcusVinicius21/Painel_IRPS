$ErrorActionPreference = 'Stop'
$taskRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$taskData = [IO.Path]::GetFullPath((Join-Path $taskRoot '.runtime/postgres-data'))
if (-not $taskData.StartsWith($taskRoot + [IO.Path]::DirectorySeparatorChar)) { throw 'Diretório fora da aplicação local.' }
& (Join-Path $taskRoot '_tools/postgresql/bin/pg_ctl.exe') -D $taskData -m fast -w stop
