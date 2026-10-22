"""I05_03 uses real PostgreSQL, immutable single-item studies and unchanged V4."""
from uuid import uuid4
from decimal import Decimal
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
import pytest
from sqlalchemy import create_engine,text
from sqlalchemy.exc import DBAPIError
from app.security import stable_id
from test_director_workflow import make_study,national

BASE='/api/v1/director/multi-studies'


def sources(c,n=3,**kw):
    return [make_study(c,name=f'Item sintético {i} '+uuid4().hex,unit=['unidade','litro','caixa de 10 resmas'][i%3],
        preliminary_target=str((i+1)*10),**kw) for i in range(n)]


def scenario(c,items):
    r=c.post('/api/v1/scenarios',json={'title':'Cenário multiitem sintético','classification':items[0]['payload']['classification'],
        'snapshot':{'period':'2027 planejado','mode':'A','participants':items[0]['payload']['municipalities'],
        'items':[s['payload']['planning_item'] for s in items]}})
    assert r.status_code==201,r.text
    return r.json()


def body(s,items,**kw):
    return dict(contract_version=1,request_id=str(uuid4()),name='Estudo com itens sintéticos',scenario_id=s['id'],
        scenario_revision=s['current_revision'],source_studies=[i['id'] for i in items],justification='Vínculo sintético para testar persistência e revisão.',**kw)


@pytest.mark.parametrize('n',[1,3])
def test_create_read_and_retry_preserve_legacy_and_scenario(login,n):
    c=login();items=sources(c,n);sc=scenario(c,items);url='/api/v1/scenarios/'+sc['id']
    before=c.get(url).json();legacy=[c.get('/api/v1/director/studies/'+s['id']).json() for s in items]
    request=body(sc,items);a=c.post(BASE,json=request);assert a.status_code==201,a.text
    saved=a.json();assert saved['contract_version']==1 and saved['revision']==1 and saved['context_current']
    assert len(saved['payload']['items'])==n and saved['payload']['cross_item_quantity_total'] is None
    assert [i['preliminary_target'] for i in saved['payload']['items']]==[str((i+1)*10) for i in range(n)]
    assert [i['unit'] for i in saved['payload']['items']]==[i['payload']['unit'] for i in items]
    assert c.get(BASE+'/'+saved['id']).json()==saved
    assert c.post(BASE,json=request).json()==saved
    assert c.get(url).json()==before
    assert [c.get('/api/v1/director/studies/'+s['id']).json() for s in items]==legacy
    assert all(c.get('/api/v1/director/studies/'+s['id']+'/register').json()['confirmed_known_total'] is None for s in items)
    assert c.post(BASE,json={**request,'name':'Outro pedido incompatível'}).status_code==409
    assert c.post(BASE,json={**request,'contract_version':2}).status_code==422


def test_revise_remove_and_preserve_all_snapshots(login):
    c=login();items=sources(c);sc=scenario(c,items);initial_request=body(sc,items);first=c.post(BASE,json=initial_request).json();url=BASE+'/'+first['id']
    # Editing V4 remains an explicit operation of the existing scenario API.
    snap=deepcopy(sc['snapshot']);snap['items']=snap['items'][:2]
    sc2=c.put('/api/v1/scenarios/'+sc['id'],headers={'If-Match':'1'},json=snap).json()
    assert c.get(url).json()['context_current'] is False
    req=body(sc2,items[:2],expected_revision=1)
    result=c.post(url+'/revisions',json=req);assert result.status_code==201,result.text
    second=result.json();assert second['revision']==2 and second['previous_revision']==1
    assert len(second['payload']['items'])==2 and second['context_current']
    assert second['context_sha256']!=first['context_sha256']
    assert c.get(url,params={'revision':1}).json()['payload']==first['payload']
    assert c.post(url+'/revisions',json=req).json()==second
    stale={**req,'request_id':str(uuid4())};assert c.post(url+'/revisions',json=stale).status_code==409
    assert c.get('/api/v1/director/studies/'+items[2]['id']).status_code==200
    assert c.get('/api/v1/scenarios/'+sc['id']).json()['snapshot']==sc2['snapshot']
    # Retry of the original create still resolves to its original revision, never revision 2.
    replay=c.post(BASE,json=initial_request).json();assert replay['revision']==1 and replay['payload']==first['payload']
    assert not replay['context_current']
    assert c.get(url,params={'revision':99}).status_code==404


