"""Increment 01: generated fixtures only, in the explicitly isolated PostgreSQL DB."""
from datetime import date
from decimal import Decimal
from uuid import uuid4
import pytest
from sqlalchemy import create_engine
from app import catalogue, sources
from app.db import DB, encoded
from app.config import load_settings
from test_director_workflow import make_study

START=date(2025,1,1);END=date(2025,12,31)
CITIES=['3131307','3101607','3100500']

@pytest.fixture
def fixture_history(login):
    client=login();identity=client.get('/api/v1/auth/context').json()
    engine=create_engine(load_settings().owner_database_url.get_secret_value(),hide_parameters=True)
    def create(dataset='synthetic'):
        item='contract-'+uuid4().hex;pid=str(uuid4());sid=str(uuid4())
        with engine.begin() as conn:
            db=DB(conn);db.execute("SELECT set_config('irps.org_id',:o,true)",{'o':identity['org_id']})
            db.execute("INSERT INTO item_version(id,version,name,family,unit,step,classification) VALUES (:i,1,'Papel de teste caixa com 10 resmas','Material','caixa de 10 resmas',1,:d)",{'i':item,'d':dataset})
            db.execute("INSERT INTO source_observation(id,org_id,provider,url,http_status,sha256,body,metadata,classification) VALUES (:i,:o,'PNCP_RESULTADOS',:url,200,:sha,'[]',:meta,:d)",{'i':sid,'o':identity['org_id'],'url':'https://example.invalid/test-only/'+sid,'sha':'a'*64,'meta':encoded({'synthetic_test_fixture':True}),'d':dataset})
            db.execute("""INSERT INTO canonical_product(org_id,id,name,category,classification,unit_key,package_signature,members,justification,evidence,reviewed_by)
                VALUES (:o,:i,'Produto fictício para teste do contrato','Material',:d,'CAIXA','CAIXA:10:RESMA',CAST(:members AS jsonb),'Teste técnico local','Dados gerados no banco isolado',:a)""",{'o':identity['org_id'],'i':pid,'d':dataset,'members':encoded([{'id':item,'version':1}]),'a':identity['actor_id']})
        def add(city=CITIES[0],quantity='3',amount='30',unit='caixa de 10 resmas',phase='homologado',current=True,event=None,process='00000000000001-1-42/2025',day='2025-12-05',source=None,**updates):
            fid=str(uuid4());event=event or uuid4().hex
            with engine.begin() as conn:
                db=DB(conn);db.execute("SELECT set_config('irps.org_id',:o,true)",{'o':identity['org_id']})
                buyer=db.one("SELECT id FROM buyer WHERE municipality_ibge=:city LIMIT 1",{'city':city})
                if not buyer:
                    bid=str(uuid4());db.execute("INSERT INTO buyer(id,org_id,name,municipality_ibge,government_level,classification) VALUES (:i,:o,'Órgão fictício do teste',:c,'municipal',:d)",{'i':bid,'o':identity['org_id'],'c':city,'d':dataset})
                else:bid=buyer['id']
                db.execute("""INSERT INTO procurement_fact(id,org_id,classification,provider,event_identity,revision_hash,source_id,buyer_id,municipality_ibge,item_id,item_version,description,unit,quantity,amount,phase,event_date,obligation_id,metadata,is_current)
                    VALUES (:i,:o,:d,'PNCP_RESULTADOS',:e,:hash,:source,:buyer,:c,:item,1,'Papel de teste caixa com 10 resmas',:u,:q,:amount,:phase,:day,:process,'{}',:current)""",{'i':fid,'o':identity['org_id'],'d':dataset,'e':event,'hash':uuid4().hex,'source':source or sid,'buyer':bid,'c':city,'item':item,'u':unit,'q':quantity,'amount':amount,'phase':phase,'day':day,'process':process,'current':current,**updates})
            return fid
        def get(cities=CITIES,phase='homologado',director=False):
            path=f'/api/v1/director/history/{pid}' if director else f'/api/v1/catalogue-intelligent/products/{pid}/history'
            response=client.get(path,params=[('phase',phase),('start',START.isoformat()),('end',END.isoformat())]+[('municipalities',c) for c in cities])
            assert response.status_code==200,response.text
            return response.json()
        return pid,add,get
    yield create,client,identity
    engine.dispose()


def test_summary_unique_process_across_cities_and_lines(fixture_history):
    create,_,_=fixture_history;_,add,get=create()
    ids=[add(quantity='2',amount='20'),add(quantity='3',amount='30'),add(city=CITIES[1],quantity='4',amount='40')]
    result=get();s=result['summary']
    assert result['contract_version']==2
    assert s['observed_records']==3 and s['municipalities_with_records']==2
    assert s['distinct_processes']==1 # Not the sum of municipal process counts (2).
    assert Decimal(s['observed_quantity'])==9 and Decimal(s['documented_amount'])==90
    assert s['unit']=='CAIXA' and s['phase']=='homologado' and s['classification']=='synthetic'
    assert s['partial'] and not s['source_completeness_claimed']
    assert set(result['temporal_windows'][-1]['fact_ids'])==set(ids)
    assert Decimal(get([CITIES[1]])['summary']['observed_quantity'])==4

