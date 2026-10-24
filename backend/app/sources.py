"""Only bounded GETs to fixed public endpoints. No keys or external credentials."""
import hashlib,json,re
from decimal import Decimal
from datetime import date,datetime,timezone
import httpx
from .db import identifier,encoded
from . import modality
from .source_retry import host_key
from .security import Context,fail

class SourceFault(Exception):
 def __init__(self,code,status=None,retry_after=60,evidence=None):self.code=code;self.status=status;self.retry_after=retry_after;self.evidence=evidence or {}

def documented_number(value):
 if value is None:return None
 try:
  d=Decimal(str(value))
  if not d.is_finite() or d<0 or d>Decimal('9999999999999999.99999999'):return None
  return str(d)
 except Exception:return None

def publication_timestamp(record):
 value=record.get('dataAtualizacaoGlobal') or record.get('dataAtualizacao')
 if not isinstance(value,str):return None
 try:return datetime.fromisoformat(value.replace('Z','+00:00'))
 except ValueError:return None

def older_publication(ctx,current,record,identity):
 if not current:return None
 source=ctx.db.one('SELECT body FROM source_observation WHERE id=:i',{'i':current['source_id']})
 try:
  payload=json.loads(source['body']) if source else {}
  previous=next((r for r in payload.get('data',[]) if r.get('numeroControlePNCP')==identity),{})
  before,after=publication_timestamp(previous),publication_timestamp(record)
  return after<before if before and after else None
 except (ValueError,TypeError,AttributeError):return None

def public_get(url,params=None,transport=None):
 try:
  with httpx.Client(timeout=httpx.Timeout(25,connect=8),follow_redirects=False,transport=transport,headers={'User-Agent':'IRPS-local-validation/0.1 (public-read-only)','Accept':'application/json'}) as client:
   with client.stream('GET',url,params=params) as response:
    resolved=str(response.url);chunks=[];size=0
    for chunk in response.iter_bytes():
     size+=len(chunk)
     if size>4*1024*1024:raise SourceFault('RESPONSE_LIMIT',response.status_code)
     chunks.append(chunk)
    content=b''.join(chunks)
    proof={'url':resolved,'http_status':response.status_code,'sha256':hashlib.sha256(content).hexdigest()}
    if response.status_code in (429,503):
     from email.utils import parsedate_to_datetime
     retry=response.headers.get('retry-after','60')
     try:delay=int(retry)
     except ValueError:
      try:delay=int((parsedate_to_datetime(retry)-datetime.now(timezone.utc)).total_seconds())
      except Exception:delay=60
     if delay>2147483647:raise SourceFault('INVALID_RETRY_AFTER',response.status_code,evidence=proof)
     raise SourceFault('RATE_LIMIT' if response.status_code==429 else 'SOURCE_UNAVAILABLE',response.status_code,max(60,delay),evidence=proof)
    if response.status_code not in (200,204):raise SourceFault('HTTP_'+str(response.status_code),response.status_code,evidence=proof)
    if response.status_code==204:return resolved,response.status_code,content,None
    try:data=json.loads(content,parse_float=Decimal)
    except (ValueError,UnicodeError):raise SourceFault('INVALID_SOURCE_FORMAT',response.status_code,evidence=proof)
    return resolved,response.status_code,content,data
 except httpx.HTTPError:raise SourceFault('SOURCE_CONNECTION') from None

def cached_get(ctx,provider,url,params=None,transport=None):
 resolved=str(httpx.Request('GET',url,params=params).url)
 def traced(result):
  ctx.last_source_response={'url':result[0],'http_status':result[1],'sha256':hashlib.sha256(result[2]).hexdigest()}
  return result
 if transport is not None:
  from .licinexus import Capture
  if isinstance(transport,Capture):return traced(transport.read(provider,url,params))
 if transport is None:
  cached=ctx.db.one("SELECT body,http_status FROM source_observation WHERE provider=:p AND url=:u AND classification='official' AND http_status IN (200,204) AND consulted_at>now()-interval '5 minutes' ORDER BY consulted_at DESC LIMIT 1",{'p':provider,'u':resolved})
  if cached:
   raw=cached['body'].encode()
   return traced((resolved,cached['http_status'],raw,None if cached['http_status']==204 else json.loads(raw,parse_float=Decimal)))
 return traced(public_get(url,params,transport))

