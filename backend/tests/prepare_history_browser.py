"""Local test helper; requires the isolated Increment 01 fixture database."""

def main():
    import os,json,sys,csv
    from pathlib import Path
    from uuid import uuid4
    r=Path(__file__).resolve().parents[2];sys.path.insert(0,str(r/'backend'));os.environ['IRPS_LOCAL_CONFIG']=str(r/'.runtime/history-contract/config.json')
    from app.main import create_app
    from app.config import load_settings
    from app.national_catalogue import import_csv
    from app.db import DB,encoded
    from sqlalchemy import create_engine
    from fastapi.testclient import TestClient
    settings=load_settings();assert settings.testing and settings.auth_mode=='local_test'
    from sqlalchemy.engine import make_url
    url=make_url(settings.owner_database_url.get_secret_value());assert url.host=='127.0.0.1' and url.database.startswith('irps_history_contract_')
    c=TestClient(create_app(settings));c.post('/api/v1/auth/test-login',json={'user_key':'compras-a'});c.headers['x-csrf-token']=c.cookies.get('irps_csrf')
    path=r/'.runtime/history-contract/test-catalogue.csv';code=str(int(uuid4().hex[:10],16))
    with path.open('w',encoding='utf-8',newline='') as f:
     w=csv.writer(f,delimiter=';');w.writerow(['codigoItem','descricaoItem','statusItem']);w.writerow([code,'Papel de teste caixa com 10 resmas - demonstração gerada',True])
    entry=import_csv(settings.owner_database_url.get_secret_value(),path,'CATMAT')
    params=[('phase','homologado'),('start','2025-01-01'),('end','2025-12-31'),('municipalities','3131307'),('municipalities','3101607')];found={}
    for p in c.get('/api/v1/director/products').json()['records']:
     if p['name']!='Produto fictício para teste do contrato':continue
     h=c.get('/api/v1/director/history/'+p['id'],params=params).json();s=h['summary']
     if s['observed_records']==1 and s['observed_quantity'] is not None and float(s['observed_quantity'])==3 and s['documented_amount'] is not None:found.setdefault('known',p['id'])
     if s['observed_records']==0:found.setdefault('empty',p['id'])
     if s['observed_records']==1 and s['observed_quantity'] is None and s['documented_amount'] is None:found.setdefault('unknown',p['id'])
     if s['observed_records']==2 and s['distinct_processes'] is None:found.setdefault('zero',p['id'])
    ids={};base={'classification':'synthetic','snapshot_id':entry['snapshot_id'],'code':code,'name':'Demonstração gerada: contrato histórico','category':'material','specification':'Papel de teste caixa com 10 resmas. Dados gerados para validar indicadores.','unit':'caixa de 10 resmas','quantity_step':'1','municipalities':['3131307','3101607'],'phase':'homologado','start':'2025-01-01','end':'2025-12-31','technical_evidence':'Conferência fictícia para teste local. Não usar como dado oficial.','technical_confirmed':True}
    for key,pid in found.items():
     resp=c.post('/api/v1/national-catalogue/links',json={'snapshot_id':entry['snapshot_id'],'code':code,'product_id':pid,'justification':'Teste local identificado: mesmo papel e embalagem para verificar o contrato.','evidence':'Fixture gerada no banco isolado; sem dados oficiais reais.','confirmed':True});assert resp.status_code==201,resp.text
     resp=c.post('/api/v1/director/studies',json={**base,'product_id':pid});assert resp.status_code==201,resp.text;ids[key]=resp.json()['id'];ids['expected_'+key]=resp.json()['payload']['history']['summary']
    assert len(found)==4
    known=c.get('/api/v1/director/studies/'+ids['known']).json();payload={**known['payload']};payload['history']={k:v for k,v in payload['history'].items() if k not in ('contract_version','summary','temporal_windows')}
    sid=str(uuid4());identity=c.get('/api/v1/auth/context').json();engine=create_engine(settings.owner_database_url.get_secret_value(),hide_parameters=True)
    with engine.begin() as conn:
     db=DB(conn);db.execute("SELECT set_config('irps.org_id',:o,true)",{'o':identity['org_id']});db.execute('INSERT INTO director_study(org_id,id,scenario_id,scenario_revision,payload,context_sha256,created_by) VALUES (:o,:i,:s,1,CAST(:p AS jsonb),:h,:a)',{'o':identity['org_id'],'i':sid,'s':known['scenario_id'],'p':encoded(payload),'h':'b'*64,'a':identity['actor_id']})
    ids['legacy']=sid;engine.dispose();(r/'.runtime/history-contract/browser-fixture.json').write_text(json.dumps(ids,indent=2));print('Ready: 5 persisted synthetic studies, isolated test database only.')

if __name__=="__main__":main()
