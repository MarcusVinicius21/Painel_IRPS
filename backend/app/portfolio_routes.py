from typing import Annotated,Literal
from fastapi import APIRouter,Depends,Query,Request
from .security import authenticate,fail
from . import portfolio
from uuid import UUID
from datetime import date
Auth=Annotated[object,Depends(authenticate,scope='function')]
router=APIRouter(prefix='/api/v1/portfolio')

@router.get('/municipalities')
def monitored_municipalities(ctx:Auth):
    from .monitoring import targets
    return targets(ctx)


@router.get('/groups')
def groups(ctx:Auth):return portfolio.groups(ctx)


@router.get('/codes')
def codes(request:Request,ctx:Auth,group:str=Query(pattern=r'^(0[1-9]|1[0-9]|20)$'),q:str=Query('',max_length=150),
        kind:Literal['CATMAT','CATSER']|None=None,active:bool|None=None,
        technical:Literal['DIRECT_TECHNICAL','NEEDS_TECH_REVIEW']|None=None,subgroup:str|None=Query(None,max_length=80),
        offset:int=Query(0,ge=0,le=500000),limit:int=Query(25,ge=1,le=50)):
    if set(request.query_params)-{'group','q','kind','active','technical','subgroup','offset','limit'}:fail(422,'Confira os filtros do portfólio.')
    return portfolio.codes(ctx,group,q,kind,active,technical,subgroup,offset,limit)


@router.get('/preferences')
def preferences(ctx:Auth):return portfolio.preference_get(ctx)


@router.post('/preferences',status_code=201)
def preferences_save(body:portfolio.Preference,ctx:Auth):return portfolio.preference_save(ctx,body)


@router.get('/enrichment/{snapshot}/{code}')
def enrichment(snapshot:UUID,code:str,ctx:Auth):
    from . import national_catalogue,catalogue_enrichment
    entry=national_catalogue.entry(ctx,snapshot,code)
    return catalogue_enrichment.fetch('item',kind=entry['kind'],code=entry['code'],official_description=entry['name'])


@router.get('/history')
def history(request:Request,ctx:Auth,group:str,start:date,end:date,phase:str,
        municipalities:list[str]=Query(default=[]),code:str|None=None,snapshot:UUID|None=None,
        buyer:str|None=Query(None,pattern=r'^\d{14}$'),provider:str|None=Query(None,pattern=r'^[A-Z][A-Z0-9_]{0,79}$'),
        offset:int=Query(0,ge=0,le=20000),limit:int=Query(25,ge=1,le=50),candidates:bool=True,suppliers_only:bool=False):
    if set(request.query_params)-{'group','start','end','phase','municipalities','code','snapshot','buyer','provider','offset','limit','candidates','suppliers_only'}:
        fail(422,'Confira os filtros das compras municipais.')
    from .portfolio_history import history as query
    return query(ctx,group=group,start=start,end=end,phase=phase,municipalities=municipalities,code=code,
        snapshot=str(snapshot) if snapshot else None,buyer=buyer,provider=provider,offset=offset,limit=limit,candidates=candidates,suppliers_only=suppliers_only)


@router.get('/coverage')
def coverage(ctx:Auth,start:date,end:date,municipalities:list[str]=Query(default=[])):
    from .portfolio_coverage import matrix
    return matrix(ctx,start,end,municipalities)


@router.get('/sources')
def sources(ctx:Auth):
    from .portfolio_sources import sources as query
    return query(ctx)


@router.get('/comparison')
def comparison(ctx:Auth,group:str,start:date,end:date,phase:str,municipalities:list[str]=Query(default=[]),
        code:str|None=None,snapshot:UUID|None=None,buyer:str|None=Query(None,pattern=r'^\d{14}$'),
        item_id:str|None=Query(None,max_length=200),item_version:int|None=Query(None,ge=1),
        offset:int=Query(0,ge=0,le=20000),limit:int=Query(25,ge=1,le=50)):
    from .portfolio_insights import compare
    result=compare(ctx,group=group,start=start,end=end,phase=phase,municipalities=municipalities,code=code,
        snapshot=str(snapshot) if snapshot else None,buyer=buyer,item_id=item_id,item_version=item_version)
    count=len(result['records']);result['records']=result['records'][offset:offset+limit]
    result.update(total=count,offset=offset,limit=limit,next_offset=offset+limit if offset+limit<count else None)
    # Supplier evidence follows only the identity groups on this page.
    ids={fid for row in result['records'] for fid in row['fact_ids']}
    result['supplier_evidence']=[s for s in result['supplier_evidence'] if s['fact_id'] in ids]
    return result
