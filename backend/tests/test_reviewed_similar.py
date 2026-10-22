"""Exact, tenant-scoped, reviewed equivalences; generated isolated fixtures only."""
from uuid import uuid4
import pytest
from sqlalchemy import create_engine
from app.config import load_settings
from app.db import DB,encoded
from test_history_contract import fixture_history

@pytest.fixture
def reviewed(fixture_history):
    create,client,identity=fixture_history;pid,add,get=create('official');first=add()
    engine=create_engine(load_settings().owner_database_url.get_secret_value(),hide_parameters=True)
    def change(action):
        with engine.begin() as c:
            db=DB(c);db.execute("SELECT set_config('irps.org_id',:o,true)",{'o':identity['org_id']});return action(db)
    def member(unit='caixa de 10 resmas'):
        nonlocal pid
        previous=pid;successor=str(uuid4())
        item='similar-test-'+uuid4().hex
        def write(db):
            db.execute("INSERT INTO item_version(id,version,name,family,unit,step,classification) VALUES (:i,1,'Papel de teste caixa com 10 resmas','Material',:u,1,'official')",{'i':item,'u':unit})
            db.execute("""INSERT INTO canonical_product(org_id,id,name,category,classification,unit_key,package_signature,members,justification,evidence,reviewed_by,supersedes_id)
              SELECT org_id,:s,name,category,classification,unit_key,package_signature,members||CAST(:m AS jsonb),justification,evidence,reviewed_by,id FROM canonical_product WHERE org_id=:o AND id=:p""",{'s':successor,'m':encoded([{'id':item,'version':1}]),'o':identity['org_id'],'p':previous})
        change(write);pid=successor;return item
    def request(**params):return client.get('/api/v1/director/products/'+pid+'/similar',params=params)
    yield pid,member,request,change,client,identity,first
    engine.dispose()

def test_reviewed_members_exact_versions_and_provenance(reviewed):
    pid,member,get,_,_,identity,fid=reviewed;second=member();r=get();assert r.status_code==200,r.text
    data=r.json();assert data['total']==2 and data['review']['supersedes_id']==pid
    assert data['review']['reviewed_by']==identity['actor_id'] and data['review']['evidence'] and data['review']['justification']
    assert all(m['version']==1 for m in data['records'])
    assert {m['id'] for m in data['records']} >= {second}
    assert any(m['fact_id']==fid and m['url'].startswith('https://example.invalid/') for m in data['records'])
    assert all('quantity' not in m and 'amount' not in m for m in data['records'])
    assert len(get(limit=1).json()['records'])==1
    assert get(limit=1,offset=1).json()['records'][0]['id']!=get(limit=1).json()['records'][0]['id']
    assert get(limit=21).status_code==422

@pytest.mark.parametrize('unit',['caixa de 20 resmas','kg'])
def test_incompatible_or_ambiguous_member_never_becomes_similar(reviewed,unit):
    _,member,get,_,_,_,_=reviewed;member(unit);response=get()
    assert response.status_code==409 and response.json()['detail']['code']=='INCOMPATIBLE_ITEMS'

def test_overlapping_active_groups_are_refused(reviewed):
    pid,_,get,change,_,identity,_=reviewed
    other=str(uuid4())
    change(lambda db:db.execute("""INSERT INTO canonical_product(org_id,id,name,category,classification,unit_key,package_signature,members,justification,evidence,reviewed_by)
       SELECT org_id,:i,name,category,classification,unit_key,package_signature,members,justification,evidence,reviewed_by FROM canonical_product WHERE org_id=:o AND id=:p""",{'i':other,'o':identity['org_id'],'p':pid}))
    assert get().status_code==409 and get().json()['detail']['code']=='CANONICAL_OVERLAP'

def test_other_tenant_and_nonexistent_product_cannot_be_read(reviewed,login):
    pid,_,_,_,client,_,_=reviewed
    assert login('compras-b').get('/api/v1/director/products/'+pid+'/similar').status_code==404
    assert client.get('/api/v1/director/products/'+str(uuid4())+'/similar').status_code==404

def test_superseded_review_never_served_as_current(reviewed):
    pid,_,get,change,client,identity,_=reviewed;successor=str(uuid4())
    change(lambda db:db.execute("""INSERT INTO canonical_product(org_id,id,name,category,classification,unit_key,package_signature,members,justification,evidence,reviewed_by,supersedes_id)
       SELECT org_id,:i,name,category,classification,unit_key,package_signature,members,justification,evidence,reviewed_by,id FROM canonical_product WHERE org_id=:o AND id=:p""",{'i':successor,'o':identity['org_id'],'p':pid}))
    assert get().status_code==404
    data=client.get('/api/v1/director/products/'+successor+'/similar').json()
    assert data['review']['supersedes_id']==pid

def test_missing_review_proof_is_not_name_based_fallback(reviewed):
    pid,_,_,change,client,identity,_=reviewed;successor=str(uuid4())
    change(lambda db:db.execute("""INSERT INTO canonical_product(org_id,id,name,category,classification,unit_key,package_signature,members,justification,evidence,reviewed_by,supersedes_id)
       SELECT org_id,:i,name,category,classification,unit_key,package_signature,members,justification,'',reviewed_by,id FROM canonical_product WHERE org_id=:o AND id=:p""",{'i':successor,'o':identity['org_id'],'p':pid}))
    response=client.get('/api/v1/director/products/'+successor+'/similar')
    assert response.status_code==409 and response.json()['detail']['code']=='EQUIVALENCE_REVIEW_REQUIRED'

def test_equal_name_and_newer_item_version_do_not_extend_review(reviewed):
    pid,_,get,change,_,identity,_=reviewed
    def write(db):
        p=db.one('SELECT members FROM canonical_product WHERE org_id=:o AND id=:p',{'o':identity['org_id'],'p':pid})
        original=p['members'][0]['id']
        db.execute("INSERT INTO item_version(id,version,name,family,unit,step,classification) SELECT id,2,name,family,unit,step,classification FROM item_version WHERE id=:i AND version=1",{'i':original})
        db.execute("INSERT INTO item_version(id,version,name,family,unit,step,classification) SELECT :new,1,name,family,unit,step,classification FROM item_version WHERE id=:i AND version=1",{'i':original,'new':'same-name-'+uuid4().hex})
    change(write);data=get().json()
    assert data['total']==1 and data['records'][0]['version']==1

def test_no_record_for_reviewed_version_is_explicit_not_invented(reviewed):
    _,member,get,_,_,_,_=reviewed;second=member()
    data=get().json();row=next(r for r in data['records'] if r['id']==second)
    assert row['fact_id'] is None and row['url'] is None and row['consulted_at'] is None
