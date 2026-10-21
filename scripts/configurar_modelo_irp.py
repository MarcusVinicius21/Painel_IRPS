"""Create a sanitized local letterhead without copying the original procedure body."""
import sys,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from app.config import load_settings
from app.irp_documents import sanitize_letterhead
from app.db import encoded

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source');args=p.parse_args();settings=load_settings()
    if settings.auth_mode!='local_test':raise SystemExit('Este comando é destinado à configuração local de testes.')
    target=Path(settings.runtime)/'irp-letterhead.docx'
    if Path(args.source).resolve()==target.resolve():raise SystemExit('Escolha o original; ele não será alterado.')
    print(encoded(sanitize_letterhead(args.source,target)))
