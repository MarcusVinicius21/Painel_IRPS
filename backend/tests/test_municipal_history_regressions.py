"""Focused regressions for canonical scope, request evidence and V4 line lookup."""
from datetime import date
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine

from app import catalogue, coverage_inventory, opportunity_demo, sources
from app.config import load_settings
from app.db import DB, encoded
from test_real_app import scenario, calc, snapshot, put


@pytest.fixture
def prepared(settings):
    opportunity_demo.seed_demo(settings)


def test_canonical_pair_is_filtered_before_limit(login, prepared):
    client=login('compras-a');identity=client.get('/api/v1/auth/context').json()
    engine=create_engine(load_settings().owner_database_url.get_secret_value(),hide_parameters=True)
    # Roll back the large fixture: the API and every subsequent test keep the same clean database.
    with engine.connect() as conn:
        transaction=conn.begin()
        try:
            db=DB(conn);db.execute("SELECT set_config('irps.org_id',:o,true)",{'o':identity['org_id']})
            original=db.one("SELECT source_id,buyer_id FROM procurement_fact WHERE org_id=:o AND item_id='papel' LIMIT 1",{'o':identity['org_id']})
            item='pair-'+uuid4().hex;pid=str(uuid4());prefix=uuid4().hex
            for version in (1,2):
                db.execute("""INSERT INTO item_version(id,version,name,family,unit,step,classification)
                    VALUES (:item,:version,'Papel A4 caixa com 10 resmas','Material','caixa de 10 resmas',1,'synthetic')""",
                    {'item':item,'version':version})
            norm=catalogue.normalized_fact({'description':'Papel A4 caixa com 10 resmas',
                'unit':'caixa de 10 resmas','provider':'SYNTHETIC_OPPORTUNITIES'})
            db.execute("""INSERT INTO canonical_product(org_id,id,name,category,classification,unit_key,
                package_signature,members,justification,evidence,reviewed_by)
                VALUES (:o,:id,'Papel A4 revisado','Material','synthetic',:unit,:package,
                CAST(:members AS jsonb),'Teste de versão exata','Dado sintético local',:actor)""",
                {'o':identity['org_id'],'id':pid,'unit':norm['unit_key'],'package':norm['package_signature'],
                 'members':encoded([{'id':item,'version':1}]),'actor':identity['actor_id']})
            db.execute("""INSERT INTO procurement_fact(id,org_id,classification,provider,event_identity,
                revision_hash,source_id,buyer_id,municipality_ibge,item_id,item_version,description,unit,
                quantity,amount,unit_price,phase,event_date,obligation_id,metadata)
                SELECT gen_random_uuid(),:o,'synthetic','SYNTHETIC_OPPORTUNITIES',:prefix||n::text,
                :prefix||n::text,:source,:buyer,'3131307',:item,2,'Papel A4 caixa com 10 resmas',
                'caixa de 10 resmas',1,10,10,'homologado','2025-01-01',:prefix||n::text,'{}'::jsonb
                FROM generate_series(1,20001) AS n""",
                {'o':identity['org_id'],'prefix':prefix,'source':original['source_id'],
                 'buyer':original['buyer_id'],'item':item})
            db.execute("""INSERT INTO procurement_fact(id,org_id,classification,provider,event_identity,
                revision_hash,source_id,buyer_id,municipality_ibge,item_id,item_version,description,unit,
                quantity,amount,unit_price,phase,event_date,obligation_id,metadata)
                VALUES (:id,:o,'synthetic','SYNTHETIC_OPPORTUNITIES',:event,:event,:source,:buyer,
                '3131307',:item,1,'Papel A4 caixa com 10 resmas','caixa de 10 resmas',3,30,10,
                'homologado','2025-02-01',:event,'{}'::jsonb)""",
                {'id':str(uuid4()),'o':identity['org_id'],'event':prefix+'valid','source':original['source_id'],
                 'buyer':original['buyer_id'],'item':item})
            ctx=sources.job_context(db,identity['org_id'],identity['actor_id'])
            summary=next(row for row in catalogue.products(ctx,'homologado',date(2025,1,1),date(2025,12,31),['3131307'])['records'] if row['id']==pid)
            detail=catalogue.product_history(ctx,pid,'homologado',date(2025,1,1),date(2025,12,31),['3131307'])
            assert summary['observed_records']==1 and float(summary['observed_quantity'])==3
            assert detail['municipalities'][0]['observed_records']==1
            assert float(detail['municipalities'][0]['observed_quantity'])==3
            windows={r['months']:r for r in detail['municipalities'][0]['temporal_windows']}
            assert windows[1]['observed_quantity'] is None and float(windows[12]['observed_quantity'])==3
            assert all(r['monthly_average'] is None and r['recurrence_percentage'] is None for r in windows.values())
            db.execute('UPDATE procurement_fact SET item_version=1 WHERE item_id=:item AND item_version=2',{'item':item})
            with pytest.raises(HTTPException) as summary_limit:
                catalogue.products(ctx,'homologado',date(2025,1,1),date(2025,12,31),['3131307'])
            with pytest.raises(HTTPException) as history_limit:
                catalogue.product_history(ctx,pid,'homologado',date(2025,1,1),date(2025,12,31),['3131307'])
            assert summary_limit.value.status_code==history_limit.value.status_code==422
            assert summary_limit.value.detail['code']==history_limit.value.detail['code']=='CATALOGUE_LIMIT'
        finally:
            transaction.rollback();engine.dispose()


