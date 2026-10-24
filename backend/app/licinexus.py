"""A durable complement to the existing collector, retaining PNCP event identities."""
import json,hashlib
from datetime import datetime,timezone
from decimal import Decimal
from urllib.parse import urlsplit,parse_qs
from sqlalchemy import text
from .db import identifier,encoded,normalize
from .security import fail
from . import sources,history_sources,licinexus_runtime

class Capture:
    """Read an actual intermediary response, not a simulated HTTP request."""
    def __init__(self,responses):self.responses=responses
    def read(self,provider,url,params=None):
        if provider not in ('PNCP_ITENS','PNCP_RESULTADOS'):raise ValueError('Unapproved capture provider')
        expected=urlsplit(url)
        if expected.scheme!='https' or expected.netloc!='pncp.gov.br' or (params or {}).get('pagina',1)!=1:raise ValueError('Unapproved capture scope')
        for r in self.responses:
            actual=urlsplit(r['url']);raw=r['body'].encode('utf8')
            if actual.scheme!='https' or actual.netloc!='pncp.gov.br' or actual.path!=expected.path:continue
            if parse_qs(actual.query).get('pagina',['1'])!=['1']:continue
            if r['status'] not in (200,204) or len(raw)>2*1024*1024 or hashlib.sha256(raw).hexdigest()!=r['sha256']:raise ValueError('Unverified capture')
            value=json.loads(raw,parse_float=Decimal) if raw else None
            if value is not None and not isinstance(value,list):raise ValueError('Expected original list')
            return r['url'],r['status'],raw,value
        raise ValueError('No official response for the exact requested document')

def enqueue(ctx,fact_id,group,operation):
    ctx.require('sources.sync')
    if group not in {f'{i:02}' for i in range(1,21)} or operation not in ('items','results','documents','contract'):fail(422,'Confira a consulta complementar.')
    fact=ctx.db.one("SELECT f.*,b.government_level FROM procurement_fact f JOIN buyer b ON b.org_id=f.org_id AND b.id=f.buyer_id WHERE f.org_id=:o AND f.id=:i AND f.is_current AND f.classification='official'",{'o':ctx.org_id,'i':fact_id})
    if not fact:fail(404,'Este registro oficial não está disponível.')
    if fact['government_level']!='M' or not ctx.db.one('SELECT 1 FROM monitoring_target WHERE org_id=:o AND municipality_ibge=:m AND monitoring_enabled',{'o':ctx.org_id,'m':fact['municipality_ibge']}):fail(422,'Escolha um órgão municipal do monitoramento.')
    requested=str(fact_id)
    if operation in ('items','documents') and fact['provider']!='PNCP':
        fact=ctx.db.one("SELECT * FROM procurement_fact WHERE org_id=:o AND provider='PNCP' AND obligation_id=:p AND is_current AND classification='official'",{'o':ctx.org_id,'p':fact['obligation_id']})
        if not fact:fail(422,'A publicação original precisa estar disponível para esta consulta.')
    if operation=='results' and fact['provider']=='PNCP_RESULTADOS':
        fact=ctx.db.one("SELECT * FROM procurement_fact WHERE org_id=:o AND provider='PNCP_ITENS' AND item_id=:item AND is_current AND classification='official'",{'o':ctx.org_id,'item':fact['item_id']})
    if not fact or operation=='results' and fact['provider']!='PNCP_ITENS' or operation=='contract' and fact['provider']!='PNCP_CONTRATOS':fail(422,'Escolha um registro compatível com esta consulta.')
    args={'fact_id':str(fact['id']),'requested_fact_id':requested,'group':group,'operation':operation,'municipality_ibge':fact['municipality_ibge']}
    key=hashlib.sha256(encoded({'provider':fact['provider'],'identity':fact['event_identity'],'operation':operation}).encode()).hexdigest()
    ctx.db.execute('SELECT pg_advisory_xact_lock(hashtextextended(:k,0))',{'k':'licinexus:'+ctx.org_id+key})
    old=ctx.db.one("SELECT id,state FROM job WHERE org_id=:o AND actor_id=:a AND kind='licinexus.query' AND input_hash=:h AND created_at>now()-interval '1 day' ORDER BY created_at DESC LIMIT 1",{'o':ctx.org_id,'a':ctx.actor_id,'h':key})
    if old:return normalize({**old,'duplicate':True})
    if ctx.db.one("SELECT 1 FROM job WHERE org_id=:o AND kind='licinexus.query' AND state IN ('queued','running')",{'o':ctx.org_id}):fail(429,'Já há uma consulta complementar na fila. Aguarde sua conclusão.')
    jid=identifier();ctx.db.execute("INSERT INTO job(org_id,id,actor_id,kind,idempotency_key,input_hash,arguments,state) VALUES (:o,:i,:a,'licinexus.query',:ik,:k,CAST(:args AS jsonb),'queued')",{'o':ctx.org_id,'a':ctx.actor_id,'i':jid,'k':key,'ik':key+':'+datetime.now(timezone.utc).date().isoformat(),'args':encoded(args)})
    ctx.audit('licinexus.queued',jid,args)
    return {'id':jid,'state':'queued','duplicate':False}

