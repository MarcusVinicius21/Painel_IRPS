"""Bounded real PNCP collection; no seed, national reimport or parallel collector."""
import sys,json,argparse
from pathlib import Path
from datetime import date
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.config import load_settings
from app.db import Database,normalize
from app.sources import job_context
from app.monitoring_collection import windows,plan_city,municipality_summary
from app.campaign_worker import tick

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--plan',action='store_true');p.add_argument('--execute',action='store_true');p.add_argument('--report',action='store_true');a=p.parse_args()
    s=load_settings()
    if s.auth_mode!='operational_local' or s.ai_enabled:raise ValueError('Existing local operational operator required')
    db=Database(s);folder=ROOT/'.runtime/integracoes-118';today=date.today();periods=windows(today);plans=[]
    with db.transaction(s.operator_org_id,s.operator_actor_id) as conn:
        cities=[r['municipality_ibge'] for r in conn.all('SELECT municipality_ibge FROM monitoring_target WHERE org_id=:o AND monitoring_enabled ORDER BY municipality_ibge',{'o':s.operator_org_id})]
    if len(cities)!=118:raise ValueError('Exactly 118 validated monitoring targets required')
    # Materialize latest closed month first. Remaining months are persistent
    # scheduled work in CI07, not fabricated completed coverage.
    first,last=periods[-2]
    if a.plan:
        for city in cities:
            with db.transaction(s.operator_org_id,s.operator_actor_id) as conn:
                plans.append({'municipality_ibge':city,**plan_city(job_context(conn,s.operator_org_id,s.operator_actor_id),city,first,last)})
        (folder/'CI06-initial-plans.json').write_text(json.dumps(plans,indent=2),encoding='utf-8');print('Validated monthly plans:',len(plans),flush=True)
    if a.execute:
        plans=plans or json.loads((folder/'CI06-initial-plans.json').read_text())
        # First group per city, round robin within a bounded shared lock.
        result=tick(db,s.operator_org_id,s.operator_actor_id,first,last,execute=True,
                    max_attempts=24,max_seconds=150,interval_seconds=4,collection_ids=[r['id'] for r in plans[:20]])
        (folder/'CI06-real-tick.json').write_text(json.dumps(normalize(result),indent=2),encoding='utf-8');print(json.dumps({'pages':result.get('pages'),'attempts':result.get('attempts'),'busy':result.get('busy',False)}),flush=True)
    if a.report:
        records=[]
        for city in cities:
            with db.transaction(s.operator_org_id,s.operator_actor_id) as conn:
                records.append(municipality_summary(job_context(conn,s.operator_org_id,s.operator_actor_id),city,periods[0][0],periods[-2][1]))
        (folder/'CI06-coverage-118.json').write_text(json.dumps(records,indent=2),encoding='utf-8');print('Municipal coverage rows:',len(records),flush=True)
    db.engine.dispose()

if __name__=='__main__':main()
