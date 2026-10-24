"""Current-user Windows DPAPI storage. Never return a credential through an API."""
import os,subprocess,shutil
from pathlib import Path

def load_portal_key():
    value=os.environ.get('PORTAL_API_KEY')
    if value:return value
    path=Path(__file__).resolve().parents[2]/'.runtime/integracoes-118/secrets/portal-api-key.dpapi'
    if os.name!='nt' or not path.is_file():return None
    # Fixed script; the path is an environment value, never interpolated as code.
    script="$s=(Get-Content -LiteralPath $env:IRPS_PORTAL_DPAPI_PATH -Raw).Trim() | ConvertTo-SecureString; $p=[Runtime.InteropServices.Marshal]::SecureStringToBSTR($s); try {[Console]::Write([Runtime.InteropServices.Marshal]::PtrToStringBSTR($p))} finally {[Runtime.InteropServices.Marshal]::ZeroFreeBSTR($p)}"
    executable=shutil.which('pwsh.exe') or shutil.which('powershell.exe')
    if not executable:return None
    result=subprocess.run([executable,'-NoProfile','-NonInteractive','-Command',script],
        env={**os.environ,'IRPS_PORTAL_DPAPI_PATH':str(path)},capture_output=True,timeout=15)
    if result.returncode:return None
    key=result.stdout.decode('utf-8').strip()
    return key if key and '\n' not in key and len(key)<512 else None