def observe(ctx,provider,url,status,content,metadata):
 sha=hashlib.sha256(content).hexdigest();sid=identifier()
 ctx.db.execute("INSERT INTO source_observation(id,org_id,provider,url,http_status,sha256,body,metadata,classification) VALUES (:i,:o,:p,:u,:s,:h,:b,CAST(:m AS jsonb),'official') ON CONFLICT(provider,url,sha256) DO NOTHING",{'i':sid,'o':ctx.org_id,'p':provider,'u':url,'s':status,'h':sha,'b':content.decode('utf-8',errors='replace'),'m':encoded(metadata)})
 return ctx.db.one('SELECT id FROM source_observation WHERE provider=:p AND url=:u AND sha256=:h',{'p':provider,'u':url,'h':sha})['id']

def sync(ctx,args,transport=None):
 ctx.require('sources.sync');provider=args['provider'];meta={'scope':args,'public':True,'note':'Consulta pontual; não comprova cobertura histórica completa.'}
 if transport is not None:
  from .licinexus import Capture
  if isinstance(transport,Capture):meta.update(intermediary='Licinexus MCP 0.2.1',capture_ingestion=True,scope_note='size is a local safety bound; original request URL is preserved, no pagination coverage inferred')
 if provider=='IBGE':
  code=args.get('municipality_ibge')
  if not code or not code.isdigit() or len(code)!=7:fail(422,'Escolha um município pelo código IBGE.')
  url,status,content,data=cached_get(ctx,provider,'https://servicodados.ibge.gov.br/api/v1/localidades/municipios/'+code,transport=transport)
  if not isinstance(data,dict) or str(data.get('id'))!=code or not data.get('nome'):raise SourceFault('INVALID_MUNICIPALITY')
  uf=(data.get('microrregiao') or {}).get('mesorregiao',{}).get('UF') or (data.get('regiao-imediata') or {}).get('regiao-intermediaria',{}).get('UF',{})
  if not uf.get('sigla'):raise SourceFault('MISSING_UF')
  old=ctx.db.one('SELECT * FROM municipality WHERE ibge=:i',{'i':code})
  sid=observe(ctx,provider,url,status,content,meta)
  # Preserve previous identity when source contradicts it. Human resolution, not silent rewrite.
  conflict=bool(old and (old['name']!=data['nome'] or old['uf']!=uf['sigla']))
  if not old:ctx.db.execute('INSERT INTO municipality(ibge,name,uf,origin) VALUES (:i,:n,:u,:p)',{'i':code,'n':data['nome'],'u':uf['sigla'],'p':url})
  result={'provider':provider,'records':1,'pages_fetched':1,'expected_pages':1,'state':'complete','source_id':str(sid),'scope':{'municipality_ibge':code,'identity_only':True},'identity_conflict':conflict,'demographic_indicators_included':False}
 elif provider.startswith('COMPRAS_'):
  is_material=provider=='COMPRAS_CATMAT';route='/modulo-material/4_consultarItemMaterial' if is_material else '/modulo-servico/6_consultarItemServico'
  url,status,content,data=cached_get(ctx,provider,'https://dadosabertos.compras.gov.br'+route,{'pagina':args.get('page',1),'tamanhoPagina':args.get('size',10)},transport)
  if not isinstance(data,dict) or not isinstance(data.get('resultado'),list):raise SourceFault('INVALID_CATALOGUE_FORMAT')
  sid=observe(ctx,provider,url,status,content,meta)
  for record in data['resultado'][:args.get('size',10)]:
   code=record.get('codigoItem' if is_material else 'codigoServico');description=record.get('descricaoItem' if is_material else 'nomeServico')
   if code is None or not description:continue
   revision=hashlib.sha256(encoded(record).encode()).hexdigest()
   ctx.db.execute('INSERT INTO official_catalogue_entry(org_id,id,provider,code,revision_hash,description,unit,active,source_id,body) VALUES (:o,:i,:p,:code,:h,:d,NULL,:a,:s,CAST(:b AS jsonb)) ON CONFLICT(provider,code,revision_hash) DO NOTHING',{'o':ctx.org_id,'i':identifier(),'p':provider,'code':str(code),'h':revision,'d':description,'a':record.get('statusItem' if is_material else 'statusServico'),'s':sid,'b':encoded(record)})
  result={'provider':provider,'records':len(data['resultado']),'pages_fetched':1,'expected_pages':None,'state':'partial','source_id':str(sid),'scope':args,'catalogue_only':True,'procurement_quantities':False,'prices_collected':False}
 elif provider=='PNCP_ITENS':
  parent=ctx.db.one("SELECT f.*,s.body,s.sha256 AS publication_sha256,s.provider AS publication_provider FROM procurement_fact f JOIN source_observation s ON s.id=f.source_id WHERE f.id=:i AND f.classification='official' AND f.provider='PNCP'",{'i':args.get('procurement_id')})
  if not parent:fail(404,'Esta publicação oficial não está disponível.')
  original=json.loads(parent['body'],parse_float=Decimal)
  header=next((r for r in original.get('data',[]) if r.get('numeroControlePNCP')==parent['obligation_id']),None)
  if not header:fail(422,'Abra a publicação original antes de consultar os itens.')
  cnpj=(header.get('orgaoEntidade') or {}).get('cnpj');year=header.get('anoCompra');sequence=header.get('sequencialCompra')
  if not cnpj or not re.fullmatch(r'\d{14}',str(cnpj)) or not isinstance(year,int) or not isinstance(sequence,int):raise SourceFault('INVALID_PURCHASE_IDENTITY')
  url,status,content,data=cached_get(ctx,provider,f'https://pncp.gov.br/api/pncp/v1/orgaos/{cnpj}/compras/{year}/{sequence}/itens',{'pagina':args.get('page',1),'tamanhoPagina':args.get('size',10)},transport)
  if status==204 and data is None:data=[]
  if not isinstance(data,list) or len(data)>args.get('size',10) or any(not isinstance(r,dict) for r in data):raise SourceFault('INVALID_ITEM_FORMAT')
  numbers=[r.get('numeroItem') for r in data]
  if any(type(n) is not int or n<1 for n in numbers) or len(set(numbers))!=len(numbers):raise SourceFault('INVALID_ITEM_IDENTITY')
  sid=observe(ctx,provider,url,status,content,{**meta,'parent_id':str(parent['id'])});count=0
  for record in sorted(data,key=lambda r:r['numeroItem']):
   number=record['numeroItem'];description=record.get('descricao');unit=record.get('unidadeMedida')
   description=description.strip() if isinstance(description,str) and description.strip() else None
   unit=unit.strip() if isinstance(unit,str) and unit.strip() else None
   event=parent['obligation_id']+':item:'+str(number)
   item_id=f'pncp:{cnpj}:{year}:{sequence}:{number}'
   ctx.db.execute('SELECT pg_advisory_xact_lock(hashtextextended(:k,0))',{'k':item_id})
   item_modality=modality.inherit(parent,'PNCP_ITENS',modality.publication(header,parent['publication_provider'],parent['source_id'],parent['publication_sha256'],parent['revision_hash']))
   revision=hashlib.sha256(encoded({'record':record,'modality_provenance':item_modality}).encode()).hexdigest()
   if ctx.db.one("SELECT id FROM procurement_fact WHERE provider='PNCP_ITENS' AND event_identity=:e AND revision_hash=:h AND classification='official'",{'e':event,'h':revision}):continue
   current=ctx.db.one("SELECT id,org_id,revision_hash FROM procurement_fact WHERE provider='PNCP_ITENS' AND event_identity=:e AND classification='official' AND is_current",{'e':event})
   if current and (current['revision_hash']==revision or str(current['org_id'])!=ctx.org_id):continue
   version=None
   # No assumed package equivalence or demand rate; quantity step is deliberately conservative.
   step=Decimal('0.00000001')
   if unit and description:
    previous_item=ctx.db.one('SELECT * FROM item_version WHERE id=:i ORDER BY version DESC LIMIT 1',{'i':item_id})
    version=previous_item['version']+1 if previous_item else 1
    ctx.db.execute("INSERT INTO item_version(id,version,name,family,unit,step,classification) VALUES (:i,:v,:n,:f,:u,:s,'official')",{'i':item_id,'v':version,'n':description,'f':record.get('materialOuServicoNome') or 'Categoria não informada','u':unit,'s':step})
   if current:ctx.db.execute('UPDATE procurement_fact SET is_current=false WHERE id=:i AND org_id=:o',{'i':current['id'],'o':ctx.org_id})
   secret=record.get('orcamentoSigiloso') is True
   qty=documented_number(record.get('quantidade'));price=documented_number(record.get('valorUnitarioEstimado')) if not secret else None;amount=documented_number(record.get('valorTotal')) if not secret else None
   ctx.db.execute("INSERT INTO procurement_fact(id,org_id,classification,provider,event_identity,revision_hash,supersedes_id,source_id,buyer_id,municipality_ibge,item_id,item_version,description,unit,quantity,unit_price,amount,phase,event_date,obligation_id,metadata) VALUES (:i,:o,'official','PNCP_ITENS',:e,:h,:previous,:s,:b,:m,:item,:v,:d,:u,:q,:p,:amount,'publicado_estimado',:date,:ob,CAST(:meta AS jsonb))",{'i':identifier(),'o':ctx.org_id,'e':event,'h':revision,'previous':current['id'] if current else None,'s':sid,'b':parent['buyer_id'],'m':parent['municipality_ibge'],'item':item_id if version else None,'v':version,'d':description or 'Descrição não informada pela fonte','u':unit,'q':str(qty) if qty is not None else None,'p':str(price) if price is not None else None,'amount':str(amount) if amount is not None else None,'date':parent['event_date'],'ob':parent['obligation_id'],'meta':encoded({'record_level':'item','parent_id':str(parent['id']),'candidate_item_identity':item_id,'technical_identity_pending':not bool(version),'missing_unit':unit is None,'missing_description':description is None,'budget_secret':secret,'source_phase':record.get('situacaoCompraItemNome'),'quantity_is_consumption':False,'quantity_step_needs_review':True,'catalogue_code':record.get('catalogoCodigoItem'),'category':record.get('itemCategoriaNome') or record.get('materialOuServicoNome'),'modality':header.get('modalidadeId'),'modality_provenance':item_modality,'purchase':{'cnpj':cnpj,'year':year,'sequence':sequence,'number':number},'has_result':record.get('temResultado')})});count+=1
  result={'provider':provider,'records':len(data),'new_revisions':count,'pages_fetched':1,'expected_pages':None,'state':'partial','source_id':str(sid),'scope':args,'items_collected':True,'phase':'publicado_estimado','payments_collected':False}
 else:
  try:start=date.fromisoformat(args.get('start_date') or '');end=date.fromisoformat(args.get('end_date') or '')
  except ValueError:fail(422,'Informe o período da consulta.')
  if not 0<=(end-start).days<=6:fail(422,'Consulte até sete dias por vez nesta rodada.')
  params={'dataInicial':start.strftime('%Y%m%d'),'dataFinal':end.strftime('%Y%m%d'),'codigoModalidadeContratacao':args['modality'],'pagina':args['page'],'tamanhoPagina':args['size']}
  if args.get('municipality_ibge'):params['codigoMunicipioIbge']=args['municipality_ibge']
  if provider not in ('PNCP','PNCP_ATUALIZACAO'):fail(422,'Esta fonte ainda não está configurada para consulta.')
  endpoint='atualizacao' if provider=='PNCP_ATUALIZACAO' else 'publicacao'
  url,status,content,data=cached_get(ctx,provider,'https://pncp.gov.br/api/consulta/v1/contratacoes/'+endpoint,params,transport)
  if data is None:data={'data':[],'totalPaginas':0}
  if not isinstance(data,dict) or not isinstance(data.get('data'),list):raise SourceFault('INVALID_SOURCE_FORMAT')
  if len(data['data'])>args['size']:raise SourceFault('INVALID_PAGE_SIZE')
  if any(not isinstance(record,dict) for record in data['data']):raise SourceFault('INVALID_SOURCE_FORMAT')
  if args.get('municipality_ibge') and any(str((record.get('unidadeOrgao') or {}).get('codigoIbge',''))!=args['municipality_ibge'] for record in data['data']):
   raise SourceFault('INVALID_MUNICIPAL_SCOPE')
  sid=observe(ctx,provider,url,status,content,meta);count=0
  for record in sorted(data['data'],key=lambda row:str(row.get('numeroControlePNCP') or '')):
   identity=record.get('numeroControlePNCP');entity=record.get('orgaoEntidade') or {};unit=record.get('unidadeOrgao') or {}
   if not identity or not entity.get('cnpj'):continue
   ctx.db.execute('SELECT pg_advisory_xact_lock(hashtextextended(:event,0))',{'event':'PNCP:'+identity+':publication'})
   unit_code=str(unit.get('codigoUnidade',''));external=str(entity['cnpj'])+':'+unit_code
   code=str(unit.get('codigoIbge',''));known=ctx.db.one('SELECT ibge FROM municipality WHERE ibge=:i',{'i':code}) if len(code)==7 else None
   buyer=identifier();ctx.db.execute("INSERT INTO buyer(id,org_id,cnpj,name,unit_code,municipality_ibge,government_level,classification,external_identity) VALUES (:i,:o,:c,:n,:u,:m,:g,'official',:e) ON CONFLICT(classification,external_identity) DO NOTHING",{'i':buyer,'o':ctx.org_id,'c':entity['cnpj'],'n':entity.get('razaoSocial') or 'Nome não informado','u':unit_code,'m':code if known else None,'g':entity.get('esferaId'),'e':external})
   buyer=ctx.db.one("SELECT id FROM buyer WHERE classification='official' AND external_identity=:e",{'e':external})['id']
   revision=hashlib.sha256(encoded(record).encode()).hexdigest();event=identity+':publication'
   if ctx.db.one("SELECT id FROM procurement_fact WHERE provider='PNCP' AND event_identity=:e AND revision_hash=:h AND classification='official'",{'e':event,'h':revision}):continue
   current=ctx.db.one("SELECT id,revision_hash,source_id FROM procurement_fact WHERE provider='PNCP' AND event_identity=:e AND classification='official' AND is_current",{'e':event})
   if current and current['revision_hash']==revision:continue
   # A public revision created by another tenant cannot be overwritten by this worker.
   if current and not ctx.db.one('SELECT id FROM procurement_fact WHERE id=:i AND org_id=:o',{'i':current['id'],'o':ctx.org_id}):continue
   source_order=older_publication(ctx,current,record,identity);late=bool(source_order)
   if current and not late:ctx.db.execute("UPDATE procurement_fact SET is_current=false WHERE id=:i AND org_id=:o",{'i':current['id'],'o':ctx.org_id})
   amount=documented_number(record.get('valorTotalEstimado'));published=record.get('dataPublicacaoPncp')
   ctx.db.execute("""INSERT INTO procurement_fact(id,org_id,classification,provider,event_identity,revision_hash,
      is_current,supersedes_id,source_id,buyer_id,municipality_ibge,description,amount,phase,event_date,obligation_id,metadata)
      VALUES (:i,:o,'official','PNCP',:e,:h,:active,:previous,:s,:b,:m,:d,:a,'publicado_estimado',:date,:ob,CAST(:meta AS jsonb))
      ON CONFLICT(provider,event_identity,revision_hash,classification) DO NOTHING""",
      {'i':identifier(),'o':ctx.org_id,'e':event,'h':revision,'active':not late,'previous':current['id'] if current and not late else None,
       's':sid,'b':buyer,'m':code if known else None,'d':record.get('objetoCompra') or 'Objeto não informado',
       'a':str(amount) if amount is not None else None,'date':published[:10] if published else None,'ob':identity,
       'meta':encoded({'record_level':'publication','unit':unit,'entity':entity,'source_phase':record.get('situacaoCompraNome'),
          'source_updated_at':record.get('dataAtualizacaoGlobal') or record.get('dataAtualizacao'),
          'late_revision':late,'source_order_verified':source_order is not None,
          'source_order_basis':'source_timestamp' if source_order is not None else 'observed_order',
          'source_query_type':provider,'items_collected':False,'location_is_not_buyer_identity':True,
          'classification_pending':True,'origin_url':record.get('linkSistemaOrigem'),'modality':record.get('modalidadeId'),
          'modality_provenance':modality.publication(record,provider,sid,hashlib.sha256(content).hexdigest(),revision,args.get('modality')),
          'category':record.get('tipoInstrumentoConvocatorioNome'),
          'purchase':{'cnpj':entity['cnpj'],'year':record.get('anoCompra'),'sequence':record.get('sequencialCompra')}})});count+=1
  expected=data.get('totalPaginas');result={'provider':provider,'records':len(data['data']),'new_revisions':count,'pages_fetched':1,'expected_pages':expected,'expected_records':data.get('totalRegistros'),'state':'partial','source_id':str(sid),'scope':args,'items_collected':False,'payments_collected':False}
 cid=identifier();ctx.db.execute('INSERT INTO coverage(org_id,id,provider,scope,state,pages_fetched,expected_pages,record_count,latest_success_at) VALUES (:o,:i,:p,CAST(:s AS jsonb),:state,:pages,:expected,:n,now())',{'o':ctx.org_id,'i':cid,'p':provider,'s':encoded(result['scope']),'state':result['state'],'pages':result['pages_fetched'],'expected':result['expected_pages'],'n':result['records']})
 ctx.audit('source.consulted',sid,{'provider':provider,'records':result['records'],'state':result['state']});return result

