"""Explicit, repeatable synthetic history. Never runs for a production identity."""
from datetime import date
from decimal import Decimal
import hashlib
from sqlalchemy import create_engine
from .config import load_settings
from .db import DB,encoded
from .security import stable_id

def seed_demo(settings=None):
    settings=settings or load_settings()
    if settings.auth_mode!='local_test':raise RuntimeError('Exemplos exigem o emissor local de testes.')
    engine=create_engine(settings.owner_database_url.get_secret_value(),hide_parameters=True)
    with engine.begin() as conn:
        db=DB(conn);cities=[r['ibge'] for r in db.all('SELECT ibge FROM municipality ORDER BY ibge')]
        selected=['3131307','3101607',next(c for c in cities if c not in ('3131307','3101607'))]
        items=db.all("SELECT * FROM item_version WHERE id IN ('papel','medicamento','servico','veiculo') AND version=1")
        for user in ('compras-a','compras-b','empresa-a','empresa-b'):
            org=stable_id('org:'+user);actor=stable_id('actor:'+user);sid=stable_id('opportunity-demo-source:'+org)
            db.execute("SELECT set_config('irps.org_id',:o,true)",{'o':org})
            body=encoded({'synthetic':True,'purpose':'Histórico fictício 2024–2025; não representa compras oficiais.'})
            db.execute("INSERT INTO source_observation(id,org_id,provider,url,http_status,sha256,body,metadata,classification) VALUES (:i,:o,'SYNTHETIC_OPPORTUNITIES',:u,200,:h,:b,CAST(:metadata AS jsonb),'synthetic') ON CONFLICT DO NOTHING",{'i':sid,'o':org,'u':'https://example.invalid/oportunidades/'+org,'h':hashlib.sha256(body.encode()).hexdigest(),'b':body,'metadata':encoded({'synthetic':True})})
            for idx,city in enumerate(selected):
                buyer=stable_id('opportunity-demo-buyer:'+org+city)
                db.execute("INSERT INTO buyer(id,org_id,name,municipality_ibge,government_level,classification,external_identity) VALUES (:i,:o,:n,:c,'municipal','synthetic',:e) ON CONFLICT DO NOTHING",{'i':buyer,'o':org,'n':'Órgão fictício '+city,'c':city,'e':'demo:'+org+city})
                for item in items:
                    for year in (2024,2025):
                        for month in range(1,13):
                            event='demo-opportunity:'+org+':'+city+':'+item['id']+f':{year}-{month:02d}'
                            qty=Decimal((idx+1)*10*(2 if year==2025 else 1));price=item['example_price'] or Decimal(10)
                            db.execute("""INSERT INTO procurement_fact(id,org_id,classification,provider,event_identity,revision_hash,source_id,buyer_id,municipality_ibge,
                                item_id,item_version,description,unit,quantity,unit_price,amount,phase,event_date,obligation_id,metadata)
                                VALUES (:i,:o,'synthetic','SYNTHETIC_OPPORTUNITIES',:e,:h,:s,:b,:c,:item,1,:d,:u,:q,:p,:a,'homologado',:date,:ob,CAST(:m AS jsonb)) ON CONFLICT DO NOTHING""",{
                                'i':stable_id(event),'o':org,'e':event,'h':hashlib.sha256(event.encode()).hexdigest(),'s':sid,'b':buyer,'c':city,'item':item['id'],
                                'd':item['name']+' · registro fictício','u':item['unit'],'q':qty,'p':price,'a':qty*price,'date':date(year,month,15),'ob':event,
                                'm':encoded({'synthetic':True,'record_level':'item','category':item['family'],'modality':6,'currency':'BRL',
                                    'supplier':{'cnpj':f'{idx+1:014d}','name':'Fornecedor fictício '+str(idx+1)},'eligible_result':True})})
            cid=stable_id('opportunity-demo-coverage:'+org)
            scope={'start':'2024-01-01','end':'2025-12-31','municipalities':selected,'modalities':[6],'publications':True,'items':True,'results':True,
                'event_dates_complete':True,'synthetic':True,'note':'Completude exclusivamente do conjunto fictício controlado; não é coleta governamental.'}
            db.execute("INSERT INTO history_collection(org_id,id,actor_id,scope,state,dataset) VALUES (:o,:i,:a,CAST(:s AS jsonb),'completed','synthetic') ON CONFLICT DO NOTHING",{'o':org,'i':cid,'a':actor,'s':encoded(scope)})
    engine.dispose()
    return {'synthetic':True,'period':'2024–2025','organizations':4,'facts_per_organization':len(items)*3*24,'network_requests':0,'human_viability_auto_approved':False}

if __name__=='__main__':print(encoded(seed_demo()))
