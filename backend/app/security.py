from dataclasses import dataclass
from pathlib import Path
from contextlib import contextmanager
import hashlib,secrets,time,json,uuid
import jwt
from jwt import PyJWK,PyJWKClient
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from fastapi import Request,HTTPException
from .db import DB,identifier,encoded

PERMISSIONS={
 'planner':{'read','scenario.write','scenario.calculate','scenario.review','document.read','document.write','document.review','export','sources.sync','watch'},
 'reviewer':{'read','scenario.review','document.read','document.review','export'},
 'viewer':{'read','document.read','export'},
 'business_owner':{'read','scenario.write','scenario.calculate','document.read','document.write','document.review','export','sources.sync','quote.read','quote.write','watch'},
 'technical_admin':{'read','sources.sync'},
}
for _role in ('planner','reviewer','business_owner'):
 PERMISSIONS[_role].add('opportunity.manage')
TEST_USERS=[
 {'key':'compras-a','name':'Equipe de compras A','org':'CONSORMULTI · organização A','role':'planner','kind':'consortium'},
 {'key':'compras-b','name':'Equipe de compras B','org':'Organização pública B','role':'planner','kind':'government'},
 {'key':'consulta-a','name':'Consulta da organização A','org':'CONSORMULTI · organização A','role':'viewer','kind':'consortium','org_key':'compras-a'},
 {'key':'empresa-a','name':'Empresa fictícia A','org':'Empresa fictícia A','role':'business_owner','kind':'business'},
 {'key':'empresa-b','name':'Empresa fictícia B','org':'Empresa fictícia B','role':'business_owner','kind':'business'},
 {'key':'tecnico-a','name':'Suporte técnico da empresa A','org':'Empresa fictícia A','role':'technical_admin','kind':'business','org_key':'empresa-a'},
]
def stable_id(name):return str(uuid.uuid5(uuid.NAMESPACE_URL,'irps-local-test:'+name))
def digest(value):return hashlib.sha256(value.encode()).hexdigest()
def fail(status,message,code='ACCESS_DENIED'):raise HTTPException(status,{'message':message,'code':code})

class Verifier:
 def __init__(self,settings):
  self.settings=settings;self.private=None;self.public_jwk=None;self.remote=None
  if settings.auth_mode=='local_test':
   path=Path(settings.runtime)/'test-issuer-private.pem';path.parent.mkdir(parents=True,exist_ok=True)
   if not path.exists():
    key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    path.write_bytes(key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
   self.private=serialization.load_pem_private_key(path.read_bytes(),password=None)
   self.public_jwk=json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(self.private.public_key()))
   self.public_jwk.update(kid='irps-local-test-rsa-v1',use='sig',alg='RS256')
  elif settings.issuer.startswith('https://') and settings.jwks_url.startswith('https://'):
   self.remote=PyJWKClient(settings.jwks_url,cache_jwk_set=True,lifespan=300,timeout=5)
 def decode(self,token):
  if not token or len(token)>16384:fail(401,'Entre novamente para continuar.','INVALID_TOKEN')
  try:
   header=jwt.get_unverified_header(token)
   if header.get('alg')!='RS256' or not header.get('kid'):raise ValueError('algorithm')
   if self.settings.auth_mode=='local_test':
    if header['kid']!=self.public_jwk['kid']:raise ValueError('kid')
    key=PyJWK.from_dict(self.public_jwk).key
   elif self.remote:key=self.remote.get_signing_key_from_jwt(token).key
   else:fail(503,'O acesso da organização ainda não foi configurado.','OIDC_NOT_CONFIGURED')
   c=jwt.decode(token,key,algorithms=['RS256'],issuer=self.settings.issuer,audience=self.settings.audience,options={'require':['exp','iat','nbf','iss','aud','sub','jti','org_id']})
   uuid.UUID(c['org_id']);return c
  except HTTPException:raise
  except Exception:fail(401,'Sua sessão não é válida. Entre novamente.','INVALID_TOKEN')
 def mint(self,subject,org):
  now=int(time.time());jti=secrets.token_urlsafe(24)
  claims={'iss':self.settings.issuer,'aud':self.settings.audience,'sub':subject,'org_id':org,'jti':jti,'iat':now,'nbf':now,'exp':now+self.settings.token_seconds}
  return jwt.encode(claims,self.private,algorithm='RS256',headers={'kid':self.public_jwk['kid']}),claims

