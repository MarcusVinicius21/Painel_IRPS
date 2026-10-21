"""Import only into the explicitly configured local PostgreSQL database."""
import argparse,sys
from pathlib import Path
from urllib.parse import urlparse
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from app.config import load_settings
from app.national_catalogue import import_csv
from app.db import encoded

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('kind',choices=['CATMAT','CATSER']);p.add_argument('path');args=p.parse_args()
    s=load_settings();url=s.owner_database_url.get_secret_value()
    if s.auth_mode!='local_test' or urlparse(url.replace('+psycopg','')).hostname not in ('127.0.0.1','localhost','::1'):
        raise SystemExit('A importação desta rodada exige banco PostgreSQL local de testes.')
    print(encoded(import_csv(url,args.path,args.kind)))
