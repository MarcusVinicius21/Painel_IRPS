"""Persist incomplete selection separately from studies, calculations and confirmations."""
from uuid import UUID
from datetime import date
from typing import Literal
from pydantic import Field,model_validator
from .schemas import Strict,Code
from .db import encoded,identifier,normalize
from .security import fail
from . import national_catalogue,catalogue


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


def get(ctx,pid):
    ctx.require('read')
    row=ctx.db.one('SELECT * FROM director_progress WHERE org_id=:o AND id=:i',{'o':ctx.org_id,'i':pid})
    if not row:fail(404,'Este rascunho não está disponível neste espaço.','NOT_FOUND')
    row['draft_only']=True;row['approval_implied']=False
    return normalize(row)


def save(ctx,body):
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
    pid=identifier();ctx.db.execute('''INSERT INTO director_progress(org_id,id,supersedes_id,payload,created_by)
        VALUES (:o,:i,:parent,CAST(:p AS jsonb),:a)''',{'o':ctx.org_id,'i':pid,'parent':body.supersedes_id,'p':encoded(payload),'a':ctx.actor_id})
    ctx.audit('director.progress_saved',pid,{'supersedes_id':str(body.supersedes_id) if body.supersedes_id else None,'draft_only':True})
    return get(ctx,pid)
