from contextlib import asynccontextmanager
from typing import Annotated,Literal
from uuid import UUID
from pathlib import Path
import hashlib,secrets
from fastapi import FastAPI,Depends,Request,Response,UploadFile,File,Form,BackgroundTasks,Header,HTTPException,Query
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse,FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError
from irps_core.domain import ValidationError
from .config import load_settings
from .db import Database,encoded,identifier,normalize
from .security import authenticate,Verifier,TEST_USERS,stable_id,establish_session,fail,PERMISSIONS
from .schemas import Login,ScenarioCreate,Snapshot,SyntheticCreate,QuoteBody,DocumentReview,AssistantBody,ToolCall,SourceSync,WatchBody
from . import scenarios,documents,exports,assistant,sources
from .opportunity_routes import router as opportunity_router
from .director_routes import router as director_router

Auth=Annotated[object,Depends(authenticate,scope='function')]

def reject_query(request,allowed):
 if set(request.query_params)-set(allowed):fail(422,'Há um filtro não reconhecido. Revise a consulta.','UNKNOWN_FILTER')

def create_app(settings=None):
 settings=settings or load_settings()
 if settings.ai_enabled:raise RuntimeError('Provedores pagos não são habilitados nesta rodada.')
 @asynccontextmanager
 async def lifespan(app):
  yield
  if app.state.database.engine:app.state.database.engine.dispose()
 app=FastAPI(title='IRPS · serviço local',version='0.1.0',lifespan=lifespan)
 app.state.settings=settings;app.state.database=Database(settings);app.state.verifier=Verifier(settings);app.state.limiter={}
 app.add_middleware(CORSMiddleware,allow_origins=settings.allowed_origins,allow_credentials=True,allow_methods=['GET','POST','PUT','DELETE','OPTIONS'],allow_headers=['Content-Type','X-CSRF-Token','If-Match','Idempotency-Key','Authorization'],expose_headers=['ETag'])
 @app.middleware('http')
 async def safeguards(request,call_next):
  request_id=secrets.token_hex(8);origin=request.headers.get('origin')
  if origin and origin not in settings.allowed_origins:return JSONResponse({'detail':{'message':'Esta origem não está autorizada.','code':'ORIGIN_DENIED'}},403)
  try:length=int(request.headers.get('content-length','0'))
  except ValueError:length=10_000_001
  if length>10_000_000:return JSONResponse({'detail':{'message':'Divida o envio em partes menores.','code':'REQUEST_LIMIT'}},413)
  response=await call_next(request)
  response.headers.update({'X-Request-ID':request_id,'X-Content-Type-Options':'nosniff','Cache-Control':'no-store','Referrer-Policy':'no-referrer','X-Frame-Options':'DENY'})
  return response
 @app.exception_handler(RequestValidationError)
 async def validation_error(request,exc):return JSONResponse({'detail':{'message':'Confira os campos e filtros informados.','code':'INVALID_INPUT','fields':['.'.join(str(v) for v in e['loc']) for e in exc.errors()]}},422)
 @app.exception_handler(ValidationError)
 async def core_error(request,exc):return JSONResponse({'detail':{'message':str(exc),'code':'CALCULATION_INVALID'}},422)
 @app.exception_handler(SQLAlchemyError)
 async def database_error(request,exc):return JSONResponse({'detail':{'message':'Não foi possível salvar agora. Atualize e tente novamente.','code':'DATABASE_OPERATION'}},409)

 @app.get('/health')
 def health():
  try:
   with app.state.database.transaction() as db:db.one('SELECT 1 AS ready')
   return {'status':'ok','database':'PostgreSQL','identity_mode':settings.auth_mode,'paid_ai_enabled':False}
  except Exception:return JSONResponse({'status':'unavailable'},503)

 @app.get('/health/live')
 def live():return {'status':'alive'}
 @app.get('/health/ready')
 def ready():return health()

 @app.get('/local-issuer/.well-known/jwks.json')
 def jwks():
  if settings.auth_mode!='local_test':fail(404,'Esta página não está disponível.')
  return {'keys':[app.state.verifier.public_jwk]}

 def test_only(request):
  if settings.auth_mode!='local_test' or (request.client.host not in ('127.0.0.1','::1') and not settings.testing):fail(404,'Esta opção não está disponível.')

 @app.get('/api/v1/auth/test-users')
 def test_users(request:Request):
  test_only(request);return {'users':[{'key':u['key'],'name':u['name'],'organization':u['org']} for u in TEST_USERS],'real_people':False}

 @app.post('/api/v1/auth/test-login')
 def login(body:Login,request:Request,response:Response):
  test_only(request);u=next(x for x in TEST_USERS if x['key']==body.user_key);org=stable_id('org:'+u.get('org_key',u['key']))
  with app.state.database.transaction(org) as db:
   actor=db.one('SELECT a.id,a.active,m.active AS membership_active FROM actor a JOIN membership m ON m.actor_id=a.id WHERE a.issuer=:iss AND a.subject=:sub AND m.org_id=:o',{'iss':settings.issuer,'sub':body.user_key,'o':org})
   if not actor or not actor['active'] or not actor['membership_active']:fail(401,'Este acesso de teste não está disponível.')
   token,claims=app.state.verifier.mint(body.user_key,org)
   # Verify the minted token through the same verification path as every protected call.
   app.state.verifier.decode(token);return establish_session(app,db,claims,actor,token,response)

 @app.post('/api/v1/auth/oidc-session')
 def oidc_session(request:Request,response:Response):
  if settings.auth_mode!='oidc':fail(404,'Esta opção ainda não está disponível.')
  auth=request.headers.get('authorization','')
  if not auth.startswith('Bearer '):fail(401,'Entre pelo acesso da sua organização.')
  claims=app.state.verifier.decode(auth[7:])
  with app.state.database.transaction(claims['org_id']) as db:
   actor=db.one('SELECT a.id,a.active,m.active AS membership_active FROM actor a JOIN membership m ON m.actor_id=a.id WHERE a.issuer=:iss AND a.subject=:sub AND m.org_id=:o',{'iss':claims['iss'],'sub':claims['sub'],'o':claims['org_id']})
   if not actor or not actor['active'] or not actor['membership_active']:fail(403,'Sua organização ainda não liberou este acesso.')
   return establish_session(app,db,claims,actor,auth[7:],response)

 @app.get('/api/v1/auth/context')
 def context(ctx:Auth):return {'actor_id':ctx.actor_id,'name':ctx.name,'org_id':ctx.org_id,'organization':ctx.organization,'kind':ctx.kind,'role':ctx.role,'permissions':sorted(PERMISSIONS.get(ctx.role,set())),'identity_mode':settings.auth_mode,'production_identity':settings.auth_mode=='oidc'}

 @app.post('/api/v1/auth/logout')
 def logout(ctx:Auth,response:Response):
  ctx.db.execute('UPDATE auth_session SET revoked=true WHERE org_id=:o AND id=:j',{'o':ctx.org_id,'j':ctx.jti});ctx.db.execute('DELETE FROM ai_cache WHERE org_id=:o AND actor_id=:a',{'o':ctx.org_id,'a':ctx.actor_id});ctx.audit('auth.logout',ctx.actor_id)
  response.delete_cookie('irps_session',path='/');response.delete_cookie('irps_csrf',path='/');return {'signed_out':True}

 @app.get('/api/v1/municipalities')
 def municipalities(ctx:Auth,request:Request,q:str='',limit:int=Query(6000,ge=1,le=6000)):
  reject_query(request,{'q','limit'});return {'records':ctx.db.all('SELECT ibge,name,uf,origin,updated_at FROM municipality WHERE name ILIKE :q OR ibge LIKE :q ORDER BY name LIMIT :n',{'q':'%'+q[:100]+'%','n':limit})}
 @app.get('/api/v1/items')
 def items(ctx:Auth):return normalize({'records':ctx.db.all('SELECT * FROM (SELECT DISTINCT ON (id) * FROM item_version ORDER BY id,version DESC) latest ORDER BY CASE WHEN id IN (\'papel\',\'medicamento\',\'veiculo\',\'servico\',\'obra\') THEN 0 ELSE 1 END,id'),'versions':ctx.db.all('SELECT * FROM item_version ORDER BY id,version DESC'),'classification':'mixed_explicit','official_catalogue_connected':True})
 @app.get('/api/v1/catalogue/official')
 def official_catalogue(ctx:Auth,q:str=''):
  return {'records':ctx.db.all('SELECT c.*,s.url AS source_url,s.consulted_at FROM official_catalogue_entry c JOIN source_observation s ON s.id=c.source_id WHERE c.description ILIKE :q OR c.code=:code ORDER BY c.provider,c.code LIMIT 100',{'q':'%'+q[:150]+'%','code':q}),'units_ready_for_calculation':False,'quantities_included':False}

 @app.get('/api/v1/scenarios')
 def scenario_list(ctx:Auth):return {'records':ctx.db.all('SELECT * FROM scenario WHERE org_id=:o ORDER BY created_at DESC LIMIT 100',{'o':ctx.org_id})}
 @app.post('/api/v1/scenarios',status_code=201)
 def scenario_create(body:ScenarioCreate,ctx:Auth):return scenarios.create_scenario(ctx,body)
 @app.post('/api/v1/scenarios/synthetic',status_code=201)
 def scenario_synthetic(body:SyntheticCreate,request:Request,ctx:Auth):
  test_only(request);return scenarios.synthetic_scenario(ctx,body)
 @app.get('/api/v1/scenarios/{sid}')
 def scenario_get(sid:UUID,ctx:Auth,response:Response,revision:int|None=None):
  r=scenarios.get_scenario(ctx,str(sid),revision);response.headers['ETag']=f'"{r["current_revision"]}"';return r
 @app.put('/api/v1/scenarios/{sid}')
 def scenario_put(sid:UUID,body:Snapshot,ctx:Auth,if_match:str|None=Header(None)):
  return scenarios.update_scenario(ctx,str(sid),body,scenarios.etag(if_match))
 @app.post('/api/v1/scenarios/{sid}/confirm-distribution')
 def distribution_confirm(sid:UUID,ctx:Auth,if_match:str|None=Header(None)):return scenarios.confirm_distribution(ctx,str(sid),scenarios.etag(if_match))
 @app.post('/api/v1/scenarios/{sid}/calculate')
 def scenario_calculate(sid:UUID,ctx:Auth,revision:int|None=None):return scenarios.calculate(ctx,str(sid),revision)
 @app.post('/api/v1/scenarios/{sid}/review')
 def scenario_review(sid:UUID,ctx:Auth,if_match:str|None=Header(None)):return scenarios.review(ctx,str(sid),scenarios.etag(if_match))
 @app.get('/api/v1/scenarios/{sid}/versions')
 def versions(sid:UUID,ctx:Auth):
  scenarios.get_scenario(ctx,str(sid));return {'records':ctx.db.all('SELECT revision,created_at,created_by FROM scenario_version WHERE org_id=:o AND scenario_id=:s ORDER BY revision DESC',{'o':ctx.org_id,'s':sid})}
 @app.get('/api/v1/scenarios/{sid}/calculations')
 def calculations(sid:UUID,ctx:Auth):
  scenarios.get_scenario(ctx,str(sid));return {'records':ctx.db.all('SELECT * FROM calculation WHERE org_id=:o AND scenario_id=:s ORDER BY created_at DESC LIMIT 30',{'o':ctx.org_id,'s':sid})}
 @app.get('/api/v1/calculations/{cid}/lines')
 def lines(cid:UUID,ctx:Auth,request:Request,offset:int=Query(0,ge=0,le=600000),limit:int=Query(20,ge=1,le=100),item_id:str|None=None,municipality_ibge:str|None=None):
  reject_query(request,{'offset','limit','item_id','municipality_ibge'})
  calc=ctx.db.one('SELECT * FROM calculation WHERE org_id=:o AND id=:i',{'o':ctx.org_id,'i':cid})
  if not calc:fail(404,'Este cálculo não está disponível neste espaço.')
  filt='l.org_id=:o AND l.calculation_id=:i';params={'o':ctx.org_id,'i':cid,'n':limit,'offset':offset}
  if item_id:filt+=' AND l.item_id=:item';params['item']=item_id
  if municipality_ibge:filt+=' AND l.ibge=:city';params['city']=municipality_ibge
  count=ctx.db.one('SELECT count(*) AS n FROM calculation_line l WHERE '+filt,params)['n']
  records=ctx.db.all('SELECT l.*,m.name AS municipality_name,v.name AS item_name FROM calculation_line l JOIN municipality m ON m.ibge=l.ibge JOIN item_version v ON v.id=l.item_id AND v.version=l.item_version WHERE '+filt+' ORDER BY l.ibge,l.item_id LIMIT :n OFFSET :offset',params)
  return normalize({'records':records,'total':count,'offset':offset,'limit':limit,'revision':calc['revision']})
 @app.get('/api/v1/calculations/{cid}/item-lines')
 def item_lines(cid:UUID,ctx:Auth,item_id:str,item_version:int=Query(ge=1),municipalities:list[str]=Query(default_factory=list)):
  ctx.require('read')
  cities=list(dict.fromkeys(municipalities))
  if not cities or len(cities)>118:fail(422,'Selecione de um a 118 municípios.','MUNICIPALITY_SCOPE')
  calc=ctx.db.one('SELECT scenario_id,revision FROM calculation WHERE org_id=:o AND id=:i',{'o':ctx.org_id,'i':cid})
  if not calc:fail(404,'Este cálculo não está disponível neste espaço.')
  scenario=ctx.db.one('SELECT current_revision FROM scenario WHERE org_id=:o AND id=:s',{'o':ctx.org_id,'s':calc['scenario_id']})
  if not scenario or calc['revision']!=scenario['current_revision']:
   fail(409,'Este cálculo pertence a uma versão anterior. Calcule novamente.','CALCULATION_STALE')
  records=ctx.db.all('''SELECT l.*,m.name AS municipality_name,v.name AS item_name
   FROM calculation_line l JOIN municipality m ON m.ibge=l.ibge
   JOIN item_version v ON v.id=l.item_id AND v.version=l.item_version
   WHERE l.org_id=:o AND l.calculation_id=:i AND l.item_id=:item
     AND l.item_version=:version AND l.ibge=ANY(:cities) ORDER BY l.ibge''',
   {'o':ctx.org_id,'i':cid,'item':item_id,'version':item_version,'cities':cities})
  return normalize({'records':records,'calculation_id':cid,'revision':calc['revision'],
                    'item_id':item_id,'item_version':item_version,'municipalities':cities})
 @app.post('/api/v1/scenarios/{sid}/exports/{fmt}')
 def scenario_export(sid:UUID,fmt:Literal['csv','xlsx','pdf'],ctx:Auth,calculation_id:UUID):return exports.create(ctx,settings.runtime,str(sid),fmt,str(calculation_id))
 @app.get('/api/v1/artifacts/{aid}/download')
 def artifact_download(aid:UUID,ctx:Auth):
  p,r=exports.authorized_file(ctx,settings.runtime,str(aid));return FileResponse(p,media_type=r['media_type'],filename=r['filename'])

 @app.get('/api/v1/quotes')
 def quote_list(ctx:Auth):
  ctx.require('quote.read');return {'records':ctx.db.all('SELECT q.id,q.current_revision,v.result,v.inputs FROM private_quote q JOIN quote_version v ON v.org_id=q.org_id AND v.quote_id=q.id AND v.revision=q.current_revision WHERE q.org_id=:o',{'o':ctx.org_id})}
 @app.post('/api/v1/quotes',status_code=201)
 def quote_create(body:QuoteBody,ctx:Auth):return scenarios.quote(ctx,body)
 @app.get('/api/v1/quotes/{qid}')
 def quote_get(qid:UUID,ctx:Auth):return assistant.execute_tool(ctx,ToolCall(tool='read_quote',quote_id=str(qid)))
 @app.put('/api/v1/quotes/{qid}')
 def quote_put(qid:UUID,body:QuoteBody,ctx:Auth,if_match:str|None=Header(None)):return scenarios.quote(ctx,body,str(qid),scenarios.etag(if_match))

 @app.get('/api/v1/documents')
 def document_list(ctx:Auth):
  ctx.require('document.read');private='quote.read' in PERMISSIONS.get(ctx.role,set())
  return {'records':ctx.db.all("SELECT d.id,d.filename,d.classification,d.created_at,d.sha256,(SELECT max(revision) FROM extracted_document e WHERE e.org_id=d.org_id AND e.document_id=d.id) AS revision FROM document d WHERE org_id=:o AND (:private OR classification<>'business_private') ORDER BY created_at DESC",{'o':ctx.org_id,'private':private})}
 @app.post('/api/v1/documents',status_code=201)
 async def document_upload(ctx:Auth,file:UploadFile=File(...),classification:Literal['synthetic','internal','business_private']=Form('internal')):
  data=await file.read(documents.LIMIT+1);return documents.ingest(ctx,settings.runtime,file.filename or 'arquivo',data,classification)
 @app.get('/api/v1/documents/{did}')
 def document_get(did:UUID,ctx:Auth):
  r=documents.get(ctx,str(did));r.pop('storage_key',None);return r
 @app.post('/api/v1/documents/{did}/review')
 def document_review(did:UUID,body:DocumentReview,ctx:Auth):return documents.review(ctx,str(did),body)
 @app.get('/api/v1/documents/{did}/original')
 def document_original(did:UUID,ctx:Auth):
  r=documents.get(ctx,str(did));root=Path(settings.runtime).resolve();p=(root/r['storage_key']).resolve()
  if root not in p.parents or not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=r['sha256']:fail(409,'O original precisa de verificação.')
  return FileResponse(p,media_type='application/octet-stream',filename=r['filename'])

 @app.post('/api/v1/assistant/ask')
 def assistant_ask(body:AssistantBody,ctx:Auth):return assistant.ask(ctx,body)
 @app.post('/api/v1/assistant/tools')
 def assistant_tool(body:ToolCall,ctx:Auth):return {**assistant.execute_tool(ctx,body),'mode':'offline','external_calls':0}
 @app.post('/api/v1/assistant/external')
 def external_disabled(ctx:Auth):fail(503,'Os serviços externos de inteligência artificial estão desativados.','PAID_AI_DISABLED')

 @app.get('/api/v1/purchases')
 def purchases(ctx:Auth,request:Request,q:str='',dataset:Literal['official','synthetic']='official',municipality_ibge:str|None=None,item_id:str|None=None,item_version:int|None=None,phase:str|None=None,offset:int=Query(0,ge=0,le=100000),limit:int=Query(20,ge=1,le=100)):
  reject_query(request,{'q','dataset','municipality_ibge','item_id','item_version','phase','offset','limit'})
  if phase and phase not in ('publicado_estimado','homologado','contratado','solicitado','entregue','consumido','empenhado','liquidado','pago','estorno'):fail(422,'Escolha uma situação reconhecida.')
  if item_id and not item_version:fail(422,'Escolha também a versão do item.')
  if municipality_ibge and not ctx.db.one('SELECT ibge FROM municipality WHERE ibge=:i',{'i':municipality_ibge}):fail(422,'Não encontramos esse município. Confira o código IBGE.','UNKNOWN_MUNICIPALITY')
  if item_id and not ctx.db.one('SELECT id FROM item_version WHERE id=:i AND version=:v',{'i':item_id,'v':item_version}):fail(422,'Não encontramos essa versão do item.','UNKNOWN_ITEM')
  clauses=['f.is_current','f.classification=:dataset'];params={'dataset':dataset,'n':limit,'off':offset}
  for k,value,col in [('city',municipality_ibge,'municipality_ibge'),('item',item_id,'item_id'),('version',item_version,'item_version'),('phase',phase,'phase')]:
   if value is not None:clauses.append('f.'+col+'=:'+k);params[k]=value
  if q:clauses.append('(f.description ILIKE :q OR b.name ILIKE :q OR m.name ILIKE :q)');params['q']='%'+q[:150]+'%'
  join=' FROM procurement_fact f LEFT JOIN buyer b ON b.id=f.buyer_id JOIN source_observation s ON s.id=f.source_id LEFT JOIN municipality m ON m.ibge=f.municipality_ibge WHERE '+' AND '.join(clauses)
  total=ctx.db.one('SELECT count(*) AS n'+join,params)['n'];records=ctx.db.all('SELECT f.*,b.name AS buyer_name,b.cnpj,b.government_level,m.name AS municipality_name,s.url AS source_url,s.consulted_at'+join+' ORDER BY f.event_date DESC,f.id LIMIT :n OFFSET :off',params)
  return normalize({'records':records,'total':total,'offset':offset,'limit':limit,'dataset':dataset,'coverage_message':'Consulta parcial. Ausência de resultado não comprova ausência de compras.'})

 @app.get('/api/v1/sources')
 def source_list(ctx:Auth):return {'observations':ctx.db.all('SELECT id,provider,url,consulted_at,http_status,sha256,metadata,classification FROM source_observation ORDER BY consulted_at DESC LIMIT 100'),'coverage':ctx.db.all('SELECT * FROM coverage WHERE org_id=:o ORDER BY latest_success_at DESC NULLS LAST LIMIT 100',{'o':ctx.org_id}),'implemented':['IBGE · identidade municipal','PNCP · publicações, atualizações, itens, resultados, contratos e atas em recortes limitados','Compras.gov.br · CATMAT, CATSER e preços por código em consulta pontual'],'jobs':ctx.db.all("SELECT id,state,kind FROM job WHERE org_id=:o AND actor_id=:a AND state IN ('queued','running') ORDER BY created_at DESC LIMIT 10",{'o':ctx.org_id,'a':ctx.actor_id}),'pending':['PNCP · cobertura ampla e conciliação de todas as fases','Compras.gov.br · histórico amplo por município','INEP','SICONFI','Tribunais de Contas','Portais municipais','Execução financeira e consumo']}
 @app.get('/api/v1/coverage')
 def coverage(ctx:Auth):return {'records':ctx.db.all('SELECT * FROM coverage WHERE org_id=:o ORDER BY latest_success_at DESC NULLS LAST LIMIT 100',{'o':ctx.org_id})}
 @app.get('/api/v1/purchases/{fid}')
 def purchase_get(fid:UUID,ctx:Auth):
  r=ctx.db.one('SELECT f.*,b.name AS buyer_name,b.cnpj,b.government_level,m.name AS municipality_name,s.url AS source_url,s.consulted_at FROM procurement_fact f LEFT JOIN buyer b ON b.id=f.buyer_id JOIN source_observation s ON s.id=f.source_id LEFT JOIN municipality m ON m.ibge=f.municipality_ibge WHERE f.id=:i',{'i':fid})
  if not r:fail(404,'Esta compra não está disponível neste espaço.','NOT_FOUND')
  return normalize({'records':[r],'total':1})
 @app.post('/api/v1/sources/sync',status_code=202)
 def source_sync(body:SourceSync,background:BackgroundTasks,ctx:Auth,idempotency_key:str|None=Header(None)):
  args=body.model_dump();job=sources.enqueue(ctx,args,idempotency_key)
  if not job['duplicate']:background.add_task(sources.run_job,app.state.database,ctx.org_id,ctx.actor_id,str(job['id']))
  return job
 @app.get('/api/v1/jobs/{jid}')
 def job_get(jid:UUID,ctx:Auth):
  r=ctx.db.one('SELECT id,kind,state,result,error_code,created_at FROM job WHERE org_id=:o AND id=:i AND actor_id=:a',{'o':ctx.org_id,'i':jid,'a':ctx.actor_id})
  if not r:fail(404,'Esta consulta não está disponível neste espaço.')
  ctx.require('sources.sync');return r

 @app.get('/api/v1/watches')
 def watches(ctx:Auth):return {'records':ctx.db.all('SELECT * FROM watch WHERE org_id=:o AND actor_id=:a ORDER BY created_at DESC',{'o':ctx.org_id,'a':ctx.actor_id}),'automatic_notifications':False}
 @app.post('/api/v1/watches',status_code=201)
 def watch_create(body:WatchBody,ctx:Auth):
  ctx.require('watch');wid=identifier();ctx.db.execute('INSERT INTO watch(org_id,id,actor_id,query) VALUES (:o,:i,:a,CAST(:q AS jsonb))',{'o':ctx.org_id,'i':wid,'a':ctx.actor_id,'q':encoded(body.model_dump())});return {'id':wid,'query':body.query,'automatic_notifications':False}
 @app.delete('/api/v1/watches/{wid}')
 def watch_delete(wid:UUID,ctx:Auth):
  ctx.require('watch');result=ctx.db.execute('DELETE FROM watch WHERE org_id=:o AND id=:i AND actor_id=:a',{'o':ctx.org_id,'i':wid,'a':ctx.actor_id})
  if not result.rowcount:fail(404,'Este acompanhamento não está disponível.')
  return {'removed':True}
 @app.get('/api/v1/audit')
 def audit(ctx:Auth):return {'records':ctx.db.all('SELECT action,resource_id,metadata,created_at FROM audit_event WHERE org_id=:o AND actor_id=:a ORDER BY created_at DESC LIMIT 100',{'o':ctx.org_id,'a':ctx.actor_id})}
 app.include_router(opportunity_router)
 app.include_router(director_router)
 return app

app=create_app()
