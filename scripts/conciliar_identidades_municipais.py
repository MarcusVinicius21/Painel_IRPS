"""Read-only crosswalk of current official municipal facts; never changes totals."""
import json,sys
from pathlib import Path
from datetime import datetime,timezone
from sqlalchemy.engine import make_url
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.config import load_settings
from app.db import Database
from app.sources import job_context
from app.municipal_crosswalk import crosswalk


def main():
    s=load_settings()
    if s.auth_mode!='operational_local' or make_url(s.database_url.get_secret_value()).host not in ('localhost','127.0.0.1','::1'):
        raise ValueError('EXPLICIT_LOCAL_OPERATIONAL_CONFIG_REQUIRED')
    folder=ROOT/'.runtime/irps-municipal';scope=json.loads((folder/'census.json').read_text())['scope']
    cities=[r['ibge'] for r in scope['municipalities']]
    buyers=json.loads((folder/'buyers.json').read_text())
    cnpjs=sorted({r['cnpj'] for r in buyers if r['state']=='verified' and not r['conflicting_evidence']
        and r['identities'] and all(i['municipal_buyer'] for i in r['identities'])})
    database=Database(s)
    try:
        with database.transaction(s.operator_org_id,s.operator_actor_id) as db:
            db.execute('SET TRANSACTION READ ONLY');ctx=job_context(db,s.operator_org_id,s.operator_actor_id);ctx.require('sources.sync')
            rows=db.all("""SELECT f.id,f.source_id,f.provider,f.phase,f.obligation_id,f.classification,
                f.municipality_ibge,b.cnpj AS buyer_cnpj FROM procurement_fact f
                LEFT JOIN buyer b ON b.id=f.buyer_id AND b.org_id=f.org_id
                WHERE f.org_id=:o AND f.is_current AND f.classification='official'
                AND f.municipality_ibge=ANY(:cities) AND f.event_date BETWEEN '2025-10-01' AND '2026-09-30'
                AND b.government_level='M' AND b.cnpj=ANY(:cnpjs)
                ORDER BY f.id LIMIT 50001""",{'o':ctx.org_id,'cities':cities,'cnpjs':cnpjs})
            if len(rows)>50000:raise ValueError('REDUCE_CROSSWALK_SCOPE')
            result=crosswalk(rows)
        result.update(at=datetime.now(timezone.utc).isoformat(),census_sha256=scope['sha256'])
        (folder/'identity-crosswalk.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        print(json.dumps({k:v for k,v in result.items() if k not in ('processes','pending_match')}))
    finally:database.engine.dispose()


if __name__=='__main__':main()