@pytest.mark.parametrize('quantity,amount',[(None,'30'),('3',None),(None,None)])
def test_missing_numbers_remain_null(fixture_history,quantity,amount):
    create,_,_=fixture_history;_,add,get=create('official');add(quantity=quantity,amount=amount)
    s=get()['summary']
    assert (s['observed_quantity'] is None if quantity is None else Decimal(s['observed_quantity'])==Decimal(quantity))
    assert (s['documented_amount'] is None if amount is None else Decimal(s['documented_amount'])==Decimal(amount))
    assert s['quantity_complete']==(quantity is not None)
    assert s['amount_complete']==(amount is not None)


def test_no_facts_is_not_zero_demand(fixture_history):
    create,_,_=fixture_history;_,_,get=create('official');result=get(director=True);s=result['summary']
    assert s['observed_records']==0 and s['distinct_processes'] is None
    assert s['observed_quantity'] is s['documented_amount'] is None
    assert all(w['observed_quantity'] is None for w in result['temporal_windows'])
    assert all(r['observed_quantity'] is None for r in result['municipalities'])

@pytest.mark.parametrize('unit',['caixa de 20 resmas','kg','unidade'])
def test_incompatible_unit_or_pack_excluded(fixture_history,unit):
    create,_,_=fixture_history;_,add,get=create();add();add(unit=unit,quantity='999',amount='9999')
    result=get();s=result['summary']
    assert s['observed_records']==2 and s['comparable_records']==1 and s['excluded_records']==1
    assert Decimal(s['observed_quantity'])==3 and Decimal(s['documented_amount'])==30
    assert not s['quantity_complete'] and not s['amount_complete']
    assert sum(len(r['excluded_from_totals']) for r in result['municipalities'])==1


def test_revisions_phase_version_and_date_do_not_leak(fixture_history):
    create,_,_=fixture_history;_,add,get=create();event=uuid4().hex
    add(current=False,event=event,quantity='999');add(event=event,quantity='3')
    add(phase='publicado_estimado',quantity='888');add(day='2024-01-01',quantity='777')
    result=get();assert result['summary']['observed_records']==1
    assert Decimal(result['summary']['observed_quantity'])==3
    assert Decimal(get(phase='publicado_estimado')['summary']['observed_quantity'])==888


def test_partial_missing_and_unidentifiable_processes(fixture_history):
    create,_,_=fixture_history;_,add,get=create('official');add(process='unidentified',quantity=None);add(process='unidentified',quantity='0',amount='0')
    result=get();s=result['summary']
    assert Decimal(s['observed_quantity'])==0 and not s['quantity_complete']
    assert s['distinct_processes'] is None and not s['process_identity_complete']
    assert s['partial'] and all(w['monthly_average'] is None and w['recurrence_percentage'] is None for w in result['temporal_windows'])


def test_director_endpoint_official_contract_and_org_isolation(fixture_history,login):
    create,client,_=fixture_history;pid,add,get=create('official');add()
    result=get(director=True);assert Decimal(result['summary']['observed_quantity'])==3
    assert result['summary']['classification']=='official'
    params=[('phase','homologado'),('start','2025-01-01'),('end','2025-12-31'),('municipalities',CITIES[0])]
    assert login('compras-b').get('/api/v1/director/history/'+pid,params=params).status_code==404
    synthetic,_,_=create()
    assert client.get('/api/v1/director/history/'+synthetic,params=params).status_code==422


def test_legacy_snapshot_is_preserved_without_live_recalculation(login,settings):
    client=login();identity=client.get('/api/v1/auth/context').json();created=make_study(client)
    engine=create_engine(settings.owner_database_url.get_secret_value(),hide_parameters=True)
    legacy={'product':{'unit':'UNIDADE'},'municipalities':[],'source_completeness_claimed':False}
    payload={**created['payload'],'history':legacy};sid=str(uuid4())
    with engine.begin() as conn:
        db=DB(conn);db.execute("SELECT set_config('irps.org_id',:o,true)",{'o':identity['org_id']})
        db.execute("""INSERT INTO director_study(org_id,id,scenario_id,scenario_revision,payload,context_sha256,created_by)
            VALUES (:o,:i,:s,1,CAST(:p AS jsonb),:h,:a)""",{'o':identity['org_id'],'i':sid,'s':created['scenario']['id'],'p':encoded(payload),'h':'a'*64,'a':identity['actor_id']})
    engine.dispose()
    for _ in range(2):
        response=client.get('/api/v1/director/studies/'+sid);assert response.status_code==200
        assert response.json()['payload']==payload and response.json()['context_sha256']=='a'*64


def test_summary_uses_full_facts_not_capped_evidence(fixture_history):
    create,_,_=fixture_history;_,add,get=create()
    for _ in range(102):add(quantity='1',amount='1')
    r=get([CITIES[0]])
    assert len(r['municipalities'][0]['evidence'])==100 and r['municipalities'][0]['evidence_truncated']
    assert Decimal(r['summary']['observed_quantity'])==102 and len(r['temporal_windows'][-1]['fact_ids'])==102
