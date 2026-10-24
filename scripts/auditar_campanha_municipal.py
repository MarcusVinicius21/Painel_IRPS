"""Read-only PNCP reconciliation; request percentages never mean municipal purchase coverage."""
from pathlib import Path
from datetime import date,datetime,timezone
import argparse,json,sys
from sqlalchemy.engine import make_url
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.config import load_settings
from app.db import Database
from app.sources import job_context
from app.campaign_audit import audit


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--start',type=date.fromisoformat,default=date(2025,10,1))
    parser.add_argument('--end',type=date.fromisoformat,default=date(2026,9,30))
    args=parser.parse_args();settings=load_settings()
    if settings.auth_mode!='operational_local' or make_url(settings.database_url.get_secret_value()).host not in ('localhost','127.0.0.1','::1'):
        parser.error('Use explicitamente o banco operacional local.')
    database=Database(settings);database.engine.update_execution_options(isolation_level='REPEATABLE READ')
    try:
        with database.transaction(settings.operator_org_id,settings.operator_actor_id) as db:
            db.execute('SET TRANSACTION READ ONLY');ctx=job_context(db,settings.operator_org_id,settings.operator_actor_id)
            report=audit(ctx,args.start,args.end,all_groups=True);report['at']=datetime.now(timezone.utc).isoformat()
        folder=ROOT/'.runtime/irps-municipal';folder.mkdir(exist_ok=True)
        target=folder/('reconciliation-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'.json')
        target.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({k:v for k,v in report.items() if k!='groups'},ensure_ascii=False))
        print(json.dumps({'evidence_file':str(target)},ensure_ascii=False))
    finally:database.engine.dispose()


if __name__=='__main__':main()
