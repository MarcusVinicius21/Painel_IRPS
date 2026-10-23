"""Materialize item requests from saved official publications, without requerying their index."""
from collections import defaultdict
import hashlib
from . import history, sources
from .db import encoded, identifier
from .opportunity_schemas import HistoricalScope
from .modality import COLLECTABLE_CODES


def proven_item_parents(rows):
    groups=defaultdict(list)
    for row in rows:
        args=row['arguments']
        groups[(str(row['collection_id']),args.get('procurement_id'),args.get('size'))].append(row)
    proven=set()
    for (_,parent,size),pages in groups.items():
        if type(size) is not int or size<1:continue
        indexed={p['arguments'].get('page'):p for p in pages if p['state']=='done'
                 and p['http_status'] in (200,204) and p['classification']=='official'
                 and p['sha256'] and p['consulted_at']}
        if not indexed:continue
        last=max(indexed)
        if set(indexed)!=set(range(1,last+1)):continue
        if any(indexed[n]['record_count']!=size for n in range(1,last)):continue
        if not 0<=indexed[last]['record_count']<size:continue
        proven.add(parent)
    return proven


def create_item_plan(ctx,municipalities,start,end,*,size=20,max_pages=2000):
    ctx.require('sources.sync')
    # Reuse date, municipality syntax and budget validation; this plan queues
    # saved parents only, never publication requests or results.
    validated=HistoricalScope(municipalities=municipalities,start=start,end=end,
                              modalities=sorted(COLLECTABLE_CODES),size=size,max_pages=max_pages,items=True,results=False)
    scope=validated.model_dump(mode='json');scope['publications']=False
    scope['municipalities'].sort()
    known={r['ibge'] for r in ctx.db.all('SELECT ibge FROM municipality')}
    if set(municipalities)-known:raise ValueError('Município fora do cadastro verificado.')
    key=hashlib.sha256(encoded({'kind':'saved_publication_items','scope':scope}).encode()).hexdigest()
    ctx.db.execute('SELECT pg_advisory_xact_lock(hashtextextended(:k,0))',{'k':ctx.org_id+':items-plan:'+key})
    parents=ctx.db.all("""SELECT f.id,f.obligation_id FROM procurement_fact f
        JOIN source_observation s ON s.id=f.source_id
        WHERE f.org_id=:o AND f.classification='official' AND f.provider='PNCP' AND f.is_current
        AND f.municipality_ibge=ANY(:cities) AND f.event_date BETWEEN :start AND :end
        AND s.classification='official' AND s.http_status=200
        ORDER BY f.id LIMIT 2001""",{'o':ctx.org_id,'cities':municipalities,'start':validated.start,'end':validated.end})
    if len(parents)>2000:raise ValueError('Divida o período ou os municípios antes de planejar os itens.')
    old=ctx.db.one("SELECT id FROM history_collection WHERE org_id=:o AND scope->'_campaign'->>'key'=:k",{'o':ctx.org_id,'k':key})
    cid=str(old['id']) if old else identifier()
    if not old:
        scope['_campaign']={'key':key,'kind':'saved_publication_items',
            'limitation':'Somente publicações já armazenadas; o índice municipal pode estar incompleto.'}
        ctx.db.execute('INSERT INTO history_collection(org_id,id,actor_id,scope) VALUES (:o,:i,:a,CAST(:s AS jsonb))',
                       {'o':ctx.org_id,'i':cid,'a':ctx.actor_id,'s':encoded(scope)})
    ids=[str(p['id']) for p in parents]
    rows=ctx.db.all("""SELECT t.collection_id,t.arguments,t.state,p.record_count,
        s.http_status,s.classification,s.sha256,s.consulted_at FROM history_task t
        LEFT JOIN history_page p ON p.task_id=t.id AND p.org_id=t.org_id
        LEFT JOIN source_observation s ON s.id=p.source_id
        WHERE t.org_id=:o AND t.provider='PNCP_ITENS' AND t.arguments->>'procurement_id'=ANY(:ids)""",
        {'o':ctx.org_id,'ids':ids}) if ids else []
    proven=proven_item_parents(rows)
    elsewhere={r['arguments']['procurement_id'] for r in rows
               if str(r['collection_id'])!=cid and r['arguments']['procurement_id'] not in proven}
    added=0
    for parent in parents:
        pid=str(parent['id'])
        if pid in proven or pid in elsewhere:continue
        before=ctx.db.one('SELECT count(*) AS n FROM history_task WHERE org_id=:o AND collection_id=:c',{'o':ctx.org_id,'c':cid})['n']
        history.queue(ctx,cid,'PNCP_ITENS',{'provider':'PNCP_ITENS','procurement_id':pid,'page':1,'size':size})
        after=ctx.db.one('SELECT count(*) AS n FROM history_task WHERE org_id=:o AND collection_id=:c',{'o':ctx.org_id,'c':cid})['n']
        added+=after-before
    if added:
        ctx.db.execute("UPDATE history_collection SET state='ready',error_code=NULL WHERE org_id=:o AND id=:c AND state='completed'",{'o':ctx.org_id,'c':cid})
    result={'id':cid,'eligible_saved_publications':len(parents),'new_tasks':added,
            'evidenced_parents_reused':len(proven),'parents_in_other_queues':len(elsewhere),
            'municipal_purchase_completeness':None,'network_requests':0}
    ctx.audit('history.items_materialized',cid,result)
    return result