def enqueue(ctx,args,key):
 ctx.require('sources.sync')
 if ctx.db.one('SELECT provider FROM source_backoff WHERE org_id=:o AND provider IN (:p,:host) AND resume_after>now()',{'o':ctx.org_id,'p':args['provider'],'host':host_key(args['provider'])}):fail(429,'A fonte pediu uma pausa. Tente novamente mais tarde.','SOURCE_BACKOFF')
 if not key or not 8<=len(key)<=120:fail(422,'A consulta precisa de uma identificação para evitar repetição.','IDEMPOTENCY_REQUIRED')
 h=hashlib.sha256(encoded(args).encode()).hexdigest();scope=ctx.org_id+':'+ctx.actor_id+':'+key
 ctx.db.execute('SELECT pg_advisory_xact_lock(hashtextextended(:k,0))',{'k':scope})
 old=ctx.db.one("SELECT id,input_hash,state FROM job WHERE org_id=:o AND actor_id=:a AND kind='source.sync' AND idempotency_key=:k",{'o':ctx.org_id,'a':ctx.actor_id,'k':key})
 if old:
  if old['input_hash']!=h:fail(409,'Esta identificação já foi usada para outra consulta.','IDEMPOTENCY_CONFLICT')
  return {'id':old['id'],'state':old['state'],'duplicate':True}
 jid=identifier();ctx.db.execute("INSERT INTO job(org_id,id,actor_id,kind,idempotency_key,input_hash,arguments,state) VALUES (:o,:i,:a,'source.sync',:k,:h,CAST(:args AS jsonb),'queued')",{'o':ctx.org_id,'i':jid,'a':ctx.actor_id,'k':key,'h':h,'args':encoded(args)});return {'id':jid,'state':'queued','duplicate':False}

