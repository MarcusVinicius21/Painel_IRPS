from typing import Annotated
from datetime import date,timedelta
from uuid import UUID
from fastapi.responses import JSONResponse
from fastapi import APIRouter,Depends,Request,BackgroundTasks,Header,Query
from .security import authenticate,fail,PERMISSIONS
from .db import normalize
from .modality import reject_filter
from .opportunity_schemas import HistoricalScope,Advance,MunicipalGroup,OpportunityFilter,Equivalence,CanonicalProductReview,ViabilityReview,ScenarioFromOpportunity,OpportunityWatch,PHASES
from . import history,opportunities,opportunity_alerts,catalogue,coverage_inventory,campaign_audit

Auth=Annotated[object,Depends(authenticate,scope='function')]
router=APIRouter(prefix='/api/v1')

@router.get('/history-campaign/audit')
def history_campaign_audit(ctx:Auth,request:Request,start:date,end:date,municipalities:list[str]=Query(default=[]),
                           offset:int=Query(0,ge=0,le=100000),limit:int=Query(100,ge=1,le=1000)):
    if set(request.query_params)-{'start','end','municipalities','offset','limit'}:fail(422,'Confira os filtros da conciliação.')
    return campaign_audit.audit(ctx,start,end,municipalities,offset,limit)

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

@router.post('/catalogue-intelligent/reprocess')
def catalogue_reprocess(ctx:Auth,limit:int=Query(500,ge=1,le=500),offset:int=Query(0,ge=0,le=1000000)):
    return catalogue.reprocess(ctx,limit,offset)

@router.get('/catalogue-intelligent/candidates')
def catalogue_candidates(ctx:Auth,limit:int=Query(100,ge=1,le=100)):
    return catalogue.candidates(ctx,limit)

@router.post('/catalogue-intelligent/products',status_code=201)
def catalogue_product_create(body:CanonicalProductReview,ctx:Auth):
    return catalogue.create_product(ctx,body)

@router.get('/catalogue-intelligent/products')
def catalogue_products(ctx:Auth,phase:PHASES='homologado',start:date=date(2020,1,1),end:date=Query(default_factory=date.today),
                       municipalities:list[str]|None=Query(None)):
    if end<start or (end-start).days>3653:fail(422,'Escolha um período de até dez anos.')
    if municipalities is not None and len(municipalities)>118:fail(422,'Escolha até 118 municípios por consulta.')
    return catalogue.products(ctx,phase,start,end,municipalities)

@router.get('/catalogue-intelligent/products/{product_id}/history')
def catalogue_product_history(product_id:UUID,request:Request,ctx:Auth,phase:PHASES='homologado',
                              start:date=Query(default_factory=lambda:date.today()-timedelta(days=1826)),
                              end:date=Query(default_factory=date.today),
                              municipalities:list[str]=Query(default_factory=list)):
    reject_filter(request)
    if end<start or (end-start).days>1826:fail(422,'Escolha um período de até cinco anos.')
    if len(municipalities)>118:fail(422,'Escolha até 118 municípios por consulta.')
    return catalogue.product_history(ctx,product_id,phase,start,end,municipalities)

@router.get('/catalogue-intelligent/reference-prices')
def catalogue_reference_prices(ctx:Auth,kind:str,code:str,code_type:str='codigoItemCatalogo',
                               start:date=date(2025,1,1),end:date=Query(default_factory=date.today),
                               page:int=Query(1,ge=1,le=100)):
    result=catalogue.reference_prices(ctx,kind,code,code_type,start,end,page)
    if result.get('state')=='source_unavailable':
        if code_type=='codigoItemCatalogo' and ctx.db.one("SELECT to_regclass('price_monthly_snapshot') AS table_name")['table_name']:
            from .monthly_prices import query as monthly_query
            preserved=monthly_query(ctx,kind,code,start,end,page)
            if preserved['records']:
                return {**preserved,'state':'partial','source_error':result['source_error'],'fallback_from':'live_api',
                    'message':'Arquivo mensal preservado. A consulta online falhou; somente os meses importados aparecem.'}
        error=result['source_error'];status=429 if error['code'] in ('RATE_LIMIT','SOURCE_COOLDOWN') else 502
        headers={'Retry-After':str(error['retry_after'])} if error.get('retry_after') else {}
        return JSONResponse(result,status_code=status,headers=headers)
    return result


@router.get('/catalogue-intelligent/monthly-prices')
def monthly_reference_prices(ctx:Auth,kind:str,code:str,start:date,end:date,page:int=Query(1,ge=1,le=100000),cursor:str|None=Query(None,max_length=2048)):
    from .monthly_prices import query as monthly_query
    return monthly_query(ctx,kind,code,start,end,page,cursor)

@router.get('/catalogue-intelligent/consolidated-prices')
def consolidated_reference_prices(ctx:Auth,kind:str,code:str,start:date,end:date,page:int=Query(1,ge=1,le=100000),cursor:str|None=Query(None,max_length=2048),
                                  unit:str|None=Query(None,max_length=120),uasg:str|None=Query(None,max_length=12),municipality:str|None=Query(None,max_length=12),supplier:str|None=Query(None,max_length=14)):
    from .monthly_consolidated import query
    return query(ctx,kind,code,start,end,page,cursor,unit,uasg,municipality,supplier)

@router.get('/catalogue-intelligent/consolidated-prices-summary')
def consolidated_price_summary(ctx:Auth,start:date,end:date):
    from .monthly_consolidated import summary
    return summary(ctx,start,end)

@router.get('/coverage/inventory')
def coverage_inventory_get(ctx:Auth,start:date=date(2024,1,1),end:date=Query(default_factory=date.today),
                           municipalities:list[str]=Query(default_factory=list)):
    if len(municipalities)>118:fail(422,'Escolha até 118 municípios por consulta.')
    return coverage_inventory.inventory(ctx,start,end,municipalities)

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
