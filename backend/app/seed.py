"""Idempotent LOCAL synthetic accounts and fixtures. Never enabled for OIDC production."""
import hashlib,json
from pathlib import Path
from sqlalchemy import create_engine,text
from .config import load_settings
from .db import DB,encoded
from .security import TEST_USERS,stable_id

def seed(settings=None):
 settings=settings or load_settings()
 if settings.auth_mode!='local_test':raise RuntimeError('A carga de testes exige local_test.')
 engine=create_engine(settings.owner_database_url.get_secret_value(),hide_parameters=True)
 root=Path(__file__).resolve().parents[1]/'seed_data'
 with engine.begin() as conn:
  db=DB(conn)
  for c in json.loads((root/'cities.json').read_text(encoding='utf-8')):
   db.execute('INSERT INTO municipality(ibge,name,uf,origin) VALUES (:i,:n,:u,:p) ON CONFLICT(ibge) DO NOTHING',{'i':c['id'],'n':c['name'],'u':c['uf'],'p':'Cadastro conciliado no Comando 5; atualização pública separada por observação.'})
  for i in json.loads((root/'items.json').read_text(encoding='utf-8')):
   db.execute("INSERT INTO item_version(id,version,name,family,unit,step,example_price,classification) VALUES (:i,:v,:n,:f,:u,:s,:p,'synthetic') ON CONFLICT(id,version) DO NOTHING",{'i':i['id'],'v':i['version'],'n':i['name'],'f':i['family'],'u':i['unit'],'s':str(i['step']),'p':str(i['price'])})
  for u in TEST_USERS:
   org=stable_id('org:'+u.get('org_key',u['key']));actor=stable_id('actor:'+u['key'])
   db.execute('INSERT INTO organization(id,name,kind) VALUES (:i,:n,:k) ON CONFLICT(id) DO NOTHING',{'i':org,'n':u['org'],'k':u['kind']})
   db.execute('INSERT INTO actor(id,issuer,subject,name) VALUES (:i,:iss,:s,:n) ON CONFLICT(id) DO NOTHING',{'i':actor,'iss':settings.issuer,'s':u['key'],'n':u['name']})
   db.execute('INSERT INTO membership(org_id,actor_id,role) VALUES (:o,:a,:r) ON CONFLICT(org_id,actor_id) DO NOTHING',{'o':org,'a':actor,'r':u['role']})
   if u['key'] not in ('compras-a','compras-b','empresa-a','empresa-b'):continue
   db.execute("SELECT set_config('irps.org_id',:o,true)",{'o':org})
   url='https://example.invalid/irps/'+org;body=encoded({'synthetic':True,'scope':'local-tests'})
   source=stable_id('source:'+org)
   db.execute("INSERT INTO source_observation(id,org_id,provider,url,http_status,sha256,body,metadata,classification) VALUES (:i,:o,'SYNTHETIC',:u,200,:h,:b,'{}','synthetic') ON CONFLICT(id) DO NOTHING",{'i':source,'o':org,'u':url,'h':hashlib.sha256(body.encode()).hexdigest(),'b':body})
   buyer=stable_id('buyer:'+org)
   city='3131307' if u['key'] in ('compras-a','empresa-a') else '3101607'
   db.execute("INSERT INTO buyer(id,org_id,name,municipality_ibge,government_level,classification,external_identity) VALUES (:i,:o,:n,:c,'municipal','synthetic',:e) ON CONFLICT(id) DO NOTHING",{'i':buyer,'o':org,'n':'Órgão fictício '+u['key'],'c':city,'e':org+':buyer'})
   # Different obligations for A and B; nothing can be inferred from a city name alone.
   obligation='O-A' if city=='3131307' else 'O-B'
   facts=[('contract','contratado','100','250','25000','2024-08-10'),('contract25','contratado','120','260','31200','2025-08-10'),('contract26','contratado','110','270','29700','2026-08-10'),('paid','pago',None,None,'10000','2026-08-20'),('reversal','estorno',None,None,'1000','2026-08-21')]
   for key,phase,qty,price,amount,date in facts:
    event=org+':'+key;fid=stable_id('fact:'+event)
    db.execute("INSERT INTO procurement_fact(id,org_id,classification,provider,event_identity,revision_hash,source_id,buyer_id,municipality_ibge,item_id,item_version,description,unit,quantity,unit_price,amount,phase,event_date,obligation_id,metadata) VALUES (:i,:o,'synthetic','SYNTHETIC',:e,:h,:s,:b,:c,'papel',1,'Papel A4, caixa com 10 resmas','caixa de 10 resmas',:q,:p,:a,:phase,:d,:ob,'{}') ON CONFLICT(id) DO NOTHING",{'i':fid,'o':org,'e':event,'h':hashlib.sha256(event.encode()).hexdigest(),'s':source,'b':buyer,'c':city,'q':qty,'p':price,'a':amount,'phase':phase,'d':date,'ob':obligation})
  # Application never administers memberships through raw DB rights.
  conn.exec_driver_sql('REVOKE INSERT,UPDATE,DELETE ON membership FROM irps_app')
 engine.dispose()
 return {'municipalities':118,'synthetic_items':100,'synthetic_users':len(TEST_USERS),'private_credentials_exported':False}

if __name__=='__main__':print(encoded(seed()))