def job_context(db,org,actor):
 row=db.one('SELECT m.role,m.active,a.name,a.active AS actor_active,o.kind,o.name AS org_name FROM membership m JOIN actor a ON a.id=m.actor_id JOIN organization o ON o.id=m.org_id WHERE m.org_id=:o AND m.actor_id=:a',{'o':org,'a':actor})
 if not row or not row['active'] or not row['actor_active']:fail(403,'Este acesso foi encerrado.','REVOKED')
 return Context(db,org,actor,row['role'],row['kind'],row['name'],row['org_name'],'worker')

def run_job(database,org,actor,jid):
 try:
  with database.transaction(org,actor) as db:
   ctx=job_context(db,org,actor);ctx.require('sources.sync');job=db.one("SELECT * FROM job WHERE org_id=:o AND id=:i AND kind='source.sync' AND state='queued' FOR UPDATE",{'o':org,'i':jid})
   if not job:return
   db.execute("UPDATE job SET state='running' WHERE org_id=:o AND id=:i",{'o':org,'i':jid});args=job['arguments']
  with database.transaction(org,actor) as db:
   ctx=job_context(db,org,actor);result=sync(ctx,args);db.execute("UPDATE job SET state='completed',result=CAST(:r AS jsonb) WHERE org_id=:o AND id=:i",{'o':org,'i':jid,'r':encoded(result)})
 except Exception as e:
  code=e.code if isinstance(e,SourceFault) else 'CONSULTATION_FAILED'
  with database.transaction(org,actor) as db:
   db.execute("UPDATE job SET state='failed',error_code=:c WHERE org_id=:o AND id=:i",{'o':org,'i':jid,'c':code})
   db.execute("INSERT INTO source_backoff(org_id,provider,resume_after) SELECT :o,arguments->>'provider',now()+make_interval(secs=>:seconds) FROM job WHERE org_id=:o AND id=:i ON CONFLICT(org_id,provider) DO UPDATE SET resume_after=EXCLUDED.resume_after",{'o':org,'i':jid,'seconds':e.retry_after if isinstance(e,SourceFault) else 60})
   db.execute("INSERT INTO coverage(org_id,id,provider,scope,state,pages_fetched,record_count,last_error_code) SELECT :o,:cid,arguments->>'provider',arguments,'unavailable',0,0,:c FROM job WHERE org_id=:o AND id=:i",{'o':org,'i':jid,'cid':identifier(),'c':code})
