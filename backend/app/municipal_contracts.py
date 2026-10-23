"""CNPJ-scoped contract plans; municipal identity must be evidenced, not inferred from location."""
import hashlib
from datetime import date
from . import history
from .db import encoded,identifier
from .municipal_plan import evidenced_windows,missing_windows
from .opportunity_schemas import HistoricalScope


def create_contract_plan(ctx,body):
    ctx.require('sources.sync')
    if not isinstance(body,HistoricalScope) or body.contracts==body.contract_updates or any((body.publications,body.updates,body.items,body.results,body.atas,body.pca)):
        raise ValueError('Separe contratos, atualizações e as outras fases neste plano.')
    return create_organization_plan(ctx,body,'PNCP_CONTRATOS' if body.contracts else 'PNCP_CONTRATOS_ATUALIZACAO')


def create_ata_plan(ctx,body,*,updated=False):
    ctx.require('sources.sync')
    if not isinstance(body,HistoricalScope) or not body.atas or not body.organization_cnpjs or any((body.publications,body.updates,body.items,body.results,body.contracts,body.contract_updates,body.pca)):
        raise ValueError('Separe as atas e informe os órgãos municipais verificados.')
    return create_organization_plan(ctx,body,'PNCP_ATAS_ATUALIZACAO' if updated else 'PNCP_ATAS_PUBLICACAO')


def create_organization_plan(ctx,body,provider):
    ctx.require('sources.sync')
    if provider not in ('PNCP_CONTRATOS','PNCP_CONTRATOS_ATUALIZACAO','PNCP_ATAS_PUBLICACAO','PNCP_ATAS_ATUALIZACAO'):raise ValueError('Fonte não configurada.')
    contracts=provider.startswith('PNCP_CONTRATOS')
    known={r['ibge'] for r in ctx.db.all('SELECT ibge FROM municipality')}
    if set(body.municipalities)-known:raise ValueError('Município fora do cadastro verificado.')
    cnpjs=set(body.organization_cnpjs)
    verified={r['cnpj'] for r in ctx.db.all("""SELECT DISTINCT cnpj FROM buyer
        WHERE org_id=:o AND classification='official' AND government_level='M'
        AND municipality_ibge=ANY(:cities) AND cnpj=ANY(:cnpjs)""",
        {'o':ctx.org_id,'cities':body.municipalities,'cnpjs':list(cnpjs)})}
    if cnpjs!=verified:raise ValueError('Confira a identidade e a esfera municipal dos órgãos antes de coletar contratos.')
    scope=body.model_dump(mode='json');scope['municipalities'].sort();scope['organization_cnpjs']=sorted(cnpjs)
    scope['modalities']=[]  # The official contract endpoint has no modality filter.
    key=hashlib.sha256(encoded(scope if contracts else {'provider':provider,'scope':scope}).encode()).hexdigest()
    ctx.db.execute('SELECT pg_advisory_xact_lock(hashtextextended(:k,0))',{'k':ctx.org_id+':contract-plan:'+key})
    old=ctx.db.one("SELECT id FROM history_collection WHERE org_id=:o AND scope->'_campaign'->>'key'=:k",{'o':ctx.org_id,'k':key})
    if old:
        if provider=='PNCP_ATAS_PUBLICACAO':
            corrected=ctx.db.execute("""UPDATE history_collection SET scope=jsonb_set(scope,'{_campaign,period_basis}','\"validity_overlap\"'::jsonb)
                WHERE org_id=:o AND id=:i AND scope->'_campaign'->>'period_basis' IS DISTINCT FROM 'validity_overlap'""",{'o':ctx.org_id,'i':old['id']})
            if corrected.rowcount:ctx.audit('history.period_basis_corrected',str(old['id']),{'period_basis':'validity_overlap','requests_and_pages_preserved':True})
        changed=ctx.db.execute("""UPDATE history_collection SET scope=jsonb_set(scope,'{_campaign,include_contract_terms}',CAST(:enabled AS jsonb))
            WHERE org_id=:o AND id=:i AND NOT (scope->'_campaign' ? 'include_contract_terms')""",{'o':ctx.org_id,'i':old['id'],'enabled':encoded(contracts)})
        if changed.rowcount:ctx.audit('history.contract_terms_enabled',str(old['id']),{'existing_pages_preserved':True})
        return {'id':str(old['id']),'reused_plan':True}
    rows=ctx.db.all("""SELECT t.id,t.collection_id,t.provider,t.arguments,t.state,p.result,p.record_count,
        s.id AS source_id,s.sha256,s.consulted_at,s.http_status,s.classification AS source_classification
        FROM history_task t JOIN history_collection c ON c.id=t.collection_id AND c.org_id=t.org_id
        LEFT JOIN history_page p ON p.task_id=t.id AND p.org_id=t.org_id
        LEFT JOIN source_observation s ON s.id=p.source_id
        WHERE t.org_id=:o AND c.dataset='official' AND t.provider=:provider
        AND t.arguments->>'cnpj'=ANY(:cnpjs) AND t.arguments->>'start_date'<=:end AND t.arguments->>'end_date'>=:start
        ORDER BY t.collection_id,t.task_key LIMIT 50001""",
        {'o':ctx.org_id,'provider':provider,'cnpjs':list(cnpjs),'start':str(body.start),'end':str(body.end)})
    if len(rows)>50000:raise ValueError('Divida o período antes de conciliar os contratos.')
    reused=evidenced_windows(rows,provider,('cnpj',))
    scope['_campaign']={'key':key,'kind':provider,'reused_organization_windows':reused,
        'include_contract_terms':contracts,
        'period_basis':'validity_overlap' if provider=='PNCP_ATAS_PUBLICACAO' else 'source_update_filter' if provider.endswith('ATUALIZACAO') else 'source_publication_filter',
        'limitation':'Somente CNPJs municipais identificados. A data da consulta não comprova pagamento ou consumo.'}
    cid=identifier();ctx.db.execute('INSERT INTO history_collection(org_id,id,actor_id,scope) VALUES (:o,:i,:a,CAST(:s AS jsonb))',
        {'o':ctx.org_id,'i':cid,'a':ctx.actor_id,'s':encoded(scope)})
    count=0
    for cnpj in sorted(cnpjs):
        verified=[(date.fromisoformat(p['start']),date.fromisoformat(p['end'])) for p in reused if p['cnpj']==cnpj]
        for first,last in missing_windows(body.start,body.end,verified):
            history.queue(ctx,cid,provider,{'cnpj':cnpj,'start_date':str(first),'end_date':str(last),'page':1,'size':body.size});count+=1
    result={'id':cid,'reused_plan':False,'initial_tasks':count,'reused_windows':len(reused),'organization_cnpjs':sorted(cnpjs),'network_requests':0}
    ctx.audit('history.contracts_materialized' if contracts else 'history.atas_materialized',cid,result)
    return result