def status(ctx):
    ctx.require('read')
    rows=ctx.db.all("SELECT id,state,arguments,result,error_code,created_at FROM job WHERE org_id=:o AND kind='licinexus.query' ORDER BY created_at DESC,id DESC LIMIT 20",{'o':ctx.org_id})
    return normalize({'installed':licinexus_runtime.installed(),'version':'0.2.1','jobs':rows,'official_origin':'PNCP',
        'limit':'Consultas pontuais; não comprovam cobertura histórica completa. Dependência Zod com alerta mitigada por isolamento e limites; sem serviço MCP público.'})

def perform(ctx,args,invoke=licinexus_runtime.invoke):
    fact=ctx.db.one("SELECT * FROM procurement_fact WHERE org_id=:o AND id=:i AND is_current AND classification='official'",{'o':ctx.org_id,'i':args['fact_id']})
    if not fact:raise ValueError('FACT_CHANGED')
    op=args['operation'];parent=fact
    if fact['provider']=='PNCP_RESULTADOS':
        parent=ctx.db.one('SELECT * FROM procurement_fact WHERE org_id=:o AND id=:i',{'o':ctx.org_id,'i':fact['metadata']['parent_id']})
    if op=='contract':
        identity=parent['metadata'].get('contract') or {};tool='get_contrato'
        query={'orgaoCnpj':identity.get('cnpj'),'ano':identity.get('year'),'sequencial':identity.get('sequence')}
    else:
        identity=parent['metadata'].get('purchase') or {}
        if not identity:raise ValueError('PURCHASE_IDENTITY_REQUIRED')
        query={'orgaoCnpj':identity['cnpj'],'ano':identity['year'],'sequencial':identity['sequence']}
        tool={'items':'list_licitacao_itens','results':'list_licitacao_resultados','documents':'list_licitacao_arquivos'}[op]
        if op=='results':
            if parent['provider']!='PNCP_ITENS':raise ValueError('ITEM_IDENTITY_REQUIRED')
            query['numeroItem']=identity['number']
    response,captures=invoke(tool,query)
    if response.get('error') or response.get('result',{}).get('isError'):
        last=next((r['status'] for r in reversed(captures) if r['status']>=400),None)
        if last in (429,503):raise sources.SourceFault('LICINEXUS_UPSTREAM',last,300)
        raise ValueError('LICINEXUS_SOURCE_ERROR')
    result={'tool':tool,'source':'PNCP','documents':[],'records':0,'new_revisions':0,'coverage':'partial','stock':None,'human_review_required':True}
    # Preserve trace even where the MCP schema discarded fields. Never promote
    # BrasilAPI fallback or an HTTP 404 to an official successful PNCP response.
    good=[r for r in captures if urlsplit(r['url']).netloc=='pncp.gov.br' and r['status'] in (200,204)]
    if not good:raise ValueError('NO_VERIFIED_PNCP_RESPONSE')
    if op in ('items','results'):
        transport=Capture(good)
        if op=='items':
            if parent['provider']!='PNCP':
                parent=ctx.db.one("SELECT * FROM procurement_fact WHERE org_id=:o AND provider='PNCP' AND obligation_id=:id AND is_current",{'o':ctx.org_id,'id':parent['obligation_id']})
            if not parent:raise ValueError('PARENT_PUBLICATION_REQUIRED')
            result.update(sources.sync(ctx,{'provider':'PNCP_ITENS','procurement_id':str(parent['id']),'page':1,'size':2000},transport))
        else:result.update(history_sources.results(ctx,{'procurement_id':str(parent['id'])},transport))
        result['documents']=[{'url':r['url'],'sha256':r['sha256'],'http_status':r['status']} for r in good]
    else:
        for r in good:
            body=r['body'].encode();data=json.loads(body) if body else None
            if hashlib.sha256(body).hexdigest()!=r['sha256']:raise ValueError('CAPTURE_HASH_MISMATCH')
            sid=history_sources.observe(ctx,'PNCP_ARQUIVOS' if op=='documents' else 'PNCP_CONTRATO_DETALHE',r['url'],r['status'],body,data or {},args,{'intermediary':'Licinexus MCP 0.2.1','purchase_or_contract':fact['obligation_id']})
            result['records']+=len(data) if isinstance(data,list) else int(bool(data))
            result['documents'].append({'source_id':str(sid),'url':r['url'],'sha256':r['sha256'],'http_status':r['status']})
        result['state']='observed_only'
    ctx.audit('licinexus.ingested',args['fact_id'],{'tool':tool,'new_revisions':result['new_revisions'],'source':'PNCP'})
    return normalize(result)

