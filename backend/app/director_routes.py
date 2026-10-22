from typing import Annotated,Literal
from datetime import date
from uuid import UUID
from fastapi import APIRouter,Depends,Query,Request,Response
from .security import authenticate,fail
from .db import normalize
from . import national_catalogue,director,irp_documents,catalogue,irp_register,executive,director_progress,multi_studies,pdf_preview,draft_review
from .opportunity_schemas import PHASES
from .history_filters import HistoryFilters
from .modality import reject_filter

Auth=Annotated[object,Depends(authenticate,scope='function')]
router=APIRouter(prefix='/api/v1')

@router.post('/director/multi-studies',status_code=201)
def create_multi_study(body:multi_studies.MultiStudyWrite,ctx:Auth):return multi_studies.write(ctx,body)

@router.get('/director/multi-studies')
def multi_study_list(ctx:Auth,limit:int=Query(default=20,ge=1,le=100),offset:int=Query(default=0,ge=0)):
    return multi_studies.listing(ctx,limit,offset)

@router.get('/director/multi-studies/{sid}')
def multi_study(sid:UUID,ctx:Auth,revision:int|None=Query(default=None,ge=1)):
    return multi_studies.read(ctx,sid,revision)

@router.post('/director/multi-studies/{sid}/revisions',status_code=201)
def revise_multi_study(sid:UUID,body:multi_studies.MultiStudyRevision,ctx:Auth):return multi_studies.write(ctx,body,sid)

@router.get('/director/dashboard/{section}')
def dashboard(section:Literal['catalogue','history','operations'],ctx:Auth):
    return executive.section(ctx,section)

@router.post('/director/progress',status_code=201)
def progress_save(body:director_progress.Progress,ctx:Auth):return director_progress.save(ctx,body)

@router.post('/director/analyses',status_code=201)
def analysis_save(body:director_progress.AnalysisSave,ctx:Auth):return director_progress.save_analysis(ctx,body)

@router.get('/director/progress')
def progress_list(ctx:Auth):
    ctx.require('read')
    return normalize({'records':ctx.db.all('''SELECT id,payload->'form'->>'name' AS name,payload->>'purpose' AS purpose,created_at
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
def history(product_id:UUID,request:Request,ctx:Auth,phase:PHASES,start:date,end:date,municipalities:list[str]=Query(default_factory=list),
            provider:str|None=Query(None,min_length=1,max_length=80,pattern=r'^[A-Z][A-Z0-9_]*$'),only_comparable:bool=False):
    reject_filter(request)
    if end<start or (end-start).days>1826 or end>date.today():fail(422,'Escolha um período passado de até cinco anos.')
    if len(municipalities)>118:fail(422,'Escolha até 118 municípios por consulta.')
    p=director.get_product(ctx,product_id)
    if p['classification']!='official':fail(422,'Esta experiência usa somente histórico oficial.','DATASET_MISMATCH')
    data=catalogue.product_history(ctx,product_id,phase,start,end,municipalities,HistoryFilters(provider=provider,only_comparable=only_comparable))
    return {**data,'snapshot_sha256':director_progress.history_digest(data)}

@router.get('/director/products/{product_id}/similar')
def similar(product_id:UUID,ctx:Auth,offset:int=Query(0,ge=0,le=100),limit:int=Query(20,ge=1,le=20)):
    return catalogue.reviewed_similar(ctx,product_id,offset,limit)

@router.get('/director/history/{product_id}/filters')
def history_options(product_id:UUID,request:Request,ctx:Auth,phase:PHASES,start:date,end:date,municipalities:list[str]=Query(default_factory=list)):
    reject_filter(request)
    if end<start or (end-start).days>1826 or end>date.today():fail(422,'Escolha um período passado de até cinco anos.')
    if len(municipalities)>118:fail(422,'Escolha até 118 municípios por consulta.')
    if director.get_product(ctx,product_id)['classification']!='official':fail(422,'Esta experiência usa somente histórico oficial.','DATASET_MISMATCH')
    return catalogue.history_filter_options(ctx,product_id,phase,start,end,municipalities)


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


@router.get('/irp-drafts/{did}/pdf/{aid}')
def pdf_info(did:UUID,aid:UUID,request:Request,ctx:Auth):
    return pdf_preview.metadata(ctx,request.app.state.settings.runtime,did,aid)

@router.get('/irp-drafts/{did}/pdf/{aid}/pages/{number}')
def pdf_page(did:UUID,aid:UUID,number:int,request:Request,ctx:Auth):
    return Response(pdf_preview.page(ctx,request.app.state.settings.runtime,did,aid,number),media_type='image/png',headers={'Cache-Control':'no-store'})


@router.get('/irp-drafts/{did}/review')
def draft_review_state(did:UUID,ctx:Auth):return draft_review.state(ctx,did)

@router.post('/irp-drafts/{did}/review',status_code=201)
def draft_review_save(did:UUID,body:draft_review.ReviewEvent,ctx:Auth):return draft_review.save(ctx,did,body)

@router.get('/irp-drafts/{did}/compare/{other}')
def compare_drafts(did:UUID,other:UUID,ctx:Auth):return draft_review.compare(ctx,did,other)


@router.get('/director/studies/{sid}/register/evidence')
def register_evidence(sid:UUID,ctx:Auth):return irp_register.evidence(ctx,sid)


@router.get('/director/studies/{sid}/dossier/inventory')
def dossier_inventory(sid:UUID,ctx:Auth):
    from .dossier_inventory import inventory
    return inventory(ctx,sid)