def test_municipality_validation_matches_summary_and_detail(login,prepared):
    client=login('compras-a')
    paths=['/api/v1/catalogue-intelligent/products','/api/v1/catalogue-intelligent/products/'+str(uuid4())+'/history']
    for path in paths:
        for code in ('9999999','invalid'):
            response=client.get(path+'?municipalities='+code)
            assert response.status_code==422 and response.json()['detail']['code']=='MUNICIPALITY_UNKNOWN',(path,code,response.json())
        duplicate=client.get(path+'?municipalities=3131307&municipalities=3131307')
        assert duplicate.status_code in (200,404)
    assert client.get(paths[0]).status_code==200  # Omitted means all permitted cities.
    assert client.get(paths[0]+'?municipalities=3131307').status_code==200


def test_coverage_requires_successful_page_evidence(login):
    client=login('compras-a');identity=client.get('/api/v1/auth/context').json()
    engine=create_engine(load_settings().owner_database_url.get_secret_value(),hide_parameters=True)
    with engine.connect() as conn:
        transaction=conn.begin()
        try:
            db=DB(conn);db.execute("SELECT set_config('irps.org_id',:o,true)",{'o':identity['org_id']})
            ctx=sources.job_context(db,identity['org_id'],identity['actor_id'])
            cid=str(uuid4());tid=str(uuid4());scope={'municipalities':['3131307']}
            pid=str(uuid4())
            db.execute("""INSERT INTO canonical_product(org_id,id,name,category,classification,unit_key,
                members,justification,evidence,reviewed_by)
                VALUES (:o,:id,'Produto sem fatos no recorte','Material','official','UNIDADE',CAST(:members AS jsonb),
                'Teste de cobertura por fase','Consulta local',:actor)""",
                {'o':identity['org_id'],'id':pid,'members':encoded([{'id':'coverage-'+pid,'version':1}]),
                 'actor':identity['actor_id']})
            db.execute("""INSERT INTO history_collection(org_id,id,actor_id,scope,dataset)
                VALUES (:o,:id,:actor,CAST(:scope AS jsonb),'official')""",
                {'o':identity['org_id'],'id':cid,'actor':identity['actor_id'],'scope':encoded(scope)})
            args=encoded({'municipality_ibge':'3131307','start_date':'2031-02-01','end_date':'2031-02-01'})
            db.execute("""INSERT INTO history_task(org_id,collection_id,id,task_key,provider,arguments,state)
                VALUES (:o,:collection,:id,'result-1','PNCP_RESULTADOS',CAST(:args AS jsonb),'ready')""",
                {'o':identity['org_id'],'collection':cid,'id':tid,'args':args})
            def state():
                result=coverage_inventory.inventory(ctx,date(2031,2,1),date(2031,2,1),['3131307'])
                rows=[row for row in result['records'] if row['provider']=='PNCP_RESULTADOS' and row['tasks']]
                assert len(rows)==1
                row=rows[0]
                detail=catalogue.product_history(ctx,pid,'homologado',date(2031,2,1),date(2031,2,1),['3131307'])
                return row,detail['municipalities'][0]['coverage_state']
            row,status=state();assert status=='pending' and row['completed_tasks']==0 and not row['proof']
            db.execute("UPDATE history_task SET state='failed' WHERE org_id=:o AND id=:id",{'o':identity['org_id'],'id':tid})
            row,status=state();assert status=='failed' and row['completed_tasks']==0 and not row['proof']
            source=str(uuid4())
            db.execute("""INSERT INTO source_observation(id,org_id,provider,url,http_status,sha256,body,metadata,classification)
                VALUES (:id,:o,'PNCP_RESULTADOS',:url,200,:hash,'[]','{}'::jsonb,'official')""",
                {'id':source,'o':identity['org_id'],'url':'https://example.invalid/'+source,'hash':'a'*64})
            db.execute("UPDATE history_task SET state='done' WHERE org_id=:o AND id=:id",{'o':identity['org_id'],'id':tid})
            db.execute("""INSERT INTO history_page(org_id,collection_id,task_id,source_id,record_count,result)
                VALUES (:o,:collection,:task,:source,0,'{}'::jsonb)""",
                {'o':identity['org_id'],'collection':cid,'task':tid,'source':source})
            row,status=state();assert status=='consulted' and row['records_returned']==0 and len(row['proof'])==1
            other=str(uuid4())
            db.execute("""INSERT INTO history_task(org_id,collection_id,id,task_key,provider,arguments,state)
                VALUES (:o,:collection,:id,'result-2','PNCP_RESULTADOS',CAST(:args AS jsonb),'ready')""",
                {'o':identity['org_id'],'collection':cid,'id':other,'args':args})
            row,status=state();assert status=='partial' and row['completed_tasks']==1 and row['pending_tasks']==1
            db.execute("UPDATE history_task SET state='failed' WHERE org_id=:o AND id=:id",{'o':identity['org_id'],'id':other})
            row,status=state();assert status=='partial' and row['failed_tasks']==1
            error_source=str(uuid4())
            db.execute("""INSERT INTO source_observation(id,org_id,provider,url,http_status,sha256,body,metadata,classification)
                VALUES (:id,:o,'PNCP_RESULTADOS',:url,404,:hash,'{}','{}'::jsonb,'official')""",
                {'id':error_source,'o':identity['org_id'],'url':'https://example.invalid/'+error_source,'hash':'b'*64})
            db.execute("UPDATE history_task SET state='done' WHERE org_id=:o AND id=:id",{'o':identity['org_id'],'id':other})
            db.execute("""INSERT INTO history_page(org_id,collection_id,task_id,source_id,record_count,result)
                VALUES (:o,:collection,:task,:source,0,'{}'::jsonb)""",
                {'o':identity['org_id'],'collection':cid,'task':other,'source':error_source})
            row,status=state();assert status=='partial' and row['completed_tasks']==1 and row['pending_tasks']==1
            assert len(row['proof'])==1 and row['proof'][0]['task_id']==tid
            scoped={'completed_tasks':1,'status':'request_reconciled','failed_tasks':0,'planned_days':1}
            assert coverage_inventory.phase_state([scoped])=='scope_complete'
            assert coverage_inventory.phase_state([scoped],date(2031,2,1),date(2031,2,7))=='consulted'
        finally:
            transaction.rollback();engine.dispose()


