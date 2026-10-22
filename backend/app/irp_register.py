"""Internal receipt register. A municipal silence is never a confirmation or refusal."""
from datetime import date
from decimal import Decimal
from uuid import UUID
from typing import Literal
from pydantic import Field
from .schemas import Strict,Number,Code
from .db import encoded,identifier,normalize
from .security import fail
from . import director,documents,scenarios

STATES={'suggestion':{'proposed','reviewed'},'communication':{'prepared','sent','no_response'},
        'manifestation':{'received','in_review','confirmed','adjusted_confirmed','not_participating','invalid'},
        'external_act':{'evidence_recorded'}}

class Operation(Strict):
    kind: Literal['suggestion','communication','manifestation','external_act']
    municipality_ibge: Code
    expected_revision: int=Field(ge=0)
    scenario_revision: int=Field(ge=1)
    status: str=Field(max_length=40)
    quantity: Number|None=None
    document_id: UUID|None=None
    event_date: date|None=None
    deadline: date|None=None
    channel: str=Field(default='',max_length=200)
    protocol: str=Field(default='',max_length=200)
    responsible_name: str=Field(default='',max_length=180)
    competence_evidence: str=Field(default='',max_length=2000)
    note: str=Field(min_length=10,max_length=3000)
    external_act: Literal['publicidade','assinatura','edital','resultado','ata']|None=None


def save(ctx,sid,body):
    ctx.require('scenario.write');ctx.require('document.write')
    data=director.study(ctx,sid);scenario=scenarios.get_scenario(ctx,data['scenario_id'],lock=True)
    if not data['context_current'] or scenario['current_revision']!=data['scenario_revision'] or scenario['current_revision']!=body.scenario_revision:
        fail(409,'O cenário mudou. Prepare o estudo atual antes de registrar esta informação.','VERSION_CONFLICT')
    if body.municipality_ibge not in data['payload']['municipalities']:fail(422,'Escolha um município deste estudo.')
    if body.status not in STATES[body.kind]:fail(422,'A situação não corresponde ao tipo de registro.')
    if body.event_date and body.event_date>date.today():fail(422,'A data de um ato recebido ou realizado não pode estar no futuro.')
    needs_proof=(body.kind=='manifestation' or body.kind=='external_act' or body.kind=='communication' and body.status=='sent')
    if needs_proof and (not body.document_id or not body.event_date or not body.channel):
        fail(422,'Anexe o comprovante e informe a data e o canal formal.','FORMAL_EVIDENCE_REQUIRED')
    if body.kind=='external_act' and (not body.external_act or not body.protocol):fail(422,'Identifique o ato externo e seu protocolo.')
    if body.kind in ('communication','external_act') and body.quantity is not None:fail(422,'Comunicação ou ato externo não confirma quantidade.')
    reviewed=body.status in ('reviewed','confirmed','adjusted_confirmed','not_participating')
    doc=documents.get(ctx,body.document_id) if body.document_id else None
    if doc and doc['classification']=='business_private':fail(422,'Um documento comercial privado não pode fundamentar a manifestação pública.')
    if doc and (doc['classification']=='synthetic')!=(data['scenario']['classification']=='synthetic'):
        fail(422,'Mantenha comprovantes fictícios e documentos internos em estudos separados.','DATASET_MISMATCH')
    if reviewed:
        ctx.require('scenario.review');ctx.require('document.review')
        if body.kind=='manifestation' and (not doc or doc['review_state']!='reviewed' or len(body.competence_evidence)<10 or not body.responsible_name):
            fail(422,'Confira o documento recebido, a competência e a pessoa responsável antes de confirmar.','FORMAL_REVIEW_REQUIRED')
    if body.kind=='manifestation' and body.status in ('confirmed','adjusted_confirmed') and body.quantity is None:
        fail(422,'Informe a quantidade expressa no documento conferido.','FORMAL_QUANTITY_REQUIRED')
    if body.kind=='manifestation' and body.status=='not_participating' and body.quantity is not None:fail(422,'Uma recusa não informa quantidade confirmada.')
    if body.kind=='suggestion':
        if body.quantity is None:fail(422,'Informe a sugestão e sua justificativa.')
        if len(body.note.strip())<10:fail(422,'Justifique a quantidade proposta com pelo menos dez caracteres.','SUGGESTION_REASON_REQUIRED')
        step=Decimal(data['payload']['quantity_step'])
        if body.quantity % step != 0:
            fail(422,'A quantidade proposta deve respeitar a unidade e o passo definidos para este item.','SUGGESTION_STEP_MISMATCH')
    key=f'{ctx.org_id}:{sid}:{body.kind}:{body.municipality_ibge}'
    ctx.db.execute('SELECT pg_advisory_xact_lock(hashtextextended(:k,0))',{'k':key})
    old=ctx.db.one('SELECT id,revision FROM irp_operation WHERE org_id=:o AND study_id=:s AND kind=:k AND municipality_ibge=:c ORDER BY revision DESC LIMIT 1',
        {'o':ctx.org_id,'s':sid,'k':body.kind,'c':body.municipality_ibge})
    if (old['revision'] if old else 0)!=body.expected_revision:fail(409,'Este registro mudou. Abra a versão atual antes de salvar.','VERSION_CONFLICT')
    payload=body.model_dump(mode='json');payload.update({'unit':data['payload']['unit'],'item':data['payload']['planning_item'],
        'document_revision':doc['revision'] if doc else None,'document_sha256':doc['sha256'] if doc else None,
        'official_act_performed_by_irps':False})
    if body.kind=='suggestion':payload.update({'note':body.note.strip(),'quantity_step':data['payload']['quantity_step']})
    oid=identifier();revision=body.expected_revision+1
    ctx.db.execute('''INSERT INTO irp_operation(org_id,id,study_id,scenario_revision,kind,municipality_ibge,revision,supersedes_id,payload,created_by)
        VALUES (:o,:i,:s,:sv,:k,:c,:r,:previous,CAST(:p AS jsonb),:a)''',
        {'o':ctx.org_id,'i':oid,'s':sid,'sv':body.scenario_revision,'k':body.kind,'c':body.municipality_ibge,'r':revision,
         'previous':old['id'] if old else None,'p':encoded(payload),'a':ctx.actor_id})
    ctx.audit('irp.'+body.kind+'_recorded',oid,{'study':str(sid),'revision':revision,'status':body.status,'scenario_revision':body.scenario_revision})
    return {'id':oid,'revision':revision,'payload':payload}


