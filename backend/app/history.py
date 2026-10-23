"""Durable, bounded PNCP pagination. Each successful page commits with its checkpoint."""
from datetime import date,datetime,timedelta,timezone
from decimal import Decimal
import hashlib,json,re,time
from .db import identifier,encoded
from .security import fail
from . import sources,history_sources,source_retry

def queue(ctx,cid,provider,args):
    key=provider+':'+hashlib.sha256(encoded(args).encode()).hexdigest()
    ctx.db.execute("INSERT INTO history_task(org_id,collection_id,id,task_key,provider,arguments) VALUES (:o,:c,:i,:k,:p,CAST(:a AS jsonb)) ON CONFLICT(org_id,collection_id,task_key) DO NOTHING",
        {'o':ctx.org_id,'c':cid,'i':identifier(),'k':key,'p':provider,'a':encoded(args)})

def get(ctx,cid):
    ctx.require('sources.sync')
    row=ctx.db.one('SELECT * FROM history_collection WHERE org_id=:o AND id=:i',{'o':ctx.org_id,'i':cid})
    if not row:fail(404,'Esta coleta não está disponível neste espaço.')
    row['tasks']=ctx.db.all('SELECT state,count(*) AS count FROM history_task WHERE org_id=:o AND collection_id=:c GROUP BY state',{'o':ctx.org_id,'c':cid})
    total=sum(r['count'] for r in row['tasks'])
    evidenced=ctx.db.one('''SELECT count(*) AS n FROM history_task t WHERE t.org_id=:o AND t.collection_id=:c
        AND t.state='done' AND EXISTS(SELECT 1 FROM history_page p JOIN source_observation s ON s.id=p.source_id
          WHERE p.org_id=t.org_id AND p.task_id=t.id AND s.http_status IN (200,204) AND s.classification='official')''',{'o':ctx.org_id,'c':cid})['n']
    row['execution']={'materialized_tasks':total,'evidenced_completed_tasks':evidenced,
        'request_plan_percent':str(Decimal(evidenced)*100/total) if total else None,
        'complete_known_plan':bool(total and evidenced==total and row['state']=='completed'),
        'denominator':'Tarefas materializadas neste plano. Pode aumentar com novas páginas e itens.',
        'municipal_purchase_completeness':None}
    row['recent_pages']=ctx.db.all('SELECT p.task_id,p.source_id,p.record_count,p.created_at,s.url,s.sha256 FROM history_page p JOIN source_observation s ON s.id=p.source_id WHERE p.org_id=:o AND p.collection_id=:c ORDER BY p.created_at DESC LIMIT 12',{'o':ctx.org_id,'c':cid})
    row['recent_errors']=ctx.db.all("SELECT created_at,metadata FROM audit_event WHERE org_id=:o AND resource_id=:c AND action='history.failed' ORDER BY created_at DESC LIMIT 20",{'o':ctx.org_id,'c':cid})
    row['coverage_message']='Conclusão significa somente o recorte e as rotas escolhidas, nunca todo o histórico municipal.'
    return row

def create(ctx,body):
    ctx.require('sources.sync')
    known={r['ibge'] for r in ctx.db.all('SELECT ibge FROM municipality')}
    if set(body.municipalities)-known:fail(422,'Confira os municípios antes de iniciar a coleta.')
    cid=identifier();scope=json.loads(body.model_dump_json())
    ctx.db.execute('INSERT INTO history_collection(org_id,id,actor_id,scope) VALUES (:o,:i,:a,CAST(:s AS jsonb))',{'o':ctx.org_id,'i':cid,'a':ctx.actor_id,'s':encoded(scope)})
    start=body.start
    while start<=body.end:
        end=min(start+timedelta(days=6),body.end)
        dates={'start_date':start.isoformat(),'end_date':end.isoformat(),'page':1,'size':body.size}
        if body.publications:
            for city in body.municipalities:
                for modality in body.modalities:queue(ctx,cid,'PNCP',{**dates,'municipality_ibge':city,'modality':modality,'provider':'PNCP'})
        if body.updates:
            for city in body.municipalities:
                for modality in body.modalities:queue(ctx,cid,'PNCP_ATUALIZACAO',{**dates,'municipality_ibge':city,'modality':modality,'provider':'PNCP_ATUALIZACAO'})
        if body.contracts:
            for cnpj in body.organization_cnpjs:queue(ctx,cid,'PNCP_CONTRATOS',{**dates,'cnpj':cnpj})
        if body.contract_updates:
            for cnpj in body.organization_cnpjs:queue(ctx,cid,'PNCP_CONTRATOS_ATUALIZACAO',{**dates,'cnpj':cnpj})
        if body.pca:
            for cnpj in body.organization_cnpjs:queue(ctx,cid,'PNCP_PCA',{'cnpj':cnpj,'year':start.year})
        for cnpj in body.organization_cnpjs:
            if body.atas:queue(ctx,cid,'PNCP_ATAS_ATUALIZACAO',{**dates,'cnpj':cnpj})
            if body.pca:queue(ctx,cid,'PNCP_PCA_ATUALIZACAO',{**dates,'cnpj':cnpj})
        start=end+timedelta(days=1)
    ctx.audit('history.created',cid,{'municipalities':len(body.municipalities),'network_requests':0})
    return get(ctx,cid)