def create_linked_contract_plan(ctx,publication_ids):
    return create_linked_artifact_plan(ctx,publication_ids,'PNCP_CONTRATOS_COMPRA')


def create_linked_ata_plan(ctx,publication_ids):
    return create_linked_artifact_plan(ctx,publication_ids,'PNCP_ATAS')


def create_linked_artifact_plan(ctx,publication_ids,provider):
    ctx.require('sources.sync')
    if provider not in ('PNCP_CONTRATOS_COMPRA','PNCP_ATAS'):raise ValueError('Fonte não configurada.')
    contracts=provider=='PNCP_CONTRATOS_COMPRA'
    ids=sorted(set(str(i) for i in publication_ids))
    if not ids or len(ids)>2000 or len(ids)!=len(publication_ids):raise ValueError('Escolha de 1 a 2.000 publicações distintas.')
    parents=ctx.db.all("""SELECT f.id,f.event_date,f.municipality_ibge,b.cnpj FROM procurement_fact f
        JOIN buyer b ON b.id=f.buyer_id WHERE f.org_id=:o AND f.id=ANY(CAST(:ids AS uuid[]))
        AND f.classification='official' AND f.provider='PNCP' AND f.is_current
        AND b.classification='official' AND b.government_level='M' AND f.event_date IS NOT NULL""",{'o':ctx.org_id,'ids':ids})
    if len(parents)!=len(ids):raise ValueError('Confira versão, data e identidade municipal das publicações.')
    key=hashlib.sha256(encoded({'linked_contract_parents' if contracts else 'linked_ata_parents':ids}).encode()).hexdigest()
    ctx.db.execute('SELECT pg_advisory_xact_lock(hashtextextended(:k,0))',{'k':ctx.org_id+':linked-contract-plan:'+key})
    old=ctx.db.one("SELECT id FROM history_collection WHERE org_id=:o AND scope->'_campaign'->>'key'=:k",{'o':ctx.org_id,'k':key})
    if old:return {'id':str(old['id']),'reused_plan':True}
    body=HistoricalScope(municipalities=sorted({p['municipality_ibge'] for p in parents}),
        start=min(p['event_date'] for p in parents),end=max(p['event_date'] for p in parents),
        publications=False,items=False,results=False,contracts=contracts,atas=not contracts,
        organization_cnpjs=sorted({p['cnpj'] for p in parents}),size=20,max_pages=2000)
    scope=body.model_dump(mode='json');scope['modalities']=[]
    scope['_campaign']={'key':key,'kind':provider,'publication_ids':ids,'include_contract_terms':contracts,
        'period_basis':'publication_date_of_parent','limitation':'Vínculos de publicações já salvas; não comprova cobertura temporal de contratos.' if contracts else 'Atas de publicações já salvas; não comprova cobertura temporal de atas.'}
    cid=identifier();ctx.db.execute('INSERT INTO history_collection(org_id,id,actor_id,scope) VALUES (:o,:i,:a,CAST(:s AS jsonb))',
        {'o':ctx.org_id,'i':cid,'a':ctx.actor_id,'s':encoded(scope)})
    previous=ctx.db.all("SELECT DISTINCT arguments->>'procurement_id' AS parent,collection_id FROM history_task WHERE org_id=:o AND provider=:provider AND arguments->>'procurement_id'=ANY(:ids)",{'o':ctx.org_id,'ids':ids,'provider':provider})
    already={p['parent'] for p in previous}
    for pid in ids:
        if pid not in already:history.queue(ctx,cid,provider,{'procurement_id':pid,'page':1,'size':20})
    result={'id':cid,'reused_plan':False,'requested_parents':len(ids),'initial_tasks':len(ids)-len(already),
        'previously_queued_parents':len(already),'network_requests':0,'municipal_purchase_completeness':None}
    ctx.audit('history.linked_contracts_materialized' if contracts else 'history.linked_atas_materialized',cid,result)
    return result
