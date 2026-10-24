"""Import a validated local triage CSV only after the restored operational backup gate."""
import csv,json,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.config import load_settings
from app.db import Database
from app.sources import job_context
from app.portfolio_rules import VERSION,classify
from app.portfolio_import import import_rows
from monthly_import_support import backup_gate


def main():
    s=load_settings()
    if s.auth_mode!='operational_local':raise ValueError('EXPLICIT_OPERATIONAL_LOCAL_CONFIG_REQUIRED')
    folder=ROOT/'.runtime/irps-fcp';file=folder/'portfolio-correspondencias.csv';raw=file.read_bytes();rows=list(csv.DictReader(raw.decode('utf-8').splitlines()))
    report=json.loads((folder/'portfolio-classification.json').read_text(encoding='utf-8'))
    if report['rule_version']!=VERSION or len(rows)!=sum(report['classified_pairs'].values()):raise ValueError('INCOMPLETE_TRIAGE')
    for row in rows:
        matches=classify(row);match=next((m for m in matches if m['group_id']==row['group_id']),None)
        if not match or any(str(match[k])!=row[k] for k in ('technical_status','commercial_status','reason','subgroup','rule_version')):
            raise ValueError('TRIAGE_RULE_MISMATCH')
    d=Database(s)
    try:
        with d.transaction(s.operator_org_id,s.operator_actor_id) as db:
            counts={t:db.one('SELECT count(*) AS n FROM '+t)['n'] for t in ('national_catalogue_entry','procurement_fact','price_monthly_snapshot','price_monthly_record')}
            proof=json.loads((folder/'FCP01-backup.json').read_text());backup_gate(proof,s,counts,len(raw))
            snapshots={str(x['id']):x for x in db.all('SELECT id,kind,sha256 FROM national_catalogue_snapshot')}
            for row in rows:
                original=snapshots.get(row['snapshot_id'])
                if not original or row['kind']!=original['kind'] or row['snapshot_sha256']!=original['sha256']:raise ValueError('SNAPSHOT_IDENTITY_MISMATCH')
            result=import_rows(job_context(db,s.operator_org_id,s.operator_actor_id),rows,
                rule_sha256=hashlib.sha256((ROOT/'backend/app/portfolio_rules.py').read_bytes()).hexdigest(),
                input_sha256=hashlib.sha256(raw).hexdigest(),provenance={'triage_report':report['at'],
                    'catalogue_rows_scanned':report['catalogue_rows_scanned'],'commercial_confirmation':False})
        (folder/'import-proof.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
    finally:d.engine.dispose()


if __name__=='__main__':main()
