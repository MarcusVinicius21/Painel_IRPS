"""Increment 02: exact sources, technical scope and immutable saved contexts."""
from uuid import uuid4
from datetime import date
from decimal import Decimal
import pytest
from sqlalchemy import create_engine
from app.db import DB,encoded
from app.config import load_settings
from app.history_filters import HistoryFilters
from app import catalogue
from test_history_contract import fixture_history, CITIES
from test_director_workflow import study_body

@pytest.fixture
def filtered(fixture_history):
    create,client,identity=fixture_history;pid,base_add,_=create('official')
    engine=create_engine(load_settings().owner_database_url.get_secret_value(),hide_parameters=True)
    def add(provider='PNCP_RESULTADOS',metadata=None,**kwargs):
        fid=base_add(**kwargs);sid=str(uuid4())
        with engine.begin() as conn:
            db=DB(conn);db.execute("SELECT set_config('irps.org_id',:o,true)",{'o':identity['org_id']})
            db.execute("INSERT INTO source_observation(id,org_id,provider,url,http_status,sha256,body,metadata,classification) VALUES (:i,:o,:p,:url,200,:hash,'[]','{}','official')",{'i':sid,'o':identity['org_id'],'p':provider,'url':'https://example.invalid/filters-test/'+sid,'hash':'a'*64})
            db.execute('UPDATE procurement_fact SET provider=:p,source_id=:s,metadata=CAST(:m AS jsonb) WHERE id=:i',{'p':provider,'s':sid,'m':encoded(metadata or {'synthetic_test_fixture':True}),'i':fid})
        return fid
    def get(provider=None,only=False,cities=CITIES,phase='homologado',start='2025-01-01',end='2025-12-31'):
        args=[('phase',phase),('start',start),('end',end),('only_comparable',str(only).lower())]+[('municipalities',c) for c in cities]
        if provider is not None:args.append(('provider',provider))
        response=client.get('/api/v1/director/history/'+pid,params=args);assert response.status_code==200,response.text
        return response.json()
    yield pid,add,get,client,identity
    engine.dispose()


def test_exact_provider_and_shared_comparison_predicate(filtered):
    pid,add,get,client,_=filtered
    good=add(quantity='3',amount='30');bad=add(quantity='999',amount='9990',unit='caixa de 20 resmas')
    other=add(provider='TESTE_IRPS_OUTRA_FONTE',quantity='5',amount='50')
    base=get();assert Decimal(base['summary']['observed_quantity'])==8 and base['summary']['observed_records']==3
    exact=get('PNCP_RESULTADOS');assert exact['summary']['observed_records']==2 and Decimal(exact['summary']['observed_quantity'])==3
    assert {e['provider'] for r in exact['municipalities'] for e in r['evidence']}=={'PNCP_RESULTADOS'}
    assert exact['scope']['filters']=={'provider':'PNCP_RESULTADOS','only_comparable':False}
    strict=get(only=True);assert strict['summary']['observed_records']==2 and Decimal(strict['summary']['observed_quantity'])==8
    assert strict['filter_exclusions'][0]['fact_id']==bad and strict['filter_exclusions'][0]['reasons']
    assert {e['fact_id'] for r in strict['municipalities'] for e in r['evidence']}=={good,other}
    assert {e['fact_id'] for r in base['municipalities'] for e in r['evidence']}=={good,bad,other}
    assert get('PNCP')['summary']['observed_quantity'] is None # No prefix matching.
    assert all(all(c['provider']=='PNCP_RESULTADOS' for c in r['coverage']) for r in exact['municipalities'])


def test_source_crosses_city_phase_date_and_superseded_revisions(filtered):
    _,add,get,_,_=filtered
    event=uuid4().hex;add(event=event,current=False,quantity='999');add(event=event,quantity='3')
    add(city=CITIES[1],quantity='4');add(phase='publicado_estimado',quantity='88');add(day='2024-01-01',quantity='77')
    assert Decimal(get('PNCP_RESULTADOS',cities=[CITIES[0]])['summary']['observed_quantity'])==3
    assert Decimal(get('PNCP_RESULTADOS',cities=[CITIES[1]])['summary']['observed_quantity'])==4
    assert Decimal(get('PNCP_RESULTADOS',phase='publicado_estimado')['summary']['observed_quantity'])==88
    assert Decimal(get('PNCP_RESULTADOS',start='2024-01-01',end='2024-12-31')['summary']['observed_quantity'])==77


def test_options_and_modality_unavailable_have_scope_proof(filtered,login):
    pid,add,get,client,_=filtered;add(metadata={'modality':6});add(provider='TESTE_IRPS_OUTRA_FONTE')
    args=[('phase','homologado'),('start','2025-01-01'),('end','2025-12-31'),('municipalities',CITIES[0])]
    response=client.get('/api/v1/director/history/'+pid+'/filters',params=args);assert response.status_code==200
    result=response.json();assert set(result['providers'])=={'PNCP_RESULTADOS','TESTE_IRPS_OUTRA_FONTE'}
    assert result['provider_field']=='procurement_fact.provider' and result['provider_matching']=='exact'
    assert not result['modality_available'] and result['modality_limitation']
    assert login('compras-b').get('/api/v1/director/history/'+pid+'/filters',params=args).status_code==404
    assert login('compras-b').get('/api/v1/director/history/'+pid,params=args).status_code==404
    for value in ('PNCP%','pncp',"PNCP' OR 1=1",'X'*81):
        assert client.get('/api/v1/director/history/'+pid,params=args+[('provider',value)]).status_code==422


