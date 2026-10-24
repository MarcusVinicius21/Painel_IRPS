import hashlib
from uuid import uuid4
import pytest
from app.db import encoded


@pytest.fixture
def data(app,login):
    assert app.state.settings.auth_mode=='local_test'
    c=login();identity=c.get('/api/v1/auth/context').json();org=identity['org_id'];actor=identity['actor_id']
    prefix='qa-indicator-'+uuid4().hex;provider='QA_'+uuid4().hex.upper()
    item=prefix+'-item';source=str(uuid4());buyer=str(uuid4())
    with app.state.database.transaction(org,actor) as db:
        body=encoded({'fixture_only':True,'synthetic_evidence_in_isolated_test_database':True})
        db.execute("""INSERT INTO source_observation(id,org_id,provider,url,http_status,sha256,body,metadata,classification)
            VALUES (:id,:o,:p,'https://example.invalid/isolated-indicators-qa',200,:h,:b,CAST(:meta AS jsonb),'official')""",
            {'id':source,'o':org,'p':provider,'h':hashlib.sha256(body.encode()).hexdigest(),'b':body,'meta':encoded({'fixture_only':True})})
        db.execute("""INSERT INTO buyer(id,org_id,cnpj,name,municipality_ibge,government_level,classification,external_identity)
            VALUES (:i,:o,'00000000000001','QA isolated municipal buyer','3131307','M','official',:e)""",
            {'i':buyer,'o':org,'e':prefix})
        name='Papel A4 caixa com 10 resmas';unit='caixa com 10 resmas'
        for version in (1,2):
            db.execute("""INSERT INTO item_version(id,version,name,family,unit,step,classification)
                VALUES (:i,:v,:name,'QA',:unit,1,'synthetic')""",
                {'i':item,'v':version,'name':name,'unit':unit})
        for index in range(28):
            phase='contratado' if index==5 else 'homologado'
            version=2 if index==3 else 1
            u='kg' if index==4 else unit
            amount=None if index in (1,2) else '10'
            quantity=None if index==2 else '2'
            currency='foreign_or_unknown' if index==6 else 'BRL'
            description=name if index<7 else name+' QA variante '+str(index)
            db.execute("""INSERT INTO procurement_fact(id,org_id,classification,provider,event_identity,revision_hash,
                source_id,buyer_id,municipality_ibge,item_id,item_version,description,unit,quantity,amount,phase,
                event_date,obligation_id,metadata) VALUES (:id,:o,'official',:p,:event,:hash,:s,:b,'3131307',
                :item,:version,:description,:unit,:qty,:amount,:phase,'2026-09-01',:event,CAST(:meta AS jsonb))""",
                {'id':str(uuid4()),'o':org,'p':provider,'event':prefix+':'+str(index),'hash':str(index),
                    's':source,'b':buyer,'item':item,'version':version,'description':description,'unit':u,
                    'qty':quantity,'amount':amount,'phase':phase,
                    'meta':encoded({'record_level':'item','currency':currency,'fixture_only':True})})
        # Superseded copy must not change the current aggregate.
        db.execute("""INSERT INTO procurement_fact(id,org_id,classification,provider,event_identity,revision_hash,
            is_current,source_id,buyer_id,municipality_ibge,item_id,item_version,description,unit,quantity,amount,phase,
            event_date,obligation_id,metadata) VALUES (:id,:o,'official',:p,:event,'old',false,:s,:b,'3131307',
            :item,1,:description,:unit,999,999,'homologado','2026-09-01',:event,CAST(:meta AS jsonb))""",
            {'id':str(uuid4()),'o':org,'p':provider,'event':prefix+':0','s':source,'b':buyer,
                'item':item,'description':name,'unit':unit,'meta':encoded({'record_level':'item','fixture_only':True})})
    return c,provider,item


def params(provider,item):
    return dict(start='2026-09-01',end='2026-09-30',phase='homologado',provider=provider,
        item_id=item,item_version=1,limit=2,municipalities=['3131307'])


def test_exact_versions_units_currency_phase_revisions_and_nulls(data):
    c,provider,item=data;p=params(provider,item)
    response=c.get('/api/v1/municipal-history/indicators',params={**p,'limit':100})
    assert response.status_code==200,response.text
    rows=response.json()['records']
    primary=next(r for r in rows if r['observed_records']==3)
    assert primary['compatible_quantity']=='4.00000000'
    assert primary['documented_amount']=='10.00000000'
    assert not primary['quantity_complete'] and not primary['amount_complete']
    assert primary['identified_processes'] is None
    wrong=next(r for r in rows if r['unit']=='kg')
    assert wrong['compatible_quantity'] is None
    assert any(r['currency']=='foreign_or_unknown' for r in rows)
    assert all(r['phase']=='homologado' and r['item_version']==1 for r in rows)
    assert sum(r['observed_records'] for r in rows)==26
    assert response.json()['municipal_coverage'] is None


def test_cursor_pages_beyond_twenty_and_excluded_city_and_org(data,login):
    c,provider,item=data;p=params(provider,item);rows=[];cursor=None
    while True:
        response=c.get('/api/v1/municipal-history/indicators',params={**p,**({'cursor':cursor} if cursor else {})})
        assert response.status_code==200,response.text
        result=response.json();rows+=result['records'];cursor=result['next_cursor']
        if cursor is None:break
    assert len(rows)>20 and len({r['group_key'] for r in rows})==len(rows)
    assert c.get('/api/v1/municipal-history/indicators',params={**p,'municipalities':['3101607']}).json()['records']==[]
    other=login('compras-b').get('/api/v1/municipal-history/indicators',params=p)
    assert other.status_code==200 and other.json()['records']==[]


def test_invalid_scope_and_unimplemented_filters_are_explicit(data):
    c,provider,item=data;p=params(provider,item)
    for change in ({'municipalities':['9999999']},{'end':'2026-08-01'},{'cursor':'bad'},{'category':'not-supported'}):
        assert c.get('/api/v1/municipal-history/indicators',params={**p,**change}).status_code==422
    assert c.get('/api/v1/municipal-history/indicators',params={k:v for k,v in p.items() if k!='item_version'}).status_code==422
