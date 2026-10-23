"""Bounded official pilot using existing collectors; no mocks or synthetic seeds."""
import argparse,json,os,sys,time
from datetime import date,timedelta,datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.config import load_settings
from app.db import Database,normalize,encoded
from app.security import Context
from app import sources,history_sources

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--max-requests',type=int,default=24);args=parser.parse_args()
    if not 1<=args.max_requests<=30:raise SystemExit('Limite permitido: 1 a 30 consultas.')
    settings=load_settings()
    if settings.auth_mode!='operational_local':raise SystemExit('Selecione o banco operacional separado.')
    database=Database(settings);out=ROOT/'docs/IRPS_PILOTO_REAL_LOGIN_UNICO';out.mkdir(exist_ok=True)
    evidence=out/'consultas-oficiais.json'
    log=json.loads(evidence.read_text(encoding='utf-8')) if evidence.exists() else []
    paused=set();budget=args.max_requests
    def consult(parameters,collector=sources.sync):
        nonlocal budget
        if budget<=0 or parameters['provider'] in paused:return None
        budget-=1
        entry={'at':datetime.now(timezone.utc).isoformat(),'arguments':parameters,'network':'live_official_public_get'}
        try:
            with database.transaction(settings.operator_org_id,settings.operator_actor_id) as db:
                ctx=Context(db,settings.operator_org_id,settings.operator_actor_id,'planner','consortium','Operador CONSORMULTI','CONSORMULTI','pilot',True)
                result=collector(ctx,parameters);entry.update(state='success',result=normalize(result))
        except sources.SourceFault as exc:
            entry.update(state='failed',error=exc.code,http_status=exc.status,retry_after=exc.retry_after)
            if exc.code in ('RATE_LIMIT','SOURCE_UNAVAILABLE'):paused.add(parameters['provider'])
        log.append(entry);(out/'consultas-oficiais.json').write_text(json.dumps(log,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({'provider':parameters['provider'],'state':entry['state'],'records':entry.get('result',{}).get('records'),'error':entry.get('error')}),flush=True)
        time.sleep(1)
        return entry
    for code in ['3131307','3168705']:consult({'provider':'IBGE','municipality_ibge':code})
    with database.transaction(settings.operator_org_id) as db:
        if not db.one("SELECT ibge FROM municipality WHERE ibge='3131307'"):raise SystemExit('Identidade IBGE de Ipatinga não comprovada. PNCP não foi iniciado.')
    # A week per request; widen only after an empty week, never silently change scope.
    publications=[]
    for week in range(3):
        end=date.today()-timedelta(days=7*week);start=end-timedelta(days=6)
        for modality in [6,8,4,9]:
            consult({'provider':'PNCP','municipality_ibge':'3131307','start_date':start.isoformat(),'end_date':end.isoformat(),'modality':modality,'page':1,'size':10})
        with database.transaction(settings.operator_org_id) as db:
            publications=db.all("SELECT id FROM procurement_fact WHERE provider='PNCP' AND classification='official' AND is_current ORDER BY event_date DESC,id LIMIT 2")
        if publications:break
    for row in publications:
        consult({'provider':'PNCP_ITENS','procurement_id':str(row['id']),'page':1,'size':10})
    with database.transaction(settings.operator_org_id) as db:
        items=db.all("SELECT id FROM procurement_fact WHERE provider='PNCP_ITENS' AND classification='official' AND is_current ORDER BY event_date DESC,id LIMIT 2")
    for row in items:consult({'provider':'PNCP_RESULTADOS','procurement_id':str(row['id'])},history_sources.results)
    with database.transaction(settings.operator_org_id) as db:
        facts=db.all('''SELECT f.id,f.provider,f.phase,f.municipality_ibge,f.obligation_id,f.item_id,f.item_version,f.description,f.unit,
            f.quantity,f.unit_price,f.amount,f.event_date,f.metadata,s.url,s.consulted_at,s.sha256 FROM procurement_fact f
            JOIN source_observation s ON s.id=f.source_id WHERE f.classification='official' AND f.is_current ORDER BY f.provider,f.id''')
        inventory={'collected_at':datetime.now(timezone.utc).isoformat(),'requests_attempted':len(log),'max_requests':args.max_requests,
            'municipalities':db.all('SELECT * FROM municipality ORDER BY ibge'),'records':normalize(facts),
            'synthetic_facts':db.one("SELECT count(*) AS n FROM procurement_fact WHERE classification='synthetic'")['n'],
            'coverage_notice':'Piloto pontual, primeira página. Não comprova cobertura histórica, consumo ou pagamento.'}
        assert inventory['synthetic_facts']==0
    (out/'dados-oficiais.json').write_text(json.dumps(normalize(inventory),ensure_ascii=False,indent=2),encoding='utf-8')
    database.engine.dispose()

if __name__=='__main__':main()
