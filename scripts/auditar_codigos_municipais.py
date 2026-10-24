"""Exact source/code audit, paged in SQL, preserving all original facts/reviews."""
from pathlib import Path
from datetime import datetime,timezone
import json,sys
from sqlalchemy.engine import make_url
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.config import load_settings
from app.db import Database,normalize
from app.sources import job_context
from app import catalogue_evidence,municipal_catalogue,national_catalogue


def main():
    s=load_settings()
    if s.auth_mode!='operational_local' or make_url(s.database_url.get_secret_value()).host not in ('127.0.0.1','localhost','::1'):
        raise ValueError('LOCAL_OPERATIONAL_CONFIG_REQUIRED')
    folder=ROOT/'.runtime/irps-municipal';scope=json.loads((folder/'census.json').read_text())['scope']
    cities=[c['ibge'] for c in scope['municipalities']];buyers=json.loads((folder/'buyers.json').read_text())
    cnpjs=[b['cnpj'] for b in buyers if b['state']=='verified' and not b['conflicting_evidence']
        and b['identities'] and all(i['municipal_buyer'] for i in b['identities'])]
    database=Database(s);database.engine.update_execution_options(isolation_level='REPEATABLE READ')
    output=[];cursor='00000000-0000-0000-0000-000000000000';cache={}
    try:
        with database.transaction(s.operator_org_id,s.operator_actor_id) as db:
            db.execute('SET TRANSACTION READ ONLY');ctx=job_context(db,s.operator_org_id,s.operator_actor_id);ctx.require('sources.sync')
            snapshots={r['kind']:r for r in db.all('SELECT DISTINCT ON(kind) * FROM national_catalogue_snapshot ORDER BY kind,imported_at DESC,id DESC')}
            while True:
                facts=db.all("""SELECT f.*,s.body AS source_body,s.sha256 AS source_sha256
                    FROM procurement_fact f JOIN source_observation s ON s.id=f.source_id
                    JOIN buyer b ON b.id=f.buyer_id AND b.org_id=f.org_id
                    WHERE f.org_id=:o AND f.is_current AND f.classification='official' AND s.classification='official'
                    AND f.provider='PNCP_ITENS' AND f.municipality_ibge=ANY(:cities)
                    AND b.government_level='M' AND b.cnpj=ANY(:cnpjs)
                    AND f.event_date BETWEEN '2025-10-01' AND '2026-09-30'
                    AND f.id>CAST(:cursor AS uuid) ORDER BY f.id LIMIT 200""",
                    {'o':ctx.org_id,'cities':cities,'cnpjs':cnpjs,'cursor':cursor})
                if not facts:break
                for fact in facts:
                    record=catalogue_evidence.original_record(fact)
                    declaration=catalogue_evidence.declaration(record or {});key=(declaration['namespace'],declaration['code'])
                    if key not in cache:
                        snapshot=snapshots.get(key[0]);entry=None
                        if snapshot and key[1]:
                            row=db.one('SELECT * FROM national_catalogue_entry WHERE snapshot_id=:s AND code=:c',{'s':snapshot['id'],'c':key[1]})
                            if row:entry={**row,'kind':key[0],'sha256':snapshot['sha256'],'origin':snapshot['origin'],
                                'imported_at':snapshot['imported_at'],'snapshot_count':snapshot['row_count']}
                        cache[key]=entry
                    output.append(municipal_catalogue.inspect_binding(fact,cache[key]))
                cursor=str(facts[-1]['id'])
        result={**municipal_catalogue.summarize(output),'at':datetime.now(timezone.utc).isoformat(),
            'records':output,'database_mutated':False,'census_sha256':scope['sha256']}
        (folder/'catalogue-bindings.json').write_text(json.dumps(normalize(result),ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({k:v for k,v in result.items() if k!='records'}))
    finally:database.engine.dispose()


if __name__=='__main__':main()