def test_item_lines_cover_every_city_and_reject_old_revision(login):
    client=login('compras-a');created=scenario(client,30,2);calculation=calc(client,created)
    items=created['snapshot']['items'];cities=created['snapshot']['participants']
    for item in items:
        params=[('item_id',item['id']),('item_version',item['version'])]+[('municipalities',city) for city in cities]
        response=client.get('/api/v1/calculations/'+calculation['id']+'/item-lines',params=params)
        assert response.status_code==200,response.text
        rows=response.json()['records'];assert len(rows)==30
        assert {(row['ibge'],row['item_id'],row['item_version']) for row in rows}=={(city,item['id'],item['version']) for city in cities}
        later=client.get('/api/v1/calculations/'+calculation['id']+'/lines',params={'item_id':item['id'],'offset':20,'limit':20}).json()['records']
        assert later and all(any(row['ibge']==line['ibge'] and row['quantity']==line['quantity'] for row in rows) for line in later)
    narrowed=client.get('/api/v1/calculations/'+calculation['id']+'/item-lines',params=[('item_id',items[0]['id']),('item_version',items[0]['version']),('municipalities',cities[24])])
    assert [row['ibge'] for row in narrowed.json()['records']]==[cities[24]]
    assert login('compras-b').get('/api/v1/calculations/'+calculation['id']+'/item-lines',params=[('item_id',items[0]['id']),('item_version',items[0]['version']),('municipalities',cities[0])]).status_code==404
    updated=put(client,created,snapshot(created));assert updated.status_code==200
    old=client.get('/api/v1/calculations/'+calculation['id']+'/item-lines',params=[('item_id',items[0]['id']),('item_version',items[0]['version']),('municipalities',cities[0])])
    assert old.status_code==409
