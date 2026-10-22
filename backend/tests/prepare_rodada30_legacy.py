"""Cria somente uma cópia de estudo legado no PostgreSQL descartável local."""
from pathlib import Path
import os,sys,json
from uuid import uuid4
root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/'backend'))
os.environ['IRPS_LOCAL_CONFIG']=str(root/'.runtime/sequence-05-06/config-browser.json')
from app.config import load_settings
from app.main import create_app
from app.db import DB,encoded
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from fastapi.testclient import TestClient
s=load_settings();u=make_url(s.owner_database_url.get_secret_value())
assert s.testing and s.auth_mode=='local_test' and u.host=='127.0.0.1' and u.database.startswith('irps_multi_i0503_')
f=json.loads((root/'.runtime/rodada30/testing/browser-fixture.json').read_text(encoding='utf-8'))
with TestClient(create_app(s)) as c:
 assert c.post('/api/v1/auth/test-login',json={'user_key':'compras-a'}).status_code==200
 identity=c.get('/api/v1/auth/context').json();original=c.get('/api/v1/director/studies/'+f['base']).json()
 payload=json.loads(json.dumps(original['payload']));payload['name']='Estudo legado fictício — teste rodada 30'
 payload['history']={k:v for k,v in payload['history'].items() if k not in ('contract_version','summary','temporal_windows','observed_series')}
 sid=str(uuid4());engine=create_engine(s.owner_database_url.get_secret_value(),hide_parameters=True)
 with engine.begin() as conn:
  db=DB(conn);db.execute("SELECT set_config('irps.org_id',:o,true)",{'o':identity['org_id']})
  db.execute('INSERT INTO director_study(org_id,id,scenario_id,scenario_revision,payload,context_sha256,created_by) VALUES (:o,:i,:s,:v,CAST(:p AS jsonb),:h,:a)',{'o':identity['org_id'],'i':sid,'s':original['scenario_id'],'v':original['scenario_revision'],'p':encoded(payload),'h':'b'*64,'a':identity['actor_id']})
 engine.dispose();assert c.get('/api/v1/director/studies/'+sid).status_code==200
 assert c.get('/api/v1/director/studies/'+f['base']).json()['payload']==original['payload']
 (root/'.runtime/rodada30/testing/legacy.json').write_text(json.dumps({'legacy':sid,'original':f['base'],'synthetic':True}),encoding='utf-8')
print('Cópia legada de teste criada; estudo original preservado, sem remoção de dados.')