@dataclass
class Context:
 db:DB
 org_id:str
 actor_id:str
 role:str
 kind:str
 name:str
 organization:str
 jti:str
 def require(self,permission):
  if permission not in PERMISSIONS.get(self.role,set()):fail(403,'Seu acesso não permite esta ação.')
  if permission.startswith('quote.') and self.kind!='business':fail(403,'Os custos ficam no espaço da empresa.')
 def audit(self,action,resource,metadata=None):
  self.db.execute('INSERT INTO audit_event(org_id,id,actor_id,action,resource_id,metadata) VALUES (:o,:i,:a,:action,:r,CAST(:m AS jsonb))',{'o':self.org_id,'i':identifier(),'a':self.actor_id,'action':action,'r':str(resource),'m':encoded(metadata or {})})

def authenticate(request:Request):
 state=request.app.state;authorization=request.headers.get('authorization','');bearer=authorization.startswith('Bearer ')
 token=authorization[7:] if bearer else request.cookies.get('irps_session','')
 claims=state.verifier.decode(token)
 with state.database.transaction(claims['org_id']) as db:
  actor=db.one('SELECT id,name,active FROM actor WHERE issuer=:iss AND subject=:sub',{'iss':claims['iss'],'sub':claims['sub']})
  if not actor or not actor['active']:fail(401,'Este acesso foi desativado.','REVOKED')
  membership=db.one('SELECT m.role,m.active,o.kind,o.name FROM membership m JOIN organization o ON o.id=m.org_id WHERE m.org_id=:o AND m.actor_id=:a',{'o':claims['org_id'],'a':actor['id']})
  session=db.one('SELECT csrf_digest,revoked,expires_at>now() AS valid FROM auth_session WHERE org_id=:o AND id=:j AND actor_id=:a',{'o':claims['org_id'],'j':claims['jti'],'a':actor['id']})
  if not membership or not membership['active'] or not session or session['revoked'] or not session['valid']:fail(401,'Seu acesso foi encerrado. Entre novamente.','REVOKED')
  if request.method not in ('GET','HEAD','OPTIONS') and not bearer:
   nonce=request.headers.get('x-csrf-token','')
   if not nonce or not secrets.compare_digest(digest(nonce),session['csrf_digest']):fail(403,'Atualize a página antes de continuar.','CSRF')
  db.execute("SELECT set_config('irps.actor_id',:a,true)",{'a':str(actor['id'])})
  ctx=Context(db,claims['org_id'],str(actor['id']),membership['role'],membership['kind'],actor['name'],membership['name'],claims['jti'])
  ctx.require('read')
  key=(ctx.org_id,ctx.actor_id,int(time.time()//60));count=state.limiter.get(key,0)+1;state.limiter[key]=count
  if count>state.settings.rate_limit:fail(429,'O limite de consultas foi alcançado. Tente novamente em instantes.','RATE_LIMIT')
  if len(state.limiter)>10000:state.limiter={k:v for k,v in state.limiter.items() if k[-1]>=int(time.time()//60)-1}
  yield ctx

def establish_session(app,db,claims,actor,token,response):
 nonce=secrets.token_urlsafe(24)
 db.execute('INSERT INTO auth_session(org_id,id,actor_id,csrf_digest,expires_at) VALUES (:o,:j,:a,:c,to_timestamp(:e)) ON CONFLICT(org_id,id) DO UPDATE SET csrf_digest=EXCLUDED.csrf_digest,revoked=false',{'o':claims['org_id'],'j':claims['jti'],'a':actor['id'],'c':digest(nonce),'e':claims['exp']})
 response.set_cookie('irps_session',token,httponly=True,secure=app.state.settings.cookie_secure,samesite='strict',max_age=app.state.settings.token_seconds,path='/')
 response.set_cookie('irps_csrf',nonce,httponly=False,secure=app.state.settings.cookie_secure,samesite='strict',max_age=app.state.settings.token_seconds,path='/')
 return {'authenticated':True,'identity_mode':app.state.settings.auth_mode,'production_identity':app.state.settings.auth_mode=='oidc'}
