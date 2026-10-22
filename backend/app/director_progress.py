"""Persist incomplete selection separately from studies, calculations and confirmations."""
from uuid import UUID
from datetime import date
from typing import Literal
from pydantic import Field,model_validator
from .history_filters import HistoryFilters
from .schemas import Strict,Code
from .db import encoded,identifier,normalize
from .security import fail
from . import national_catalogue,catalogue
import hashlib,json


class PartialItem(Strict):
    name:str=Field(default='',max_length=5000)
    specification:str=Field(default='',max_length=6000)
    category:Literal['material','veiculo','uniforme','saas','servico','obra']='material'
    classification:Literal['internal','synthetic']='internal'
    unit:str=Field(default='',max_length=120)
    quantity_step:str=Field(default='1',max_length=60)
    preliminary_target:str=Field(default='',max_length=60)
    target_justification:str=Field(default='',max_length=3000)
    technical_evidence:str=Field(default='',max_length=2000)
    service_period:str=Field(default='',max_length=200)
    quantity_basis:str=Field(default='',max_length=500)


class Progress(Strict):
    history_filters:HistoryFilters=Field(default_factory=HistoryFilters)
    supersedes_id:UUID|None=None
    snapshot_id:UUID|None=None
    code:str|None=Field(default=None,pattern=r'^\d{1,20}$')
    product_id:UUID|None=None
    municipalities:list[Code]=Field(default_factory=list,max_length=118)
    start:date
    end:date
    phase:str=Field(max_length=40)
    stage:Literal['selecao','historico','planejamento']='planejamento'
    form:PartialItem

    @model_validator(mode='after')
    def paired(self):
        if bool(self.snapshot_id)!=bool(self.code):raise ValueError('Código e versão devem permanecer juntos.')
        return self


class AnalysisSave(Progress):
    source_study_id:UUID|None=None
    source_progress_id:UUID|None=None
    expected_history_sha256:str|None=Field(default=None,pattern=r'^[a-f0-9]{64}$')


def history_digest(history):
    return hashlib.sha256(json.dumps(normalize(history),sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()


def save_analysis(ctx,body):
    ctx.require('scenario.write')
    from .opportunity_schemas import PHASES
    from typing import get_args
    if body.phase not in get_args(PHASES) or body.end<body.start or (body.end-body.start).days>1826 or body.end>date.today():
        fail(422,'Escolha uma situação válida e um período passado de até cinco anos.')
    if not body.product_id or not body.municipalities:
        fail(422,'Consulte um produto e escolha municípios antes de salvar a análise.','HISTORY_REQUIRED')
    cities=catalogue.validated_municipalities(ctx,body.municipalities)
    if body.source_study_id and body.source_progress_id:fail(422,'Escolha uma única versão de origem.')
    if body.source_study_id or body.source_progress_id:
        from .director import study
        source=study(ctx,body.source_study_id) if body.source_study_id else get(ctx,body.source_progress_id)
        p=source['payload'];history=p.get('history')
        expected=(str(p.get('product_id')),p.get('phase'),p.get('start'),p.get('end'),set(p.get('municipalities',[])),p.get('history_filters',{}).get('provider'),p.get('history_filters',{}).get('only_comparable',False),str(p.get('snapshot_id') or ''),p.get('code'))
        actual=(str(body.product_id),body.phase,body.start.isoformat(),body.end.isoformat(),set(cities),body.history_filters.provider,body.history_filters.only_comparable,str(body.snapshot_id or ''),body.code)
        if not history or expected!=actual:fail(409,'O recorte mudou. Consulte os dados novamente antes de salvar.','ANALYSIS_CONTEXT_CHANGED')
    else:
        from .director import get_product,links
        if get_product(ctx,body.product_id)['classification']!='official':
            fail(422,'Esta experiência usa somente histórico oficial.','DATASET_MISMATCH')
        if body.snapshot_id and not any(str(row['product_id'])==str(body.product_id) for row in links(ctx,body.snapshot_id,body.code)['records']):
            fail(422,'Confira o vínculo entre o código e o histórico antes de salvar.','CATALOGUE_LINK_REQUIRED')
        history=catalogue.product_history(ctx,body.product_id,body.phase,body.start,body.end,cities,body.history_filters)
        if not body.expected_history_sha256 or history_digest(history)!=body.expected_history_sha256:
            fail(409,'Os dados mudaram. Atualize o histórico e confira antes de salvar.','HISTORY_CHANGED')
    if not any((row.get('observed_records') or 0)>0 for row in history.get('municipalities',[])):
        fail(422,'Não há registros associados para preservar nesta análise.','HISTORY_REQUIRED')
    return save(ctx,body,analysis=history)


def get(ctx,pid):
    ctx.require('read')
    row=ctx.db.one('SELECT * FROM director_progress WHERE org_id=:o AND id=:i',{'o':ctx.org_id,'i':pid})
    if not row:fail(404,'Este rascunho não está disponível neste espaço.','NOT_FOUND')
    row['draft_only']=True;row['approval_implied']=False
    return normalize(row)


def save(ctx,body,analysis=None):
    ctx.require('scenario.write')
    if body.supersedes_id:
        get(ctx,body.supersedes_id)
        ctx.db.execute('SELECT pg_advisory_xact_lock(hashtextextended(:k,0))',{'k':str(ctx.org_id)+':progress:'+str(body.supersedes_id)})
        if ctx.db.one('SELECT 1 AS found FROM director_progress WHERE org_id=:o AND supersedes_id=:i',{'o':ctx.org_id,'i':body.supersedes_id}):
            fail(409,'O rascunho mudou. Reabra a versão atual antes de salvar.','VERSION_CONFLICT')
    entry=national_catalogue.entry(ctx,body.snapshot_id,body.code) if body.snapshot_id else None
    cities=catalogue.validated_municipalities(ctx,body.municipalities) if body.municipalities else []
    payload=body.model_dump(mode='json');payload.update({'municipalities':cities,'catalogue_entry':entry,
        'technical_confirmed':False,'v4_input_created':False,'confirmation_created':False})
    if analysis is not None:
        payload.update({'purpose':'historical_analysis','history':analysis,'history_sha256':history_digest(analysis),'stage':'historico'})
        payload['form'].update({'preliminary_target':'','target_justification':'','technical_evidence':''})
    pid=identifier();ctx.db.execute('''INSERT INTO director_progress(org_id,id,supersedes_id,payload,created_by)
        VALUES (:o,:i,:parent,CAST(:p AS jsonb),:a)''',{'o':ctx.org_id,'i':pid,'parent':body.supersedes_id,'p':encoded(payload),'a':ctx.actor_id})
    ctx.audit('director.progress_saved',pid,{'supersedes_id':str(body.supersedes_id) if body.supersedes_id else None,'draft_only':True})
    return get(ctx,pid)