def test_replace_technical_definition_and_exact_version_matching(login,national,settings,tmp_path):
    c=login();catalogue,_,prefix=national
    a=make_study(c,snapshot_id=catalogue['snapshot_id'],code=prefix+'0')
    sc=scenario(c,[a]);created=c.post(BASE,json=body(sc,[a]));assert created.status_code==201,created.text
    first=created.json();binding=first['payload']['items'][0]
    assert binding['catalogue_binding']=={'snapshot_id':catalogue['snapshot_id'],'code':prefix+'0'}
    old=deepcopy(first['payload'])
    from app.national_catalogue import import_csv
    changed_catalogue=tmp_path/'snapshot2.csv'
    changed_catalogue.write_text('codigoItem;descricaoItem;statusItem\n'+prefix+'0;Nova descrição sintética do mesmo código;True\n',encoding='utf-8')
    new_catalogue=import_csv(settings.owner_database_url.get_secret_value(),changed_catalogue,'CATMAT')
    b=make_study(c,snapshot_id=new_catalogue['snapshot_id'],code=prefix+'0',unit='litro',specification='Nova especificação técnica sintética documentada.')
    snap=deepcopy(sc['snapshot']);snap['items']=[b['payload']['planning_item']]
    sc2=c.put('/api/v1/scenarios/'+sc['id'],headers={'If-Match':'1'},json=snap).json()
    wrong=c.post(BASE+'/'+first['id']+'/revisions',json=body(sc2,[a],expected_revision=1))
    assert wrong.status_code==422 and wrong.json()['detail']['code']=='ITEM_BINDING_MISMATCH'
    updated=c.post(BASE+'/'+first['id']+'/revisions',json=body(sc2,[b],expected_revision=1));assert updated.status_code==201,updated.text
    assert updated.json()['payload']['items'][0]['catalogue_binding']=={'snapshot_id':new_catalogue['snapshot_id'],'code':prefix+'0'}
    assert updated.json()['payload']['items'][0]['unit']=='litro'
    assert c.get(BASE+'/'+first['id'],params={'revision':1}).json()['payload']==old
    assert c.get('/api/v1/director/studies/'+a['id']).json()['payload']['unit']=='unidade'


def test_incompatible_sources_duplicates_and_classification_are_explicit(login):
    c=login();items=sources(c,2);sc=scenario(c,items)
    for patch,code in [({'source_studies':[items[0]['id']]},'ITEM_BINDING_MISMATCH'),
                       ({'scenario_revision':99},'VERSION_CONFLICT')]:
        req=body(sc,items);r=c.post(BASE,json={**req,**patch});assert r.status_code in (409,422) and r.json()['detail']['code']==code
    req=body(sc,items);assert c.post(BASE,json={**req,'source_studies':[items[0]['id'],items[0]['id']]}).status_code==422
    other=make_study(c,municipalities=['3131307']);target=scenario(c,[other])
    mismatch=body(target,[items[0]])
    assert c.post(BASE,json=mismatch).json()['detail']['code']=='PARTICIPANT_SCOPE_MISMATCH'
    internal=make_study(c,classification='internal');target=scenario(c,[internal])
    assert c.post(BASE,json=body(target,[items[0]])).json()['detail']['code']=='DATASET_MISMATCH'
    # A source definition is immutable; a later source scenario revision makes its context stale.
    src=items[0];srcsc=c.get('/api/v1/scenarios/'+src['scenario']['id']).json()
    assert c.put('/api/v1/scenarios/'+srcsc['id'],headers={'If-Match':'1'},json={**srcsc['snapshot'],'period':'2028 alterado'}).status_code==200
    assert c.post(BASE,json=body(sc,items)).json()['detail']['code']=='SOURCE_CONTEXT_STALE'


def test_null_target_and_different_units_never_become_total(login):
    c=login();a=make_study(c,preliminary_target=None,target_justification='');b=make_study(c,name='Serviço técnico sintético em litros',unit='litro')
    sc=scenario(c,[a,b]);r=c.post(BASE,json=body(sc,[a,b]));assert r.status_code==201,r.text
    data=r.json();assert data['payload']['items'][0]['preliminary_target'] is None
    assert data['payload']['cross_item_quantity_total'] is None
    assert c.get('/api/v1/scenarios/'+sc['id']).json()['snapshot']['inputs']=={}


