"""Validate the versioned 118-target roster against saved official IBGE responses.

--apply requires a fresh, restored backup and never calls operational seed.
"""
import argparse,csv,hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.monitoring import reconcile,register
from app.config import load_settings
from app.db import Database
from app.sources import job_context,observe
from monthly_import_support import backup_gate

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    folder=ROOT/'.runtime/integracoes-118';origin_file=ROOT/'dados/municipios_118_origem.csv'
    origin=list(csv.DictReader(origin_file.read_text(encoding='utf-8-sig').splitlines(),delimiter=';'))
    refs=json.loads((ROOT/'backend/seed_data/cities.json').read_text(encoding='utf-8-sig'))
    raw={uf:(folder/('ibge-'+uf+'.json')).read_bytes() for uf in {r['uf'] for r in refs}}
    fetched=json.loads((folder/'ibge-fetch-proof.json').read_text(encoding='utf-8'))
    expected={r['uf']:r for r in fetched['responses']}
    for uf,b in raw.items():
        p=expected.get(uf,{})
        if p.get('http_status')!=200 or p.get('url')!='https://servicodados.ibge.gov.br/api/v1/localidades/estados/'+uf+'/municipios' or hashlib.sha256(b).hexdigest()!=p.get('sha256'):
            raise ValueError('Official response differs from the actual HTTP proof')
    data={uf:json.loads(b) for uf,b in raw.items()};rows=reconcile(origin,refs,[r for group in data.values() for r in group])
    sha=hashlib.sha256(json.dumps(rows,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    proof={'targets':rows,'roster_sha256':sha,'origin_sha256':hashlib.sha256(origin_file.read_bytes()).hexdigest(),
           'source_sha256':{uf:hashlib.sha256(b).hexdigest() for uf,b in raw.items()},'operational_imported':False}
    if args.apply:
        s=load_settings()
        if s.auth_mode!='operational_local' or s.testing:raise ValueError('Existing operational operator required')
        db=Database(s)
        with db.transaction(s.operator_org_id,s.operator_actor_id) as conn:
            conn.execute('SET LOCAL max_parallel_workers_per_gather=0')
            conn.execute('SET LOCAL enable_indexonlyscan=off')
            conn.execute('SET LOCAL enable_indexscan=off')
            counts={t:conn.one('SELECT count(*) n FROM '+t)['n'] for t in ['national_catalogue_entry','procurement_fact','price_monthly_snapshot','price_monthly_record']}
        backup_gate(json.loads((folder/'CI01-backup-sequential.json').read_text()),s,counts,sum(map(len,raw.values())))
        subprocess.run([sys.executable,'-m','alembic','upgrade','0017'],cwd=ROOT/'backend',check=True)
        with db.transaction(s.operator_org_id,s.operator_actor_id) as conn:
            ctx=job_context(conn,s.operator_org_id,s.operator_actor_id)
            source_ids={uf:observe(ctx,'IBGE','https://servicodados.ibge.gov.br/api/v1/localidades/estados/'+uf+'/municipios',200,b,
                          {'purpose':'monitoring_identity','membership_confirmed':False}) for uf,b in raw.items()}
            proof['result']=register(ctx,rows,source_ids,sha);proof['operational_imported']=True
        db.engine.dispose()
    (folder/'CI03-roster.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'targets':len(rows),'roster_sha256':sha,'operational_imported':proof['operational_imported']}))

if __name__=='__main__':main()