def tick(database,org,actor,invoke=licinexus_runtime.invoke):
    with database.engine.connect() as lease:
        key='irps-public-history-runner:'+org
        if not lease.execute(text('SELECT pg_try_advisory_lock(hashtextextended(:k,0))'),{'k':key}).scalar():lease.commit();return {'state':'busy'}
        lease.commit()
        try:
            with database.transaction(org,actor) as db:
                # Expired process leases are retryable; a crash never marks success.
                db.execute("UPDATE job SET state='queued',error_code='LEASE_RECOVERED' WHERE org_id=:o AND kind='licinexus.query' AND state='running' AND (result->>'lease_until')::timestamptz<now()",{'o':org})
                job=db.one("SELECT * FROM job WHERE org_id=:o AND kind='licinexus.query' AND (state='queued' OR state='retry_wait' AND (result->>'retry_at')::timestamptz<=now()) ORDER BY created_at,id LIMIT 1 FOR UPDATE",{'o':org})
                if not job:return {'state':'idle'}
                pause=db.one("SELECT 1 FROM source_backoff WHERE org_id=:o AND provider IN ('PNCP','PNCP_HOST') AND resume_after>now()",{'o':org})
                if pause:return {'state':'backoff'}
                attempts=int((job.get('result') or {}).get('attempts',0))+1
                db.execute("UPDATE job SET state='running',result=jsonb_build_object('lease_until',now()+interval '3 minutes','attempts',:n) WHERE org_id=:o AND id=:i",{'o':org,'i':job['id'],'n':attempts})
            try:
                with database.transaction(org,actor) as db:
                    ctx=sources.job_context(db,org,actor);result=perform(ctx,job['arguments'],invoke);result['attempts']=attempts
                    db.execute("UPDATE job SET state='completed',result=CAST(:r AS jsonb),error_code=NULL WHERE org_id=:o AND id=:i",{'o':org,'i':job['id'],'r':encoded(result)})
                return result
            except Exception as exc:
                with database.transaction(org,actor) as db:
                    retry=isinstance(exc,sources.SourceFault) and attempts<3
                    db.execute("UPDATE job SET state=:state,error_code=:e,result=jsonb_build_object('attempts',:n,'retry_at',now()+interval '5 minutes') WHERE org_id=:o AND id=:i",{'o':org,'i':job['id'],'e':exc.code if isinstance(exc,sources.SourceFault) else type(exc).__name__,'n':attempts,'state':'retry_wait' if retry else 'failed'})
                    if isinstance(exc,sources.SourceFault):
                        db.execute("INSERT INTO source_backoff(org_id,provider,resume_after) VALUES (:o,'PNCP_HOST',now()+interval '5 minutes') ON CONFLICT(org_id,provider) DO UPDATE SET resume_after=GREATEST(source_backoff.resume_after,EXCLUDED.resume_after)",{'o':org})
                return {'state':'failed','error_type':type(exc).__name__}
        finally:lease.execute(text('SELECT pg_advisory_unlock(hashtextextended(:k,0))'),{'k':key});lease.commit()

def schedule(ctx,city,start,end):
    """Discover one saved publication; text is priority only, never a code link."""
    if not licinexus_runtime.installed():return None
    if ctx.db.one("SELECT 1 FROM job WHERE org_id=:o AND kind='licinexus.query' AND state IN ('queued','running','retry_wait')",{'o':ctx.org_id}):return None
    rows=ctx.db.all("""SELECT f.id,f.description FROM procurement_fact f JOIN buyer b ON b.id=f.buyer_id AND b.org_id=f.org_id
     WHERE f.org_id=:o AND f.provider='PNCP' AND f.classification='official' AND f.is_current AND b.government_level='M'
     AND f.municipality_ibge=:city AND f.event_date BETWEEN :start AND :end
     AND NOT EXISTS(SELECT 1 FROM procurement_fact item WHERE item.org_id=f.org_id AND item.provider='PNCP_ITENS' AND item.obligation_id=f.obligation_id)
     AND NOT EXISTS(SELECT 1 FROM job j WHERE j.org_id=f.org_id AND j.kind='licinexus.query' AND j.arguments->>'fact_id'=f.id::text)
     ORDER BY f.event_date DESC,f.id LIMIT 100""",{'o':ctx.org_id,'city':city,'start':start,'end':end})
    from .portfolio_rules import fold,classify,DIRECT,REVIEW
    priorities=[('17',('INFORMATICA','COMPUTADOR','NOTEBOOK')),('15',('CAFE',)),('13',('MEDICAMENTO','HOSPITALAR')),('03',('UNIFORME ESCOLAR',)),('01',('AQUISICAO DE VEICULO','COMPRA DE VEICULO')),('02',('MATERIAL ESCOLAR',))]
    for r in rows:
        text=fold(r['description'])
        # Existing twenty-group rules are reusable for priority only. They do
        # not assert equivalence or attach a national catalogue code.
        classified=[x for kind in ('CATMAT','CATSER') for x in classify({'name':r['description'],'kind':kind}) if x['technical_status'] in (DIRECT,REVIEW)]
        if classified:return enqueue(ctx,str(r['id']),classified[0]['group_id'],'items')
        for group,terms in priorities:
            if any(term in text for term in terms):return enqueue(ctx,str(r['id']),group,'items')
    return None
