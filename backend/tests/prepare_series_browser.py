"""Synthetic end-to-end filter fixtures; refuses operational databases."""
def main():
    import sys,os,json,csv
    from pathlib import Path
    from uuid import uuid4
    from sqlalchemy import create_engine
    from sqlalchemy.engine import make_url
    r=Path(__file__).resolve().parents[2];sys.path.insert(0,str(r/'backend'))
    os.environ['IRPS_LOCAL_CONFIG']=str(r/'.runtime/history-filters/config.json')
    from app.config import load_settings
    from app.main import create_app
    from app.seed import seed
    from app.db import DB,encoded
    from app.national_catalogue import import_csv
    from fastapi.testclient import TestClient
    settings=load_settings();url=make_url(settings.owner_database_url.get_secret_value())
    assert settings.testing and settings.auth_mode=='local_test' and url.host=='127.0.0.1' and url.database.startswith('irps_history_filters_')
    seed(settings);client=TestClient(create_app(settings));client.post('/api/v1/auth/test-login',json={'user_key':'compras-a'});client.headers['x-csrf-token']=client.cookies.get('irps_csrf');identity=client.get('/api/v1/auth/context').json()
    engine=create_engine(settings.owner_database_url.get_secret_value(),hide_parameters=True)
    item='filter-browser-'+uuid4().hex;pid=str(uuid4());cities=['3131307','3101607']
    with engine.begin() as conn:
        db=DB(conn);db.execute("SELECT set_config('irps.org_id',:o,true)",{'o':identity['org_id']})
        db.execute("INSERT INTO item_version(id,version,name,family,unit,step,classification) VALUES (:i,1,'Papel de teste caixa com 10 resmas','Material','caixa de 10 resmas',1,'official')",{'i':item})
        db.execute("""INSERT INTO canonical_product(org_id,id,name,category,classification,unit_key,package_signature,members,justification,evidence,reviewed_by) VALUES (:o,:i,'Demonstração gerada de filtros','Material','official','CAIXA','CAIXA:10:RESMA',CAST(:members AS jsonb),'Dados gerados para testar filtros','Sem registros oficiais reais neste banco de teste',:a)""",{'o':identity['org_id'],'i':pid,'members':encoded([{'id':item,'version':1}]),'a':identity['actor_id']})
        for index,(provider,city,quantity,amount,unit) in enumerate([
            ('PNCP_RESULTADOS',cities[0],'3','30','caixa de 10 resmas'),
            ('PNCP_RESULTADOS',cities[0],'999','9990','caixa de 20 resmas'),
            ('TESTE_IRPS_FONTE_B',cities[0],'5','50','caixa de 10 resmas'),
            ('TESTE_IRPS_FONTE_B',cities[1],'2','20','caixa de 10 resmas'),
            ('PNCP_RESULTADOS',cities[1],None,None,'caixa de 10 resmas')]):
            sid=str(uuid4());bid=str(uuid4());fid=str(uuid4())
            db.execute("INSERT INTO source_observation(id,org_id,provider,url,http_status,sha256,body,metadata,classification) VALUES (:i,:o,:p,:url,200,:hash,'[]',CAST(:meta AS jsonb),'official')",{'i':sid,'o':identity['org_id'],'p':provider,'url':'https://example.invalid/generated-filter-test/'+fid,'hash':'a'*64,'meta':encoded({'synthetic_test_fixture':True})})
            db.execute("INSERT INTO buyer(id,org_id,name,municipality_ibge,government_level,classification,external_identity) VALUES (:i,:o,'Órgão fictício do teste',:city,'municipal','official',:external)",{'i':bid,'o':identity['org_id'],'city':city,'external':'test-'+bid})
            db.execute("""INSERT INTO procurement_fact(id,org_id,classification,provider,event_identity,revision_hash,source_id,buyer_id,municipality_ibge,item_id,item_version,description,unit,quantity,amount,phase,event_date,obligation_id,metadata) VALUES (:i,:o,'official',:p,:event,:hash,:s,:b,:city,:item,1,'Papel de teste caixa com 10 resmas',:unit,:q,:amount,'homologado',:day,'00000000000001-1-42/2025',CAST(:meta AS jsonb))""",{'i':fid,'day':['2025-01-05','2025-02-05','2025-03-05','2025-05-05','2025-07-05'][index],'event':fid,'o':identity['org_id'],'p':provider,'hash':uuid4().hex,'s':sid,'b':bid,'city':city,'item':item,'unit':unit,'q':quantity,'amount':amount,'meta':encoded({'synthetic_test_fixture':True,'modality':6 if index%2==0 else None})})
    engine.dispose()
    path=r/'.runtime/series-i04-02/browser-catalogue.csv';code=str(int(uuid4().hex[:10],16))
    with path.open('w',encoding='utf-8',newline='') as f:
        writer=csv.writer(f,delimiter=';');writer.writerow(['codigoItem','descricaoItem','statusItem']);writer.writerow([code,'Papel de teste caixa com 10 resmas — demonstração gerada',True])
    entry=import_csv(settings.owner_database_url.get_secret_value(),path,'CATMAT')
    link=client.post('/api/v1/national-catalogue/links',json={'snapshot_id':entry['snapshot_id'],'code':code,'product_id':pid,'justification':'Conferência fictícia do produto e embalagem para teste local.','evidence':'Fixture local gerada; nenhuma compra oficial real.','confirmed':True});assert link.status_code==201,link.text
    body={'classification':'synthetic','snapshot_id':entry['snapshot_id'],'code':code,'product_id':pid,'name':'Demonstração de filtros do histórico','category':'material','specification':'Papel de teste caixa com 10 resmas — dados gerados','unit':'caixa de 10 resmas','quantity_step':'1','municipalities':cities,'phase':'homologado','start':'2025-01-01','end':'2025-12-31','technical_confirmed':True,'technical_evidence':'Dados gerados para teste local, sem validade oficial.'}
    ids={'product_id':pid,'cities':cities,'code':code,'snapshot_id':entry['snapshot_id']}
    for key,filters in [('base',{'provider':None,'only_comparable':False}),('filtered',{'provider':'PNCP_RESULTADOS','only_comparable':True})]:
        response=client.post('/api/v1/director/studies',json={**body,'history_filters':filters});assert response.status_code==201,response.text;ids[key]=response.json()['id']
    (r/'.runtime/series-i04-02/browser-fixture.json').write_text(json.dumps(ids,indent=2));print('I04_02: two persisted synthetic studies, generated facts in distinct months, isolated DB only.')
if __name__=='__main__':main()
