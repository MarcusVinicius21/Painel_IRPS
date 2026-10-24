"""Start the reviewed isolated CGU sidecar, loading the key only in child memory."""
import os,sys,subprocess,shutil,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.portal_credentials import load_portal_key

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--poc-isolada',action='store_true',required=True,
        help='Somente teste local por stdio; dependências auditadas têm alertas e não foram liberadas para produção.')
    parser.parse_args()
    sidecar=ROOT/'.runtime/integracoes-118/sidecars/portal-poc'
    node=shutil.which('node')
    runner=sidecar/'node_modules/tsx/dist/cli.mjs'
    entry=ROOT/'scripts/portal_mcp_entry.mjs'
    key=load_portal_key()
    if not key:raise SystemExit('Configure a chave autorizada no armazenamento privado do operador.')
    if not node or not runner.is_file() or not entry.is_file():
        raise SystemExit('O sidecar revisado ainda não está instalado neste ambiente.')
    # No shell interpolation or arbitrary executable/URL supplied by a client.
    return subprocess.run([node,str(runner),str(entry)],cwd=sidecar,
        env={**os.environ,'PORTAL_API_KEY':key}).returncode

if __name__=='__main__':raise SystemExit(main())
