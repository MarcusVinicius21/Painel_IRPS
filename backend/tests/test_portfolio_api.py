import hashlib
from uuid import uuid4
import pytest
from app import portfolio,portfolio_import,national_catalogue
from app.sources import job_context
from app.portfolio_rules import classify


@pytest.fixture
def prepared(app,login,settings,tmp_path):
    assert settings.auth_mode=='local_test'
    client=login();identity=client.get('/api/v1/auth/context').json();code=str(int(uuid4().hex[:9],16))
    path=tmp_path/'qa-material.csv';path.write_text('codigoItem;descricaoItem;statusItem\n'+code+';CAFÉ, TIPO TORRADO, APRESENTAÇÃO MOÍDO;True\n',encoding='utf-8')
    national_catalogue.import_csv(settings.owner_database_url.get_secret_value(),path,'CATMAT',expected_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),expected_records=1)
    with app.state.database.transaction(identity['org_id'],identity['actor_id']) as db:
        entry=db.one('SELECT e.*,s.kind FROM national_catalogue_entry e JOIN national_catalogue_snapshot s ON s.id=e.snapshot_id WHERE code=:c',{'c':code})
        row={**entry,**classify(entry)[0]};ctx=job_context(db,identity['org_id'],identity['actor_id'])
        checksum=uuid4().hex*2
        first=portfolio_import.import_rows(ctx,[row],rule_sha256=checksum,input_sha256=checksum,provenance={'fixture_only':True})
        again=portfolio_import.import_rows(ctx,[row],rule_sha256=checksum,input_sha256=checksum,provenance={'fixture_only':True})
        assert again['duplicate'] and again['id']==first['id']
    return client,code


def test_twenty_groups_code_search_and_national_catalogue_unchanged(prepared):
    c,code=prepared
    response=c.get('/api/v1/portfolio/groups');assert response.status_code==200,response.text
    assert len(response.json()['records'])==20
    query=c.get('/api/v1/portfolio/codes',params={'group':'15','q':code,'limit':1})
    assert query.status_code==200,query.text
    rows=query.json()['records'];assert len(rows)==1 and rows[0]['code']==code
    assert rows[0]['commercial_status']=='COMMERCIAL_PENDING'
    assert c.get('/api/v1/portfolio/codes?group=01&q='+code).json()['records']==[]
    assert c.get('/api/v1/national-catalogue?q='+code).json()['total']>=1
    assert c.get('/api/v1/portfolio/codes?group=15&not_implemented=1').status_code==422


def test_preferences_persist_and_other_organization_is_isolated(prepared,login):
    c,_=prepared
    payload={'group':'15','q':'café','municipalities':['3131307'],'phase':'homologado','start':'2025-10-01','end':'2026-09-30'}
    saved=c.post('/api/v1/portfolio/preferences',json=payload);assert saved.status_code==201,saved.text
    read=c.get('/api/v1/portfolio/preferences').json();assert read['payload']['group']=='15' and read['payload']['municipalities']==['3131307']
    other=login('compras-b');assert other.get('/api/v1/portfolio/groups').json()['records']==[]
    assert other.get('/api/v1/portfolio/preferences').json()['id'] is None
    assert login('consulta-a').post('/api/v1/portfolio/preferences',json=payload).status_code==403
    assert c.post('/api/v1/portfolio/preferences',json={**payload,'municipalities':['9999999']}).status_code==422


def test_rls_forced_and_immutable_rows(prepared,app):
    c,_=prepared;identity=c.get('/api/v1/auth/context').json()
    with app.state.database.transaction(identity['org_id'],identity['actor_id']) as db:
        rows=db.all("SELECT relname,relrowsecurity,relforcerowsecurity FROM pg_class WHERE relname IN ('portfolio_run','portfolio_group','portfolio_code_link','portfolio_preference')")
        assert len(rows)==4 and all(r['relrowsecurity'] and r['relforcerowsecurity'] for r in rows)
