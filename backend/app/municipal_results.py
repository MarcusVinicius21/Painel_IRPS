"""Results discovered from saved current items; parent publication dates are not result coverage."""
import hashlib
import re
from . import history
from .db import encoded,identifier
from .modality import COLLECTABLE_CODES
from .opportunity_schemas import HistoricalScope


def create_result_plan(ctx,municipalities,start,end,*,max_pages=2000):
    ctx.require('sources.sync')
    validated=HistoricalScope(municipalities=municipalities,start=start,end=end,
        modalities=sorted(COLLECTABLE_CODES),size=20,max_pages=max_pages)
    known={r['ibge'] for r in ctx.db.all('SELECT ibge FROM municipality')}
    if set(municipalities)-known:raise ValueError('Município fora do cadastro verificado.')
    scope=validated.model_dump(mode='json');scope['municipalities'].sort();scope['publications']=False
    key=hashlib.sha256(encoded({'kind':'saved_item_results','scope':scope}).encode()).hexdigest()
    ctx.db.execute('SELECT pg_advisory_xact_lock(hashtextextended(:k,0))',{'k':ctx.org_id+':results-plan:'+key})
    parents=ctx.db.all("""SELECT f.id,f.item_id,f.item_version,f.metadata FROM procurement_fact f
        JOIN source_observation s ON s.id=f.source_id
        WHERE f.org_id=:o AND f.classification='official' AND f.is_current AND f.provider='PNCP_ITENS'
        AND f.municipality_ibge=ANY(:cities) AND f.event_date BETWEEN :start AND :end
        AND s.classification='official' AND s.http_status=200 ORDER BY f.id LIMIT 2001""",
        {'o':ctx.org_id,'cities':municipalities,'start':validated.start,'end':validated.end})
    if len(parents)>2000:raise ValueError('Divida o período ou os municípios antes de planejar os resultados.')
    eligible=[p for p in parents if p['metadata'].get('has_result') is True and p['item_version']
              and re.fullmatch(r'pncp:\d{14}:\d{4}:\d+:\d+',p['item_id'] or '')]
    old=ctx.db.one("SELECT id FROM history_collection WHERE org_id=:o AND scope->'_campaign'->>'key'=:k",{'o':ctx.org_id,'k':key})
    cid=str(old['id']) if old else identifier()
    if not old:
        scope['_campaign']={'key':key,'kind':'saved_item_results','discovery_period_basis':'publication_date_of_parent_item',
            'limitation':'Somente itens correntes salvos com resultado sinalizado; não comprova cobertura temporal de homologações.'}
        ctx.db.execute('INSERT INTO history_collection(org_id,id,actor_id,scope) VALUES (:o,:i,:a,CAST(:s AS jsonb))',
            {'o':ctx.org_id,'i':cid,'a':ctx.actor_id,'s':encoded(scope)})
    ids=[str(p['id']) for p in eligible]
    rows=ctx.db.all("""SELECT t.collection_id,t.arguments,t.state,p.result,s.http_status,s.sha256,s.consulted_at,s.classification
        FROM history_task t LEFT JOIN history_page p ON p.task_id=t.id AND p.org_id=t.org_id
        LEFT JOIN source_observation s ON s.id=p.source_id
        WHERE t.org_id=:o AND t.provider='PNCP_RESULTADOS' AND t.arguments->>'procurement_id'=ANY(:ids)""",
        {'o':ctx.org_id,'ids':ids}) if ids else []
    proven={r['arguments']['procurement_id'] for r in rows if r['state']=='done' and r['http_status'] in (200,204)
            and r['classification']=='official' and r['sha256'] and r['consulted_at'] and r['result']
            and r['result'].get('expected_pages')==1 and r['result'].get('phase')=='homologado'}
    elsewhere={r['arguments']['procurement_id'] for r in rows if str(r['collection_id'])!=cid
               and r['arguments']['procurement_id'] not in proven}
    added=0
    for parent in eligible:
        pid=str(parent['id'])
        if pid in proven or pid in elsewhere:continue
        present=ctx.db.one("SELECT id FROM history_task WHERE org_id=:o AND collection_id=:c AND provider='PNCP_RESULTADOS' AND arguments->>'procurement_id'=:p",{'o':ctx.org_id,'c':cid,'p':pid})
        if present:continue
        history.queue(ctx,cid,'PNCP_RESULTADOS',{'procurement_id':pid});added+=1
    if added:ctx.db.execute("UPDATE history_collection SET state='ready',error_code=NULL WHERE org_id=:o AND id=:c AND state='completed'",{'o':ctx.org_id,'c':cid})
    result={'id':cid,'saved_current_items':len(parents),'eligible_items':len(eligible),'new_tasks':added,
        'evidenced_parents_reused':len(proven),'parents_in_other_queues':len(elsewhere),
        'items_without_confirmed_result_or_identity':len(parents)-len(eligible),
        'result_date_coverage':None,'municipal_purchase_completeness':None,'network_requests':0}
    ctx.audit('history.results_materialized',cid,result)
    return result
