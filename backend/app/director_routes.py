from typing import Annotated,Literal
from datetime import date
from uuid import UUID
from fastapi import APIRouter,Depends,Query,Request
from .security import authenticate,fail
from .db import normalize
from . import national_catalogue,director,irp_documents,catalogue,irp_register,executive,director_progress
from .opportunity_schemas import PHASES

Auth=Annotated[object,Depends(authenticate,scope='function')]
router=APIRouter(prefix='/api/v1')

@router.get('/director/dashboard/{section}')
def dashboard(section:Literal['catalogue','history','operations'],ctx:Auth):
    return executive.section(ctx,section)

@router.post('/director/progress',status_code=201)
def progress_save(body:director_progress.Progress,ctx:Auth):return director_progress.save(ctx,body)

@router.get('/director/progress')
def progress_list(ctx:Auth):
    ctx.require('read')
    return normalize({'records':ctx.db.all('''SELECT id,payload->'form'->>'name' AS name,created_at
        FROM director_progress p WHERE org_id=:o AND NOT EXISTS (SELECT 1 FROM director_progress n
          WHERE n.org_id=p.org_id AND n.supersedes_id=p.id) ORDER BY created_at DESC,id DESC LIMIT 50''',{'o':ctx.org_id})})

@router.get('/director/progress/{pid}')
def progress_get(pid:UUID,ctx:Auth):return director_progress.get(ctx,pid)

@router.get('/national-catalogue')
def search(ctx:Auth,q:str=Query('',max_length=200),kind:Literal['CATMAT','CATSER']|None=None,
           active:bool|None=None,group:str|None=Query(None,max_length=30),classification:str|None=Query(None,max_length=30),
           snapshot:UUID|None=None,offset:int=Query(0,ge=0,le=500000),limit:int=Query(25,ge=1,le=50)):
    return national_catalogue.search(ctx,q,kind,active,group,classification,snapshot,offset,limit)

@router.get('/national-catalogue/{snapshot}/{code}/links')
def links(snapshot:UUID,code:str,ctx:Auth):return director.links(ctx,snapshot,code)

@router.get('/national-catalogue/{snapshot}/{code}')
def catalogue_entry(snapshot:UUID,code:str,ctx:Auth):return national_catalogue.entry(ctx,snapshot,code)

@router.post('/national-catalogue/links',status_code=201)
def link(body:director.CatalogueLink,ctx:Auth):return director.link(ctx,body)

@router.get('/director/products')
def products(ctx:Auth):
    ctx.require('read')
    return normalize({'records':[{'id':p['id'],'name':p['name'],'unit':p['unit_key'],'classification':p['classification']} for p in catalogue.active_products(ctx) if p['classification']=='official']})

@router.get('/director/history/{product_id}')
def history(product_id:UUID,ctx:Auth,phase:PHASES,start:date,end:date,municipalities:list[str]=Query(default_factory=list)):
    if end<start or (end-start).days>1826 or end>date.today():fail(422,'Escolha um período passado de até cinco anos.')
    if len(municipalities)>118:fail(422,'Escolha até 118 municípios por consulta.')
    p=director.get_product(ctx,product_id)
    if p['classification']!='official':fail(422,'Esta experiência usa somente histórico oficial.','DATASET_MISMATCH')
    return catalogue.product_history(ctx,product_id,phase,start,end,municipalities)

@router.post('/director/studies',status_code=201)
def create_study(body:director.StudyCreate,ctx:Auth):return director.create_study(ctx,body)

@router.get('/director/studies')
def studies(ctx:Auth):
    ctx.require('read')
    return normalize({'records':ctx.db.all('SELECT id,scenario_id,scenario_revision,payload->>\'name\' AS name,created_at FROM director_study WHERE org_id=:o ORDER BY created_at DESC,id DESC LIMIT 50',{'o':ctx.org_id})})

@router.get('/director/studies/{sid}')
def study(sid:UUID,ctx:Auth):return director.study(ctx,sid)

@router.get('/director/studies/{sid}/register')
def register(sid:UUID,ctx:Auth):return irp_register.summary(ctx,sid)

@router.post('/director/studies/{sid}/operations',status_code=201)
def operation(sid:UUID,body:irp_register.Operation,ctx:Auth):return irp_register.save(ctx,sid,body)

@router.post('/director/studies/{sid}/dossier',status_code=201)
def dossier(sid:UUID,request:Request,ctx:Auth):return irp_documents.dossier(ctx,request.app.state.settings.runtime,sid)

@router.post('/director/studies/{sid}/drafts',status_code=201)
def draft_create(sid:UUID,body:director.DraftCreate,ctx:Auth):return director.create_draft(ctx,sid,body)

@router.get('/director/studies/{sid}/drafts')
def drafts(sid:UUID,ctx:Auth):
    director.study(ctx,sid)
    return normalize({'records':ctx.db.all('''SELECT id,created_at,payload->'request' AS request,validation
        FROM irp_draft WHERE org_id=:o AND study_id=:s ORDER BY created_at DESC,id DESC LIMIT 50''',{'o':ctx.org_id,'s':sid})})

@router.post('/director/studies/{sid}/consolidation/{fmt}',status_code=201)
def consolidation(sid:UUID,fmt:Literal['xlsx','pdf'],request:Request,ctx:Auth):
    return irp_documents.consolidation_export(ctx,request.app.state.settings.runtime,sid,fmt)

@router.get('/irp-drafts/{did}')
def draft(did:UUID,ctx:Auth):return director.draft(ctx,did)

@router.get('/irp-drafts/{did}/preview')
def draft_preview(did:UUID,ctx:Auth):
    row=director.draft(ctx,did)
    return {'sections':irp_documents.sections(row),'stale':row['stale'],'state':row['validation']['state']}

@router.post('/irp-drafts/{did}/exports/{fmt}',status_code=201)
def export(did:UUID,fmt:Literal['docx','pdf'],request:Request,ctx:Auth):
    return irp_documents.export(ctx,request.app.state.settings.runtime,did,fmt)
