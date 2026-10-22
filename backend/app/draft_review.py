"""Internal review events, never legal approval and never mutable draft bodies."""
import hashlib
from uuid import UUID
from typing import Literal
from pydantic import Field
from .schemas import Strict
from .db import encoded,identifier,normalize
from .security import fail
from . import director


class ReviewEvent(Strict):
    expected_revision:int=Field(ge=0)
    context_sha256:str=Field(pattern=r'^[a-f0-9]{64}$')
    status:Literal['requested','changes_requested','reviewed_internal']
    note:str=Field(min_length=10,max_length=3000)


def state(ctx,did):
    draft=director.draft(ctx,did);request=draft['payload']['request']
    latest=ctx.db.one('''SELECT id FROM irp_draft WHERE org_id=:o AND study_id=:s
        AND payload->'request'->>'kind'=:k AND coalesce(payload->'request'->>'municipality_ibge','')=:m
        ORDER BY created_at DESC,id DESC LIMIT 1''',{'o':ctx.org_id,'s':draft['study_id'],'k':request['kind'],'m':request.get('municipality_ibge') or ''})
    rows=ctx.db.all('''SELECT r.id,r.revision,r.status,r.note,r.context_sha256,r.created_by,a.name AS created_by_name,r.created_at
        FROM irp_draft_review r JOIN actor a ON a.id=r.created_by
        WHERE r.org_id=:o AND r.draft_id=:d ORDER BY r.revision DESC LIMIT 101''',{'o':ctx.org_id,'d':did})
    last=rows[0] if rows else None;current=bool(not draft['stale'] and not draft['validation']['errors'])
    latest_kind=bool(latest and str(latest['id'])==str(did))
    digest=hashlib.sha256(encoded({'draft_id':str(did),'payload':draft['payload'],'validation':draft['validation']}).encode()).hexdigest()
    blocked=not current or bool(last and (not latest_kind or last['status']=='changes_requested'))
    return normalize({'draft_id':did,'revision':last['revision'] if last else 0,'status':last['status'] if last else 'not_requested',
        'context_sha256':digest,'context_current':current,'latest_for_kind':latest_kind,
        'export_blocked':blocked,'can_submit':current and latest_kind and (not last or last['status']=='reviewed_internal'),
        'can_decide':current and latest_kind and bool(last and last['status']=='requested'),
        'events':rows[:100],'history_truncated':len(rows)>100,'officially_approved':False,
        'notice':'Revisão interna não é aprovação jurídica, homologação, assinatura ou publicação.'})


def save(ctx,did,body):
    if body.status=='requested':ctx.require('document.write');ctx.require('scenario.write')
    else:ctx.require('document.review');ctx.require('scenario.review')
    ctx.db.execute('SELECT pg_advisory_xact_lock(hashtextextended(:k,0))',{'k':f'draft-review:{ctx.org_id}:{did}'})
    # The scenario row lock prevents an input change during the review transition.
    d=director.draft(ctx,did)
    from . import scenarios
    scenarios.get_scenario(ctx,d['payload']['scenario_id'],lock=True)
    current=state(ctx,did)
    if not current['context_current'] or not current['latest_for_kind'] or current['context_sha256']!=body.context_sha256:
        fail(409,'Esta minuta mudou ou é uma versão anterior. Confira a versão atual.','VERSION_CONFLICT')
    if body.expected_revision!=current['revision']:fail(409,'A revisão mudou. Abra o estado atual antes de registrar.','VERSION_CONFLICT')
    allowed={'not_requested':{'requested'},'requested':{'changes_requested','reviewed_internal'},'reviewed_internal':{'requested'},'changes_requested':set()}
    if body.status not in allowed[current['status']]:fail(422,'Esta transição de revisão não está disponível. Prepare nova minuta quando houver ajustes.','REVIEW_TRANSITION_INVALID')
    rid=identifier();revision=current['revision']+1
    previous=current['events'][0]['id'] if current['events'] else None
    ctx.db.execute('''INSERT INTO irp_draft_review(org_id,id,draft_id,revision,previous_id,status,note,context_sha256,created_by)
        VALUES (:o,:i,:d,:r,:p,:s,:n,:h,:a)''',{'o':ctx.org_id,'i':rid,'d':did,'r':revision,'p':previous,'s':body.status,'n':body.note,'h':body.context_sha256,'a':ctx.actor_id})
    ctx.audit('irp.draft_review_recorded',did,{'review_id':rid,'revision':revision,'state':body.status})
    return state(ctx,did)


def guard_export(ctx,did):
    if state(ctx,did)['export_blocked']:
        fail(409,'A minuta tem ajustes pendentes ou ficou desatualizada. Prepare a versão corrigida.','IRP_REVIEW_BLOCKED')


def compare(ctx,did,other_id):
    current=director.draft(ctx,did);other=director.draft(ctx,other_id)
    if current['study_id']!=other['study_id']:fail(422,'Compare minutas do mesmo estudo.')
    labels={'object':'Objeto','kind':'Tipo de documento','coherence_evidence':'Conferência técnica','coherence_confirmed':'Conferência registrada',
        'note':'Observações','procedure_reference':'Referência informada','deadline':'Prazo','delivery':'Entrega','municipality_ibge':'Município','scenario_revision':'Versão do cenário'}
    a=other['payload']['request'];b=current['payload']['request']
    return normalize({'draft_id':did,'compared_id':other_id,'differences':[{'field':k,'label':labels.get(k,k),'before':a.get(k),'after':b.get(k)} for k in sorted(set(a)|set(b)) if a.get(k)!=b.get(k)],'source_preserved':True})
