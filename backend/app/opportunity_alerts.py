"""In-app, evidence-backed watches. No email, scheduler or future purchase promises."""
from .db import encoded,identifier,normalize
from .opportunity_schemas import OpportunityFilter
from .security import fail
from . import opportunities

def snapshot(row):
    return normalize({k:row.get(k) for k in ('id','event_identity','revision_hash','description','quantity','unit_price','amount','phase','event_date','source_id','source_url','metadata')})

def watch_create(ctx,body):
    ctx.require('watch');rows,_=opportunities.facts(ctx,body.filters)
    filters=body.filters.model_dump()
    if body.opportunity_key:
        detail=opportunities.detail(ctx,body.opportunity_key,body.filters)
        # Keep the reviewed members as id/version pairs. A plain item id could
        # accidentally include another version after the catalogue is revised.
        filters['opportunity_key']=body.opportunity_key
        members={(m['id'],m['version']) for m in detail['members']}
        rows=[r for r in rows if (r['item_id'],r['item_version']) in members]
    seen={r['event_identity']:snapshot(r) for r in rows}
    wid=identifier();ctx.db.execute('INSERT INTO opportunity_watch(org_id,id,actor_id,name,filters,seen) VALUES (:o,:i,:a,:n,CAST(:f AS jsonb),CAST(:s AS jsonb))',{'o':ctx.org_id,'i':wid,'a':ctx.actor_id,'n':body.name,'f':encoded(filters),'s':encoded(seen)})
    ctx.audit('opportunity.watch_created',wid,{'baseline_records':len(seen)})
    return {'id':wid,'baseline_records':len(seen),'alerts_created':0,'external_notifications':False}

def refresh(ctx):
    ctx.require('watch');count=0
    watches=ctx.db.all('SELECT * FROM opportunity_watch WHERE org_id=:o AND actor_id=:a AND active ORDER BY created_at LIMIT 50 FOR UPDATE',{'o':ctx.org_id,'a':ctx.actor_id})
    for watch in watches:
        saved=dict(watch['filters']);opportunity_key=saved.pop('opportunity_key',None)
        f=OpportunityFilter.model_validate(saved);rows,_=opportunities.facts(ctx,f)
        if opportunity_key:
            candidates,_,_=opportunities.build(ctx,f)
            candidate=next((entry for entry in candidates if entry['key']==opportunity_key),None)
            members={(m['id'],m['version']) for m in candidate['members']} if candidate else set()
            rows=[r for r in rows if (r['item_id'],r['item_version']) in members]
        # Retifications leaving a price/date filter still produce an alert for a previously seen event.
        if watch['seen']:
            changed=ctx.db.all('SELECT f.*,s.url AS source_url FROM procurement_fact f JOIN source_observation s ON s.id=f.source_id WHERE f.classification=:d AND f.is_current AND f.event_identity=ANY(:events)',{'d':f.dataset,'events':list(watch['seen'])})
            rows=list({r['event_identity']:r for r in [*rows,*changed]}.values())
        seen=dict(watch['seen'])
        for row in rows:
            previous=seen.get(row['event_identity']);after=snapshot(row)
            if previous and previous['revision_hash']==row['revision_hash']:continue
            kind='cancelled_result' if row['metadata'].get('cancelled') else 'changed' if previous else 'new_record'
            result=ctx.db.execute("INSERT INTO opportunity_alert(org_id,id,watch_id,actor_id,fact_id,event_identity,revision_hash,kind,before,after) VALUES (:o,:i,:w,:a,:f,:e,:h,:k,CAST(:b AS jsonb),CAST(:n AS jsonb)) ON CONFLICT(org_id,watch_id,event_identity,revision_hash) DO NOTHING",{'o':ctx.org_id,'i':identifier(),'w':watch['id'],'a':ctx.actor_id,'f':row['id'],'e':row['event_identity'],'h':row['revision_hash'],'k':kind,'b':encoded(previous) if previous else None,'n':encoded(after)})
            count+=result.rowcount;seen[row['event_identity']]=after
        if len(seen)>20000:fail(422,'Divida este acompanhamento em recortes menores.')
        ctx.db.execute('UPDATE opportunity_watch SET seen=CAST(:s AS jsonb) WHERE org_id=:o AND id=:i',{'o':ctx.org_id,'i':watch['id'],'s':encoded(seen)})
    return {'created':count,'external_notifications':False,'future_purchase_promised':False}

def listing(ctx):
    ctx.require('read')
    return {'watches':ctx.db.all('SELECT id,name,filters,active,created_at FROM opportunity_watch WHERE org_id=:o AND actor_id=:a ORDER BY created_at DESC',{'o':ctx.org_id,'a':ctx.actor_id}),
        'alerts':ctx.db.all('SELECT a.*,w.name AS watch_name FROM opportunity_alert a JOIN opportunity_watch w ON w.org_id=a.org_id AND w.id=a.watch_id WHERE a.org_id=:o AND a.actor_id=:actor ORDER BY a.created_at DESC LIMIT 100',{'o':ctx.org_id,'actor':ctx.actor_id}),
        'external_notifications':False,'message':'Mudanças em registros coletados. Nenhuma compra futura é garantida.'}