def action(ctx,cid,action,max_pages=None):
    get(ctx,cid)
    if action=='pause':
        ctx.db.execute("UPDATE history_collection SET state='paused',error_code='USER_PAUSED',updated_at=now() WHERE org_id=:o AND id=:i",{'o':ctx.org_id,'i':cid})
    elif action=='extend':
        row=ctx.db.one('SELECT pages,scope FROM history_collection WHERE org_id=:o AND id=:i FOR UPDATE',{'o':ctx.org_id,'i':cid})
        if not max_pages or not row['pages']<max_pages<=2000:fail(422,'Defina um limite maior que as páginas já coletadas, até 2.000.')
        scope={**row['scope'],'max_pages':max_pages}
        ctx.db.execute("UPDATE history_collection SET scope=CAST(:s AS jsonb),state='ready',error_code=NULL WHERE org_id=:o AND id=:i",{'o':ctx.org_id,'i':cid,'s':encoded(scope)})
    else:
        row=ctx.db.one('SELECT resume_after FROM history_collection WHERE org_id=:o AND id=:i',{'o':ctx.org_id,'i':cid})
        if row['resume_after'] and row['resume_after']>datetime.now(timezone.utc):fail(429,'A fonte pediu uma pausa. Aguarde o horário informado.')
        ctx.db.execute("UPDATE history_collection SET state='ready',error_code=NULL WHERE org_id=:o AND id=:i",{'o':ctx.org_id,'i':cid})
    ctx.audit('history.'+action,cid)
    return get(ctx,cid)

def children(ctx,cid,scope,provider,args,result):
    observation=ctx.db.one('SELECT body FROM source_observation WHERE id=:s',{'s':result['source_id']})
    data=json.loads(observation['body']) if observation and observation['body'] else None
    if provider in ('PNCP','PNCP_ATUALIZACAO','PNCP_CONTRATOS','PNCP_CONTRATOS_ATUALIZACAO',
                    'PNCP_ATAS_ATUALIZACAO','PNCP_PCA_ATUALIZACAO'):
        total=result.get('expected_pages')
        if not isinstance(total,int) or total<0:raise sources.SourceFault('PAGINATION_UNVERIFIED')
        if total>10000:raise sources.SourceFault('SOURCE_PAGE_RANGE')
        if args['page']<total:queue(ctx,cid,provider,{**args,'page':args['page']+1})
        if provider in ('PNCP','PNCP_ATUALIZACAO'):
            for record in (data or {}).get('data',[]):
                parent=ctx.db.one("SELECT id FROM procurement_fact WHERE provider='PNCP' AND obligation_id=:i AND is_current AND classification='official'",{'i':record.get('numeroControlePNCP')})
                if not parent:continue
                if scope['items']:queue(ctx,cid,'PNCP_ITENS',{'provider':'PNCP_ITENS','procurement_id':str(parent['id']),'page':1,'size':scope['size']})
                entity=record.get('orgaoEntidade') or {};cnpj=entity.get('cnpj')
                valid_cnpj=bool(re.fullmatch(r'\d{14}',str(cnpj or '')))
                if valid_cnpj and scope.get('atas'):queue(ctx,cid,'PNCP_ATAS',{'procurement_id':str(parent['id'])})
                if valid_cnpj and scope.get('pca') and isinstance(record.get('anoCompra'),int):
                    queue(ctx,cid,'PNCP_PCA',{'cnpj':str(cnpj),'year':record['anoCompra']})
                if valid_cnpj and scope.get('atas'):
                    queue(ctx,cid,'PNCP_ATAS_ATUALIZACAO',{'cnpj':str(cnpj),'start_date':args['start_date'],
                        'end_date':args['end_date'],'page':1,'size':scope['size']})
                if valid_cnpj and scope.get('pca'):
                    queue(ctx,cid,'PNCP_PCA_ATUALIZACAO',{'cnpj':str(cnpj),'start_date':args['start_date'],
                        'end_date':args['end_date'],'page':1,'size':scope['size']})
    elif provider=='PNCP_ITENS':
        if not isinstance(data,list):raise sources.SourceFault('INVALID_ITEM_FORMAT')
        # An exact full page schedules one more request; no count is inferred from a full page.
        if len(data)==args['size']:queue(ctx,cid,provider,{**args,'page':args['page']+1})
        if scope['results']:
            parent=ctx.db.one('SELECT obligation_id FROM procurement_fact WHERE id=:i',{'i':args['procurement_id']})
            for record in data:
                if record.get('temResultado') is not True:continue
                item=ctx.db.one("SELECT id FROM procurement_fact WHERE provider='PNCP_ITENS' AND event_identity=:e AND is_current",{'e':parent['obligation_id']+':item:'+str(record.get('numeroItem'))})
                if item:queue(ctx,cid,'PNCP_RESULTADOS',{'procurement_id':str(item['id'])})

