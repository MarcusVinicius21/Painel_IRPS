from typing import Annotated
from uuid import UUID
from fastapi import APIRouter,Depends,Request,BackgroundTasks,Header,Query
from .security import authenticate,fail,PERMISSIONS
from .db import normalize
from .opportunity_schemas import HistoricalScope,Advance,MunicipalGroup,OpportunityFilter,Equivalence,ViabilityReview,ScenarioFromOpportunity,OpportunityWatch
from . import history,opportunities,opportunity_alerts

Auth=Annotated[object,Depends(authenticate,scope='function')]
router=APIRouter(prefix='/api/v1')

@router.get('/opportunity-options')
def options(ctx:Auth):
    ctx.require('read')
    return {'groups':ctx.db.all('SELECT id,name,municipalities FROM municipality_group WHERE org_id=:o ORDER BY name',{'o':ctx.org_id}),
        'buyers':ctx.db.all('SELECT id,name,cnpj,classification,municipality_ibge FROM buyer ORDER BY name LIMIT 1000'),
        'equivalences':ctx.db.all('SELECT * FROM opportunity_equivalence WHERE org_id=:o ORDER BY created_at DESC',{'o':ctx.org_id}),
        'categories':ctx.db.all("SELECT DISTINCT COALESCE(f.metadata->>'category',i.family) AS category,f.classification FROM procurement_fact f JOIN item_version i ON i.id=f.item_id AND i.version=f.item_version WHERE f.is_current ORDER BY category LIMIT 200"),
        'suppliers':ctx.db.all("SELECT DISTINCT metadata->'supplier'->>'cnpj' AS cnpj,metadata->'supplier'->>'name' AS name,classification FROM procurement_fact WHERE is_current AND metadata->'supplier'->>'cnpj' IS NOT NULL LIMIT 500")}

@router.post('/municipality-groups',status_code=201)
def group_create(body:MunicipalGroup,ctx:Auth):return opportunities.group_create(ctx,body)

@router.post('/opportunity-equivalences',status_code=201)
def equivalence_create(body:Equivalence,ctx:Auth):return opportunities.equivalence_create(ctx,body)

@router.post('/opportunities/query')
def query(body:OpportunityFilter,ctx:Auth):return opportunities.query(ctx,body)

@router.post('/opportunities/{key}/detail')
def detail(key:str,body:OpportunityFilter,ctx:Auth,offset:int=Query(0,ge=0,le=20000),limit:int=Query(100,ge=1,le=100)):
    return opportunities.detail(ctx,key,body,offset,limit)

@router.post('/opportunities/{key}/review',status_code=201)
def review(key:str,body:ViabilityReview,ctx:Auth):return opportunities.review_save(ctx,key,body)

@router.post('/opportunities/{key}/scenario',status_code=201)
def scenario(key:str,body:ScenarioFromOpportunity,ctx:Auth,idempotency_key:str|None=Header(None)):
    return opportunities.to_scenario(ctx,key,body,idempotency_key)

@router.get('/history-collections')
def collections(ctx:Auth):
    ctx.require('sources.sync')
    return {'records':ctx.db.all('SELECT * FROM history_collection WHERE org_id=:o ORDER BY created_at DESC LIMIT 100',{'o':ctx.org_id})}

@router.post('/history-collections',status_code=201)
def collection_create(body:HistoricalScope,ctx:Auth):return history.create(ctx,body)

@router.get('/history-collections/{cid}')
def collection_get(cid:UUID,ctx:Auth):return normalize(history.get(ctx,str(cid)))

def run_collection(database,org,actor,cid,pages):
    from .sources import job_context
    result=history.advance(database,org,actor,cid,pages)
    # Refresh only watches belonging to the authorized collector. Other actors refresh their own.
    with database.transaction(org,actor) as db:
        ctx=job_context(db,org,actor)
        if 'watch' in PERMISSIONS.get(ctx.role,set()):opportunity_alerts.refresh(ctx)
    return result

@router.post('/history-collections/{cid}/advance',status_code=202)
def advance(cid:UUID,body:Advance,ctx:Auth,request:Request,background:BackgroundTasks):
    c=history.get(ctx,str(cid))
    if c['dataset']!='official':fail(422,'Este conjunto fictício não consulta fontes externas.')
    background.add_task(run_collection,request.app.state.database,ctx.org_id,ctx.actor_id,str(cid),body.pages)
    return {'id':cid,'accepted':True,'page_budget':body.pages,'automatic_infinite_loop':False}

@router.post('/history-collections/{cid}/pause')
def pause(cid:UUID,ctx:Auth):return normalize(history.action(ctx,str(cid),'pause'))

@router.post('/history-collections/{cid}/resume')
def resume(cid:UUID,ctx:Auth):return normalize(history.action(ctx,str(cid),'resume'))

@router.post('/history-collections/{cid}/extend')
def extend(cid:UUID,ctx:Auth,max_pages:int=Query(ge=1,le=2000)):return normalize(history.action(ctx,str(cid),'extend',max_pages))

@router.get('/opportunity-alerts')
def alerts(ctx:Auth):return normalize(opportunity_alerts.listing(ctx))

@router.post('/opportunity-watches',status_code=201)
def watch_create(body:OpportunityWatch,ctx:Auth):return opportunity_alerts.watch_create(ctx,body)

@router.post('/opportunity-alerts/refresh')
def alerts_refresh(ctx:Auth):return opportunity_alerts.refresh(ctx)

@router.delete('/opportunity-watches/{wid}')
def watch_delete(wid:UUID,ctx:Auth):
    ctx.require('watch')
    result=ctx.db.execute('UPDATE opportunity_watch SET active=false WHERE org_id=:o AND id=:i AND actor_id=:a',{'o':ctx.org_id,'i':wid,'a':ctx.actor_id})
    if not result.rowcount:fail(404,'Este acompanhamento não está disponível.')
    return {'active':False,'history_preserved':True}