def test_permissions_rls_and_immutable_storage(login,app,settings):
    a=login();items=sources(a,1);sc=scenario(a,items);request=body(sc,items)
    assert login('consulta-a').post(BASE,json=request).status_code==403
    saved=a.post(BASE,json=request).json();other=login('compras-b')
    assert other.get(BASE+'/'+saved['id']).status_code==404
    assert other.post(BASE+'/'+saved['id']+'/revisions',json={**request,'request_id':str(uuid4()),'expected_revision':1}).status_code==404
    assert other.post(BASE,json={**request,'request_id':str(uuid4())}).status_code==404
    assert login('consulta-a').get(BASE+'/'+saved['id']).status_code==200
    with app.state.database.transaction(stable_id('org:compras-b')) as db:
        assert not db.all('SELECT * FROM director_multi_study_version WHERE id=:i',{'i':saved['id']})
        assert not db.all('SELECT * FROM director_multi_study_item WHERE study_id=:i',{'i':saved['id']})
        role=db.one('SELECT rolsuper,rolbypassrls FROM pg_roles WHERE rolname=current_user');assert not role['rolsuper'] and not role['rolbypassrls']
    owner=create_engine(settings.owner_database_url.get_secret_value(),hide_parameters=True)
    for table,key in [('director_multi_study_version','id'),('director_multi_study_item','study_id')]:
        with pytest.raises(DBAPIError):
            with owner.begin() as conn:conn.execute(text(f'DELETE FROM {table} WHERE {key}=:i'),{'i':saved['id']})
    owner.dispose()
    assert a.get(BASE+'/'+saved['id']).json()==saved
    audit=a.get('/api/v1/audit').json()['records'];assert any(r['action']=='director.multi_study_version_created' and r['resource_id']==saved['id'] for r in audit)


def test_concurrent_idempotent_create_produces_one_version(login,app):
    a=login();b=login();items=sources(a,2);sc=scenario(a,items);request=body(sc,items)
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lambda client:client.post(BASE,json=request),[a,b]))
    assert all(r.status_code==201 for r in results),[r.text for r in results]
    assert results[0].json()['id']==results[1].json()['id']
    with app.state.database.transaction(stable_id('org:compras-a')) as db:
        assert db.one('SELECT count(*) AS n FROM director_multi_study_version WHERE request_id=:q',{'q':request['request_id']})['n']==1


def test_existing_multi_item_v4_remains_auditable_without_cross_unit_total(login):
    c=login();items=sources(c,3);sc=scenario(c,items);snap=deepcopy(sc['snapshot'])
    snap['inputs']={city+'|'+item['payload']['planning_item']['id']:{'driver_count':'10','units_per_driver':'2',
        'driver_source':'Base sintética verificada no teste.','rate_source':'Taxa sintética para testar o núcleo.',
        'available_stock':'0','confirmed_incoming':'0'} for city in snap['participants'] for item in items}
    update=c.put('/api/v1/scenarios/'+sc['id'],headers={'If-Match':'1'},json=snap);assert update.status_code==200
    sc=update.json();saved=c.post(BASE,json=body(sc,items));assert saved.status_code==201,saved.text
    result=c.post('/api/v1/scenarios/'+sc['id']+'/calculate');assert result.status_code==200,result.text
    summary=result.json()['summary'];assert summary['lines']==6
    assert len(summary['item_totals'])==3 and all(Decimal(r['quantity'])==Decimal('40') for r in summary['item_totals'])
    assert saved.json()['payload']['cross_item_quantity_total'] is None
    assert c.get('/api/v1/scenarios/'+sc['id']).json()['snapshot']==sc['snapshot']


def test_exact_planning_item_version_and_failed_write_are_not_silently_rebound(login,app):
    c=login();items=sources(c,1);sc=scenario(c,items);ref=items[0]['payload']['planning_item']
    with app.state.database.transaction(stable_id('org:compras-a')) as db:
        db.execute('''INSERT INTO item_version(id,version,name,family,unit,step,classification,org_id)
            SELECT id,2,name,family,unit,step,classification,org_id FROM item_version WHERE id=:i AND version=1''',{'i':ref['id']})
    snap=deepcopy(sc['snapshot']);snap['items']=[{'id':ref['id'],'version':2}]
    update=c.put('/api/v1/scenarios/'+sc['id'],headers={'If-Match':'1'},json=snap);assert update.status_code==200
    request=body(update.json(),items);response=c.post(BASE,json=request)
    assert response.status_code==422 and response.json()['detail']['code']=='ITEM_BINDING_MISMATCH'
    with app.state.database.transaction(stable_id('org:compras-a')) as db:
        assert db.one('SELECT count(*) AS n FROM director_multi_study_version WHERE request_id=:q',{'q':request['request_id']})['n']==0