def advance(database,org,actor,cid,budget=1,transport=None):
    """No autonomous infinite loop. Scheduler/CLI explicitly requests at most three pages."""
    done=0
    for _ in range(min(budget,3)):
        with database.transaction(org,actor) as db:
            ctx=sources.job_context(db,org,actor);ctx.require('sources.sync')
            collection=db.one('SELECT * FROM history_collection WHERE org_id=:o AND id=:i FOR UPDATE',{'o':org,'i':cid})
            if not collection or collection['dataset']!='official':return {'pages':done}
            if collection['state'] in ('completed','limited') or (collection['state']=='paused' and (collection['error_code']=='USER_PAUSED' or collection['resume_after'] and collection['resume_after']>datetime.now(timezone.utc))):return {'pages':done}
            if collection['pages']>=collection['scope']['max_pages']:
                db.execute("UPDATE history_collection SET state='limited',updated_at=now() WHERE org_id=:o AND id=:i",{'o':org,'i':cid});return {'pages':done}
            if db.one("SELECT id FROM history_task WHERE org_id=:o AND collection_id=:c AND state='running' AND lease_until>now()",{'o':org,'c':cid}):return {'pages':done}
            db.execute("""UPDATE history_task SET state='blocked',lease_until=NULL,error_code='RETRY_EXHAUSTED'
                WHERE org_id=:o AND collection_id=:c AND attempts>=:max AND
                (state IN ('ready','failed','failed_retryable') OR (state='running' AND lease_until<now()))""",
                {'o':org,'c':cid,'max':source_retry.MAX_ATTEMPTS})
            task=db.one("""SELECT * FROM history_task WHERE org_id=:o AND collection_id=:c
                AND attempts<:max AND (state IN ('ready','failed','failed_retryable') OR (state='running' AND lease_until<now()))
                ORDER BY attempts,CASE provider WHEN 'PNCP' THEN 0 WHEN 'PNCP_ATUALIZACAO' THEN 0
                  WHEN 'PNCP_RESULTADOS' THEN 1 WHEN 'PNCP_ITENS' THEN 2 ELSE 3 END,
                  CASE arguments->>'modality' WHEN '6' THEN 0 WHEN '8' THEN 1 WHEN '9' THEN 2 WHEN '4' THEN 3 ELSE 4 END,task_key
                LIMIT 1 FOR UPDATE SKIP LOCKED""",{'o':org,'c':cid,'max':source_retry.MAX_ATTEMPTS})
            if not task:
                unfinished=db.one("SELECT count(*) AS n FROM history_task WHERE org_id=:o AND collection_id=:c AND state<>'done'",{'o':org,'c':cid})['n']
                db.execute("UPDATE history_collection SET state=:state,error_code=:error,updated_at=now() WHERE org_id=:o AND id=:i",{'o':org,'i':cid,'state':'paused' if unfinished else 'completed','error':'TASKS_REQUIRE_REVIEW' if unfinished else None})
                return {'pages':done,'blocked':bool(unfinished)}
            pause=db.one('SELECT max(resume_after) AS resume_after FROM source_backoff WHERE org_id=:o AND provider IN (:p,:host) AND resume_after>now()',{'o':org,'p':task['provider'],'host':source_retry.host_key(task['provider'])})
            pause=pause if pause and pause['resume_after'] else None
            if pause:
                db.execute("UPDATE history_collection SET state='paused',error_code='SOURCE_BACKOFF',resume_after=:r WHERE org_id=:o AND id=:i",{'o':org,'i':cid,'r':pause['resume_after']});return {'pages':done}
            db.execute("UPDATE history_task SET state='running',lease_until=now()+interval '3 minutes',attempts=attempts+1 WHERE org_id=:o AND id=:i",{'o':org,'i':task['id']})
            db.execute("UPDATE history_collection SET state='running',source_requests=source_requests+1,updated_at=now() WHERE org_id=:o AND id=:i",{'o':org,'i':cid})
        try:
            with database.transaction(org,actor) as db:
                ctx=sources.job_context(db,org,actor);ctx.require('sources.sync')
                args=task['arguments'];provider=task['provider']
                if provider in ('PNCP_CONTRATOS','PNCP_CONTRATOS_ATUALIZACAO'):
                    result=history_sources.contracts(ctx,args,transport,updated=provider.endswith('ATUALIZACAO'))
                elif provider=='PNCP_RESULTADOS':result=history_sources.results(ctx,args,transport)
                elif provider=='PNCP_ATAS':result=history_sources.atas(ctx,args,transport)
                elif provider=='PNCP_PCA':result=history_sources.pca(ctx,args,transport)
                elif provider in ('PNCP_ATAS_ATUALIZACAO','PNCP_PCA_ATUALIZACAO'):
                    result=history_sources.updated_index(ctx,provider,args,transport)
                else:result=sources.sync(ctx,args,transport)
                children(ctx,cid,collection['scope'],provider,args,result)
                db.execute('INSERT INTO history_page(org_id,collection_id,task_id,source_id,record_count,result) VALUES (:o,:c,:t,:s,:n,CAST(:r AS jsonb))',{'o':org,'c':cid,'t':task['id'],'s':result['source_id'],'n':result['records'],'r':encoded(result)})
                db.execute("UPDATE history_task SET state='done',lease_until=NULL,error_code=NULL WHERE org_id=:o AND id=:i",{'o':org,'i':task['id']})
                pending=db.one("SELECT count(*) AS n FROM history_task WHERE org_id=:o AND collection_id=:c AND state<>'done'",{'o':org,'c':cid})['n']
                next_state='completed' if not pending else 'limited' if collection['pages']+1>=collection['scope']['max_pages'] else 'ready'
                db.execute("UPDATE history_collection SET pages=pages+1,records=records+:n,state=CASE WHEN error_code='USER_PAUSED' THEN 'paused' ELSE :state END,error_code=CASE WHEN error_code='USER_PAUSED' THEN error_code ELSE NULL END,resume_after=NULL,updated_at=now() WHERE org_id=:o AND id=:i",{'o':org,'i':cid,'n':result['records'],'state':next_state})
                ctx.audit('history.page',cid,{'provider':provider,'records':result['records'],'source_id':result['source_id']})
            done+=1
            if transport is None and budget>1:time.sleep(1)
        except Exception as exc:
            code=exc.code if isinstance(exc,sources.SourceFault) else 'HISTORY_PAGE_FAILED'
            decision=source_retry.policy(code,exc.status if isinstance(exc,sources.SourceFault) else None,task['attempts']+1,exc.retry_after if isinstance(exc,sources.SourceFault) else 60)
            wait=decision['retry_after']
            response_evidence=(exc.evidence if isinstance(exc,sources.SourceFault) else {}) or getattr(ctx,'last_source_response',{})
            with database.transaction(org,actor) as db:
                db.execute("UPDATE history_task SET state=:state,lease_until=NULL,error_code=:e WHERE org_id=:o AND id=:i",{'o':org,'i':task['id'],'e':code,'state':decision['state']})
                db.execute("UPDATE history_collection SET state='paused',error_code=CASE WHEN error_code='USER_PAUSED' THEN error_code ELSE :e END,resume_after=now()+make_interval(secs=>:w),updated_at=now() WHERE org_id=:o AND id=:i",{'o':org,'i':cid,'e':code,'w':wait})
                if wait is not None:
                    db.execute("INSERT INTO source_backoff(org_id,provider,resume_after) VALUES (:o,:p,now()+make_interval(secs=>:w)) ON CONFLICT(org_id,provider) DO UPDATE SET resume_after=greatest(source_backoff.resume_after,EXCLUDED.resume_after)",{'o':org,'p':source_retry.host_key(task['provider']),'w':wait})
                ctx=sources.job_context(db,org,actor)
                ctx.audit('history.failed',cid,{'task_id':str(task['id']),'provider':task['provider'],'code':code,
                    'http_status':(exc.status if isinstance(exc,sources.SourceFault) else None) or response_evidence.get('http_status'),'attempt':task['attempts']+1,
                    **decision,'response_evidence':response_evidence})
            return {'pages':done,'paused':True,'error_code':code}
    return {'pages':done}
