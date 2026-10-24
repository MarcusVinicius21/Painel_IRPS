"""Preview local official catalogue; apply explicitly only Saturday 08:00–11:59 BRT."""
import sys,argparse,json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.config import load_settings
from app.db import Database
from app.catalogue_manual import preview,allowed_time
from app.national_catalogue import import_csv

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--file',required=True);p.add_argument('--kind',required=True,choices=['CATMAT','CATSER']);p.add_argument('--sha256',required=True);p.add_argument('--official-origin',required=True);p.add_argument('--apply',action='store_true');a=p.parse_args()
    if not a.official_origin.startswith(('https://dadosabertos.compras.gov.br/','https://www.gov.br/','https://repositorio.dados.gov.br/')):raise ValueError('Verified official origin required')
    s=load_settings();d=Database(s)
    with d.transaction() as db:
        old={r['code']:(r['name'],r['active']) for r in db.all('''SELECT e.code,e.name,e.active FROM national_catalogue_entry e
          WHERE e.snapshot_id=(SELECT id FROM national_catalogue_snapshot WHERE kind=:k ORDER BY imported_at DESC,id DESC LIMIT 1)''',{'k':a.kind})}
    result=preview(a.file,a.kind,a.sha256,old);print(json.dumps(result),flush=True)
    if a.apply:
        if s.auth_mode!='operational_local' or not allowed_time(datetime.now(ZoneInfo('America/Sao_Paulo'))):raise ValueError('Manual import permitted Saturday morning only')
        # Append-only importer retains old snapshots and reuses identical checksums.
        result=import_csv(s.owner_database_url.get_secret_value(),a.file,a.kind,
          origin=json.dumps({'official_url':a.official_origin,'operator_supplied':True}),expected_sha256=a.sha256,expected_records=result['rows'])
        print(json.dumps(result))
    d.engine.dispose()

if __name__=='__main__':main()
