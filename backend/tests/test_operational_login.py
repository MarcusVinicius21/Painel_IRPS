"""Single operator regression on disposable QA DB, never the operational dataset."""
import uuid,time
from dataclasses import replace
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.operational import PASSWORDS
from app.security import PERMISSIONS
from app.seed import seed
from pydantic import SecretStr

@pytest.fixture
def operator(settings):
    org=str(uuid.uuid4());actor=str(uuid.uuid4());password='test-only-'+uuid.uuid4().hex
    s=settings.model_copy(update={'auth_mode':'operational_local','operator_org_id':org,'operator_actor_id':actor,
        'operator_password_hash':SecretStr(PASSWORDS.hash(password)),'issuer':'irps:qa:single-operator:'+actor,
        'allowed_origins':['http://127.0.0.1:5292'],'cookie_secure':False})
    app=create_app(s)
    # Prepare only this test identity; fixtures remain separate from operational data.
    from sqlalchemy import create_engine,text
    engine=create_engine(s.owner_database_url.get_secret_value(),hide_parameters=True)
    with engine.begin() as conn:
        conn.execute(text("SELECT set_config('irps.org_id',:o,true)"),{'o':org})
        conn.execute(text("INSERT INTO organization(id,name,kind) VALUES (:o,'CONSORMULTI QA','consortium')"),{'o':org})
        conn.execute(text("INSERT INTO actor(id,issuer,subject,name) VALUES (:a,:iss,'consormulti-operador','Operador QA')"),{'a':actor,'iss':s.issuer})
        conn.execute(text("INSERT INTO membership(org_id,actor_id,role) VALUES (:o,:a,'planner')"),{'o':org,'a':actor})
    engine.dispose()
    with TestClient(app,client=('127.0.0.1',1234)) as client:
        yield client,app,password

def enter(operator):
    client,app,password=operator
    r=client.post('/api/v1/auth/operator-login',json={'password':password});assert r.status_code==200
    client.headers['x-csrf-token']=client.cookies.get('irps_operator_csrf')
    return client,app

def test_single_login_all_permissions(operator):
    c,app=enter(operator)
    r=c.get('/api/v1/auth/context');assert r.status_code==200
    assert set(r.json()['permissions'])==set().union(*PERMISSIONS.values())
    assert r.json()['kind']=='consortium'
    assert 'HttpOnly' in c.cookies.jar._cookies['testserver.local']['/']['irps_operator_session']._rest
    for url in ['/quotes','/documents','/director/studies','/scenarios','/sources','/national-catalogue','/audit']:
        assert c.get('/api/v1'+url).status_code==200,url

def test_wrong_password_and_persistent_limit(operator):
    c,_,_=operator
    for _ in range(5):assert c.post('/api/v1/auth/operator-login',json={'password':'wrong'}).status_code==401
    assert c.post('/api/v1/auth/operator-login',json={'password':'wrong'}).status_code==429
    assert c.get('/api/v1/auth/context').status_code==401

def test_csrf_logout_and_revocation(operator):
    c,_=enter(operator);cookie=c.cookies.get('irps_operator_session')
    csrf=c.headers.pop('x-csrf-token')
    assert c.post('/api/v1/auth/logout').status_code==403
    c.headers['x-csrf-token']=csrf
    assert c.post('/api/v1/auth/logout').status_code==200
    assert c.get('/api/v1/auth/context',headers={'Authorization':'Bearer '+cookie}).status_code==401

def test_expired_and_wrong_operator_tokens(operator):
    c,app=enter(operator);settings=app.state.settings
    token,_=app.state.verifier.mint('another-identity',settings.operator_org_id)
    assert c.get('/api/v1/auth/context',headers={'Authorization':'Bearer '+token}).status_code==401
    token,_=app.state.verifier.mint('consormulti-operador',str(uuid.uuid4()))
    assert c.get('/api/v1/auth/context',headers={'Authorization':'Bearer '+token}).status_code==401
    settings.token_seconds=-1
    token,_=app.state.verifier.mint('consormulti-operador',settings.operator_org_id)
    assert c.get('/api/v1/auth/context',headers={'Authorization':'Bearer '+token}).status_code==401

def test_test_routes_and_synthetic_writes_forbidden(operator):
    c,_=enter(operator)
    assert c.get('/api/v1/auth/test-users').status_code==404
    assert c.post('/api/v1/auth/test-login',json={'user_key':'compras-a'}).status_code==404
    assert c.get('/local-issuer/.well-known/jwks.json').status_code==404
    assert c.post('/api/v1/scenarios/synthetic',json={'participants':3,'items':1,'title':'QA blocked'}).status_code==404
    assert c.post('/api/v1/director/studies',json={'classification':'synthetic'}).status_code==422

def test_non_loopback_and_untrusted_origin(operator):
    c,app,password=operator
    assert c.post('/api/v1/auth/operator-login',json={'password':password},headers={'Origin':'https://untrusted.invalid'}).status_code==403
    with TestClient(app,client=('192.0.2.10',1234)) as remote:
        assert remote.get('/api/v1/auth/mode').status_code==403

def test_seed_refuses_operational_mode(operator):
    _,app,_=operator
    with pytest.raises(RuntimeError):seed(app.state.settings)

def test_synthetic_multipart_document_forbidden(operator):
    c,_=enter(operator)
    r=c.post('/api/v1/documents',files={'file':('example.csv',b'descricao,quantidade\npapel,1')},data={'classification':'synthetic'})
    assert r.status_code==422
    assert r.json()['detail']['code']=='SYNTHETIC_DISABLED'

def test_unauthenticated_modules(operator):
    c,_,_=operator
    for path in ['/quotes','/documents','/scenarios','/director/studies']:
        assert c.get('/api/v1'+path).status_code==401