def summary(ctx,sid):
    data=director.study(ctx,sid)
    rows=ctx.db.all('''SELECT DISTINCT ON(kind,municipality_ibge) id,kind,municipality_ibge,revision,scenario_revision,payload,created_by,(SELECT name FROM actor WHERE actor.id=irp_operation.created_by) AS created_by_name,created_at
        FROM irp_operation WHERE org_id=:o AND study_id=:s ORDER BY kind,municipality_ibge,revision DESC''',{'o':ctx.org_id,'s':sid})
    indexed={(r['kind'],r['municipality_ibge']):r for r in rows};cities=[]
    for code in data['payload']['municipalities']:
        suggestion=indexed.get(('suggestion',code));manifest=indexed.get(('manifestation',code));communication=indexed.get(('communication',code))
        valid=data['context_current']
        if manifest and manifest['payload'].get('document_id'):
            current=ctx.db.one('SELECT review_state,revision FROM extracted_document WHERE org_id=:o AND document_id=:d ORDER BY revision DESC LIMIT 1',{'o':ctx.org_id,'d':manifest['payload']['document_id']})
            valid=valid and bool(current and current['review_state']=='reviewed' and current['revision']==manifest['payload']['document_revision'])
        confirmed=valid and manifest and manifest['payload']['status'] in ('confirmed','adjusted_confirmed')
        declined=bool(valid and manifest and manifest['payload']['status']=='not_participating')
        if manifest:
            display_state=manifest['payload']['status'] if valid else 'requires_reconfirmation'
        elif communication and communication['payload'].get('deadline') and communication['payload']['deadline']<date.today().isoformat():
            display_state='overdue'
        elif communication and communication['payload']['status']=='sent':
            display_state='awaiting_response'
        else:
            display_state='communication_pending'
        suggestion_current=bool(data['context_current'] and suggestion and suggestion['scenario_revision']==data['scenario_revision'])
        if suggestion_current and suggestion['payload'].get('document_id'):
            proof=ctx.db.one('SELECT revision FROM extracted_document WHERE org_id=:o AND document_id=:d ORDER BY revision DESC LIMIT 1',{'o':ctx.org_id,'d':suggestion['payload']['document_id']})
            suggestion_current=bool(proof and proof['revision']==suggestion['payload']['document_revision'])
        proposed=bool(suggestion_current and suggestion['payload']['status']=='reviewed')
        cities.append({'ibge':code,'suggested_quantity':suggestion['payload']['quantity'] if proposed else None,
            'suggestion_state':('requires_reconfirmation' if not suggestion_current else suggestion['payload']['status']) if suggestion else 'not_proposed',
            'suggestion_context_current':suggestion_current,
            'confirmed_quantity':manifest['payload']['quantity'] if confirmed else None,
            'manifestation_state':manifest['payload']['status'] if manifest else 'not_received',
            'confirmation_current':bool(confirmed),'non_participation_current':declined,'display_state':display_state,
            'communication_state':communication['payload']['status'] if communication else 'not_prepared',
            'unit':data['payload']['unit'],'suggestion':suggestion,'manifestation':manifest,'communication':communication})
    known=[Decimal(r['confirmed_quantity']) for r in cities if r['confirmed_quantity'] is not None]
    suggestions=[Decimal(r['suggested_quantity']) for r in cities if r['suggested_quantity'] is not None]
    declined=sum(r['non_participation_current'] for r in cities)
    resolved=len(known)+declined
    history=ctx.db.all('''SELECT id,kind,municipality_ibge,revision,scenario_revision,payload,created_by,(SELECT name FROM actor WHERE actor.id=irp_operation.created_by) AS created_by_name,created_at
        FROM irp_operation WHERE org_id=:o AND study_id=:s ORDER BY created_at DESC,id DESC LIMIT 501''',{'o':ctx.org_id,'s':sid})
    return normalize({'study_id':sid,'scenario_revision':data['scenario']['current_revision'],'context_current':data['context_current'],
        'municipalities':cities,'operations':rows,'history':history[:500],'history_truncated':len(history)>500,
        'confirmed_known_total':sum(known,Decimal(0)) if known else None,
        'suggested_known_total':sum(suggestions,Decimal(0)) if suggestions else None,
        'suggestion_pending_municipalities':len(cities)-len(suggestions),
        'all_municipalities_confirmed':len(known)==len(cities),'all_invitations_resolved':resolved==len(cities),
        'confirmed_municipalities':len(known),'non_participating_municipalities':declined,
        'consolidated_total':sum(known,Decimal(0)) if known and resolved==len(cities) else None,
        'pending_municipalities':len(cities)-resolved,'legal_procedure_approved':False,
        'notice':'Somente manifestações documentadas e conferidas entram no total conhecido. Pendências não valem zero. A competência e o rito dependem de validação institucional.'})


