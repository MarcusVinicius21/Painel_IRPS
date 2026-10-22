"""I03_06: immutable historical analyses in isolated PostgreSQL only."""
from decimal import Decimal
from datetime import date
import pytest
from sqlalchemy import create_engine,text
from sqlalchemy.exc import DBAPIError
from app.config import load_settings
from app.director_progress import history_digest
from test_history_contract import fixture_history
from test_director_workflow import national


def body(pid,h,**updates):
    return {'product_id':pid,'municipalities':['3131307','3101607','3100500'],'phase':'homologado','start':'2025-01-01','end':'2025-12-31','expected_history_sha256':h.get('snapshot_sha256'),
        'history_filters':{'provider':None,'only_comparable':False},'stage':'historico','form':{'name':'Análise fictícia para teste isolado','specification':'Papel de teste caixa com 10 resmas','unit':'caixa de 10 resmas','classification':'synthetic','preliminary_target':'999','technical_evidence':'Não transformar em cálculo'},**updates}


def test_analysis_snapshot_immutable_after_new_facts_and_no_scenario(fixture_history):
    create,c,identity=fixture_history;pid,add,get=create('official');add();h=get(director=True)
    engine=create_engine(load_settings().owner_database_url.get_secret_value(),hide_parameters=True)
    with engine.connect() as conn: before=conn.execute(text('SELECT count(*) FROM scenario')).scalar()
    r=c.post('/api/v1/director/analyses',json=body(pid,h));assert r.status_code==201,r.text
    saved=r.json();p=saved['payload'];assert p['purpose']=='historical_analysis'
    assert p['history_sha256']==h['snapshot_sha256'];assert Decimal(p['history']['summary']['observed_quantity'])==3
    assert p['form']['preliminary_target']=='' and p['technical_confirmed'] is False
    assert p['v4_input_created'] is False and p['confirmation_created'] is False
    assert any(row['evidence'] for row in p['history']['municipalities'])
    add(quantity='4',amount='40');assert Decimal(get(director=True)['summary']['observed_quantity'])==7
    old=c.get('/api/v1/director/progress/'+saved['id']).json();assert old['payload']==p
    with engine.connect() as conn: assert conn.execute(text('SELECT count(*) FROM scenario')).scalar()==before
    engine.dispose()


def test_changed_history_conflicts_and_new_version_preserves_old(fixture_history):
    create,c,_=fixture_history;pid,add,get=create('official');add();h=get(director=True)
    a=c.post('/api/v1/director/analyses',json=body(pid,h));assert a.status_code==201
    add(quantity='2');r=c.post('/api/v1/director/analyses',json=body(pid,h));assert r.status_code==409
    latest=get(director=True);b=c.post('/api/v1/director/analyses',json=body(pid,latest,supersedes_id=a.json()['id']));assert b.status_code==201,b.text
    assert b.json()['id']!=a.json()['id'];assert c.get('/api/v1/director/progress/'+a.json()['id']).json()['payload']==a.json()['payload']
    assert c.post('/api/v1/director/analyses',json=body(pid,latest,supersedes_id=a.json()['id'])).status_code==409


def test_reopen_saved_source_keeps_scope_and_rejects_context_change(fixture_history):
    create,c,_=fixture_history;pid,add,get=create('official');add();h=get(director=True)
    a=c.post('/api/v1/director/analyses',json=body(pid,h)).json();add(quantity='20')
    r=c.post('/api/v1/director/analyses',json=body(pid,h,source_progress_id=a['id'],expected_history_sha256=None));assert r.status_code==201,r.text
    assert r.json()['payload']['history']==a['payload']['history']
    assert c.post('/api/v1/director/analyses',json=body(pid,h,source_progress_id=a['id'],phase='contratado')).status_code==409


def test_analysis_unknown_numbers_and_no_data(fixture_history):
    create,c,_=fixture_history;pid,add,get=create('official');add(quantity=None,amount=None);h=get(director=True)
    r=c.post('/api/v1/director/analyses',json=body(pid,h));assert r.status_code==201
    assert r.json()['payload']['history']['summary']['observed_quantity'] is None
    assert r.json()['payload']['history']['summary']['documented_amount'] is None
    empty,_,emptyget=create('official');assert c.post('/api/v1/director/analyses',json=body(empty,emptyget(director=True))).status_code==422


def test_analysis_isolation_permissions_and_rls(fixture_history,login):
    create,c,identity=fixture_history;pid,add,get=create('official');add();h=get(director=True)
    a=c.post('/api/v1/director/analyses',json=body(pid,h)).json();other=login('compras-b');otherid=other.get('/api/v1/auth/context').json()
    assert other.get('/api/v1/director/progress/'+a['id']).status_code==404
    assert other.post('/api/v1/director/analyses',json=body(pid,h,source_progress_id=a['id'])).status_code==404
    assert login('consulta-a').post('/api/v1/director/analyses',json=body(pid,h)).status_code==403
    engine=create_engine(load_settings().owner_database_url.get_secret_value(),hide_parameters=True)
    with engine.begin() as conn:
        conn.exec_driver_sql('SET LOCAL ROLE irps_app');conn.execute(text("SELECT set_config('irps.org_id',:o,true)"),{'o':otherid['org_id']})
        assert conn.execute(text('SELECT count(*) FROM director_progress WHERE id=:i'),{'i':a['id']}).scalar()==0
    with pytest.raises(DBAPIError):
        with engine.begin() as conn:
            conn.execute(text("UPDATE director_progress SET payload='{}'::jsonb WHERE id=:i"),{'i':a['id']})
    assert c.get('/api/v1/director/progress/'+a['id']).json()['payload']==a['payload'];engine.dispose()


def test_analysis_rejects_invalid_scope_and_client_history(fixture_history):
    create,c,_=fixture_history;pid,add,get=create('official');add();h=get(director=True)
    for changes in [{'phase':'inexistente'},{'end':'2099-01-01'},{'start':'2026-01-01'},{'municipalities':['9999999']},{'history':{'summary':{'observed_quantity':999}}}]:
        assert c.post('/api/v1/director/analyses',json=body(pid,h,**changes)).status_code==422


def test_analysis_rejects_unreviewed_catalogue_link(fixture_history,national):
    create,c,_=fixture_history;pid,add,get=create('official');add();h=get(director=True)
    snapshot,_,prefix=national
    response=c.post('/api/v1/director/analyses',json=body(pid,h,snapshot_id=snapshot['snapshot_id'],code=prefix+'0'))
    assert response.status_code==422
    assert response.json()['detail']['code']=='CATALOGUE_LINK_REQUIRED'