@pytest.mark.parametrize('q,amount',[(None,None),('0','0')])
def test_source_empty_null_and_zero_are_distinct(filtered,q,amount):
    _,add,get,_,_=filtered;add(quantity=q,amount=amount)
    s=get('PNCP_RESULTADOS',only=True)['summary'];assert s['partial'] and not s['source_completeness_claimed']
    assert (s['observed_quantity'] is None if q is None else Decimal(s['observed_quantity'])==0)
    assert (s['documented_amount'] is None if amount is None else Decimal(s['documented_amount'])==0)
    missing=get('TESTE_SEM_REGISTROS');assert missing['summary']['observed_quantity'] is None
    assert all(r['observed_quantity'] is None and r['coverage_state']=='not_collected' for r in missing['municipalities'])


def test_study_and_progress_preserve_filters_without_editing_original(filtered):
    pid,add,get,client,_=filtered;add();add(provider='TESTE_IRPS_OUTRA_FONTE',quantity='9')
    initial=client.post('/api/v1/director/studies',json={**study_body(),'category':'material','unit':'caixa de 10 resmas','product_id':pid}).json()
    assert initial.get('id'),initial
    filters={'provider':'PNCP_RESULTADOS','only_comparable':True}
    selected=client.post('/api/v1/director/studies',json={**study_body(),'category':'material','unit':'caixa de 10 resmas','product_id':pid,'history_filters':filters})
    assert selected.status_code==201,selected.text
    saved=selected.json();assert saved['payload']['history_filters']==filters
    assert saved['payload']['history']['scope']['filters']==filters
    assert Decimal(saved['payload']['history']['summary']['observed_quantity'])==3
    assert client.get('/api/v1/director/studies/'+initial['id']).json()['payload']==initial['payload']
    progress=client.post('/api/v1/director/progress',json={'product_id':pid,'municipalities':[CITIES[0]],'start':'2025-01-01','end':'2025-12-31','phase':'homologado','stage':'historico','form':{'name':'Rascunho fictício'},'history_filters':filters})
    assert progress.status_code==201,progress.text
    assert client.get('/api/v1/director/progress/'+progress.json()['id']).json()['payload']['history_filters']==filters


def test_provider_filter_precedes_limit(filtered):
    pid,add,get,client,identity=filtered;fid=add(quantity='3')
    from app import sources
    from fastapi import HTTPException
    engine=create_engine(load_settings().owner_database_url.get_secret_value(),hide_parameters=True)
    with engine.connect() as conn:
        transaction=conn.begin()
        try:
            db=DB(conn);db.execute("SELECT set_config('irps.org_id',:o,true)",{'o':identity['org_id']})
            row=db.one('SELECT * FROM procurement_fact WHERE id=:i',{'i':fid});prefix=uuid4().hex
            db.execute("""INSERT INTO procurement_fact(id,org_id,classification,provider,event_identity,revision_hash,source_id,buyer_id,municipality_ibge,item_id,item_version,description,unit,quantity,amount,phase,event_date,obligation_id,metadata)
                SELECT gen_random_uuid(),:o,'official','TESTE_IRPS_OUTRA_FONTE',:prefix||n::text,:prefix||n::text,:source,:buyer,:city,:item,1,'Papel caixa com 10 resmas','caixa de 10 resmas',1,10,'homologado','2025-12-05',:process,'{}' FROM generate_series(1,20001) n""",{'o':identity['org_id'],'prefix':prefix,'source':row['source_id'],'buyer':row['buyer_id'],'city':row['municipality_ibge'],'item':row['item_id'],'process':row['obligation_id']})
            ctx=sources.job_context(db,identity['org_id'],identity['actor_id'])
            result=catalogue.product_history(ctx,pid,'homologado',date(2025,1,1),date(2025,12,31),[CITIES[0]],HistoryFilters(provider='PNCP_RESULTADOS'))
            assert result['summary']['observed_records']==1
            with pytest.raises(HTTPException) as error:
                catalogue.product_history(ctx,pid,'homologado',date(2025,1,1),date(2025,12,31),[CITIES[0]])
            assert error.value.status_code==422 and error.value.detail['code']=='CATALOGUE_LIMIT'
        finally:
            transaction.rollback()
    engine.dispose()


def test_classification_is_not_widened_by_provider_filters(filtered,fixture_history):
    _,add,get,client,_=filtered
    add(quantity='3');add(quantity='999',d='synthetic')
    assert get('PNCP_RESULTADOS')['summary']['observed_records']==1
    assert Decimal(get('PNCP_RESULTADOS')['summary']['observed_quantity'])==3
    create,_,identity=fixture_history;pid,base_add,_=create('synthetic');base_add(quantity='7')
    args=[('phase','homologado'),('start','2025-01-01'),('end','2025-12-31'),('municipalities',CITIES[0]),('provider','PNCP_RESULTADOS')]
    assert client.get('/api/v1/director/history/'+pid,params=args).status_code==422
    from app import sources
    engine=create_engine(load_settings().owner_database_url.get_secret_value(),hide_parameters=True)
    with engine.begin() as conn:
        db=DB(conn);db.execute("SELECT set_config('irps.org_id',:o,true)",{'o':identity['org_id']})
        ctx=sources.job_context(db,identity['org_id'],identity['actor_id'])
        result=catalogue.product_history(ctx,pid,'homologado',date(2025,1,1),date(2025,12,31),[CITIES[0]],HistoryFilters(provider='PNCP_RESULTADOS',only_comparable=True))
        assert result['summary']['classification']=='synthetic' and Decimal(result['summary']['observed_quantity'])==7
    engine.dispose()
