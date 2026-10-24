from typing import Annotated,Literal
from fastapi import APIRouter,Depends,Query,Request
from .security import authenticate,fail
from . import portfolio
Auth=Annotated[object,Depends(authenticate,scope='function')]
router=APIRouter(prefix='/api/v1/portfolio')


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
