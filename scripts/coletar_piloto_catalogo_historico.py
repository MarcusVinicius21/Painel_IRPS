"""Resume a small official PNCP plan; one request at a time with durable checkpoints."""
import argparse,csv,json,sys,time
from pathlib import Path
from datetime import date,timedelta,datetime,timezone
from sqlalchemy.engine import make_url
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.config import load_settings
from app.db import Database,normalize
from app.security import Context
from app.opportunity_schemas import HistoricalScope
from app import history,coverage_inventory

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--target-database',required=True);parser.add_argument('--budget',type=int,default=60);args=parser.parse_args()
    s=load_settings()
    if s.auth_mode!='operational_local' or make_url(s.database_url.get_secret_value()).database!=args.target_database:
        raise SystemExit('Confirme o banco operacional local exato.')
    if not 1<=args.budget<=100:raise SystemExit('Use até 100 tentativas por lote.')
    database=Database(s);runtime=ROOT/'.runtime/catalogo-historico-real';output=ROOT/'docs/IRPS_CATALOGO_HISTORICO_REAL'
    state_path=runtime/'coleta.json'
    state=json.loads(state_path.read_text(encoding='utf-8')) if state_path.exists() else {'database':args.target_database,'org_id':s.operator_org_id,'collections':[],'attempts':[]}
    if state['database']!=args.target_database or state['org_id']!=s.operator_org_id:raise SystemExit('Checkpoint de outro ambiente.')
    def context(db):return Context(db,s.operator_org_id,s.operator_actor_id,'planner','consortium','Operador CONSORMULTI','CONSORMULTI','public-collection',True)
    if not state['collections']:
        for year in [2026,2025]:
            end=min(date(year,10,22),date.today());start=end-timedelta(days=6)
            scope=HistoricalScope(municipalities=['3131307','3168705'],start=start,end=end,modalities=[4,6,8,9],items=True,results=True,size=20,max_pages=80)
            with database.transaction(s.operator_org_id,s.operator_actor_id) as db:collection=history.create(context(db),scope)
            state['collections'].append({'id':str(collection['id']),'start':str(start),'end':str(end),'kind':'publications_items_results'})
        state_path.write_text(json.dumps(state,indent=2),encoding='utf-8')
    used=0
    while used<args.budget:
        progressed=False
        for collection in state['collections']:
            with database.transaction(s.operator_org_id,s.operator_actor_id) as db:current=history.get(context(db),collection['id'])
            if current['state'] in ('completed','limited'):continue
            if current['state']=='paused' and current.get('resume_after') and current['resume_after']>datetime.now(timezone.utc):continue
            used+=1;progressed=True
            result=history.advance(database,s.operator_org_id,s.operator_actor_id,collection['id'],1)
            state['attempts'].append({'at':datetime.now(timezone.utc).isoformat(),'collection':collection['id'],'result':normalize(result)})
            state_path.write_text(json.dumps(state,indent=2),encoding='utf-8')
            print(json.dumps({'attempt':used,'collection':collection['id'],'result':normalize(result)}),flush=True)
            if used>=args.budget:break
            time.sleep(1.2)
        if not progressed:break
    with database.transaction(s.operator_org_id,s.operator_actor_id) as db:
        ledger=db.all('''SELECT c.id AS collection_id,c.scope,t.id AS task_id,t.provider,t.arguments,t.state,t.attempts,t.error_code,
            p.record_count,p.result,p.created_at,s.url,s.sha256,s.http_status,f.municipality_ibge AS parent_city,f.metadata AS parent_metadata
            FROM history_collection c JOIN history_task t ON t.org_id=c.org_id AND t.collection_id=c.id
            LEFT JOIN history_page p ON p.org_id=t.org_id AND p.task_id=t.id
            LEFT JOIN source_observation s ON s.id=p.source_id LEFT JOIN procurement_fact f ON f.id::text=t.arguments->>'procurement_id' WHERE c.org_id=:o ORDER BY c.created_at,t.provider,t.task_key''',{'o':s.operator_org_id})
        collections=[normalize(history.get(context(db),c['id'])) for c in state['collections']]
    (output/'E3_LEDGER.json').write_text(json.dumps(normalize(ledger),ensure_ascii=False,indent=2),encoding='utf-8')
    (output/'E3_COLETAS.json').write_text(json.dumps(collections,ensure_ascii=False,indent=2),encoding='utf-8')
    with (output/'COBERTURA_PNCP_POR_ESCOPO.csv').open('w',encoding='utf-8-sig',newline='') as f:
        fields=['collection_id','provider','municipality','start','end','modality','phase','task_id','page','state','attempts','records','expected_pages','url','http_status','sha256','consulted_at','error','global_completeness']
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for r in normalize(ledger):
            a=r['arguments'];result=r.get('result') or {}
            w.writerow(dict(zip(fields,[r['collection_id'],r['provider'],a.get('municipality_ibge') or r.get('parent_city') or ('CNPJ '+a.get('cnpj','')+' · sem filtro municipal'),a.get('start_date') or r['scope'].get('start'),a.get('end_date') or r['scope'].get('end'),a.get('modality') or (r.get('parent_metadata') or {}).get('modality'),result.get('phase') or ('publicado_estimado' if r['provider'] in ('PNCP','PNCP_ITENS') else ''),r['task_id'],a.get('page'),r['state'],r['attempts'],r.get('record_count'),result.get('expected_pages'),r.get('url'),r.get('http_status'),r.get('sha256'),r.get('created_at'),r.get('error_code'),'Não afirmada'])))
    database.engine.dispose()
    print(json.dumps({'attempts_this_batch':used,'collections':[{k:c[k] for k in ['id','state','pages','records']} for c in collections]}))

if __name__=='__main__':main()
