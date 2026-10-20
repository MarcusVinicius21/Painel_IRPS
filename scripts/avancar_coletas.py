"""One bounded scheduler tick for already authorized local PNCP collections.

Use an external scheduler to invoke this process. User-paused jobs are excluded.
"""
import argparse
import json
import os
import sys
from pathlib import Path

from sqlalchemy import create_engine,text

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.config import load_settings
from app.db import Database
from app import history


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--collections',type=int,default=5)
    parser.add_argument('--pages-each',type=int,default=1)
    args=parser.parse_args()
    if not 1<=args.collections<=20 or not 1<=args.pages_each<=3:parser.error('Limite: 20 coletas, até 3 páginas por coleta.')
    os.environ.setdefault('IRPS_LOCAL_CONFIG',str(ROOT/'.runtime/config-local.json'))
    settings=load_settings()
    if settings.auth_mode!='local_test' or settings.ai_enabled:parser.error('Esta rotina opera somente no ambiente local de testes, sem IA paga.')
    owner=create_engine(settings.owner_database_url.get_secret_value(),hide_parameters=True)
    with owner.connect() as conn:
        rows=conn.execute(text("""SELECT id,org_id,actor_id FROM history_collection
            WHERE dataset='official' AND (state IN ('ready','running') OR
              (state='paused' AND error_code<>'USER_PAUSED' AND resume_after<=now()))
            ORDER BY updated_at,id LIMIT :limit"""),{'limit':args.collections}).mappings().all()
    owner.dispose()
    db=Database(settings);results=[]
    try:
        for row in rows:
            result=history.advance(db,str(row['org_id']),str(row['actor_id']),str(row['id']),args.pages_each)
            results.append({'collection_id':str(row['id']),**result})
    finally:db.engine.dispose()
    print(json.dumps({'collections_examined':len(rows),'results':results},ensure_ascii=False))


if __name__=='__main__':main()
