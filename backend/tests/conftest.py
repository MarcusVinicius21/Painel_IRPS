import os,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'backend'))
os.environ.setdefault('IRPS_LOCAL_CONFIG',str(ROOT/'.runtime/config-test.json'))
from app.config import load_settings
from app.seed import seed
from app.main import create_app
from fastapi.testclient import TestClient

@pytest.fixture(scope='session')
def settings():
 s=load_settings();s.testing=True;s.rate_limit=100000;seed(s);return s
@pytest.fixture(scope='session')
def app(settings):return create_app(settings)
@pytest.fixture
def login(app):
 clients=[]
 def factory(user='compras-a'):
  c=TestClient(app);r=c.post('/api/v1/auth/test-login',json={'user_key':user});assert r.status_code==200,r.text
  c.headers['x-csrf-token']=c.cookies.get('irps_csrf');clients.append(c);return c
 yield factory
 for c in clients:c.close()