def evidence(ctx,sid):
    """Read-only provenance. Kept outside summary to preserve immutable draft snapshots."""
    ctx.require('document.read')
    register=summary(ctx,sid)
    ids=list({op['payload']['document_id'] for op in register['operations'] if op['payload'].get('document_id')})
    docs=ctx.db.all('''SELECT DISTINCT ON(d.id) d.id,d.filename,d.sha256,d.created_at AS uploaded_at,
        uploader.name AS uploaded_by_name,e.revision AS current_revision,e.review_state,
        reviewer.name AS reviewer_name,review_event.created_at AS reviewed_at
        FROM document d JOIN extracted_document e ON e.org_id=d.org_id AND e.document_id=d.id
        JOIN actor uploader ON uploader.id=d.created_by LEFT JOIN actor reviewer ON reviewer.id=e.reviewer
        LEFT JOIN LATERAL (SELECT a.created_at FROM audit_event a WHERE a.org_id=d.org_id
          AND a.resource_id=d.id::text AND a.action='document.reviewed'
          AND a.metadata->>'revision'=e.revision::text ORDER BY a.created_at DESC LIMIT 1) review_event ON true
        WHERE d.org_id=:o AND d.id::text=ANY(:ids) AND d.classification!='business_private'
        ORDER BY d.id,e.revision DESC''',{'o':ctx.org_id,'ids':ids}) if ids else []
    indexed={str(d['id']):d for d in docs};cities=[]
    for municipality in register['municipalities']:
        records=[]
        for op in register['operations']:
            if op['municipality_ibge']!=municipality['ibge']:continue
            payload=op['payload'];did=payload.get('document_id');doc=indexed.get(did)
            proof=None
            if doc:
                proof={**doc,'recorded_revision':payload.get('document_revision'),
                    'revision_matches':doc['current_revision']==payload.get('document_revision'),
                    'original_url':'/api/v1/documents/'+did+'/original'}
            records.append({'operation_id':op['id'],'kind':op['kind'],'revision':op['revision'],
                'recorded_by_name':op['created_by_name'],'recorded_at':op['created_at'],
                'channel':payload.get('channel'),'event_date':payload.get('event_date'),'protocol':payload.get('protocol'),
                'declared_responsible':payload.get('responsible_name'),'competence_evidence':payload.get('competence_evidence'),
                'document':proof,'qualification':'reviewed_document' if proof and proof['revision_matches'] and proof['review_state']=='reviewed' else 'review_pending' if proof else 'missing'})
        cities.append({'ibge':municipality['ibge'],'records':records})
    return normalize({'study_id':sid,'municipalities':cities,'history_truncated':register['history_truncated'],
        'notice':'Upload não comprova origem municipal. Canal, data e competência exigem conferência responsável.'})
