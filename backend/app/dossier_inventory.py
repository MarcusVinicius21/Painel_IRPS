"""Read-only dossier inventory. A reviewed internal draft is never an official final act."""
from . import director,draft_review,irp_register
from .db import normalize
from .security import fail


def inventory(ctx,sid):
    ctx.require('document.read');study=director.study(ctx,sid)
    candidates=ctx.db.all('SELECT id,payload,validation,created_at FROM irp_draft WHERE org_id=:o AND study_id=:s ORDER BY created_at DESC,id DESC LIMIT 501',{'o':ctx.org_id,'s':sid})
    if len(candidates)>500:fail(422,'Escolha um estudo com menos de 500 minutas para conferir o dossiê.')
    current={}
    for row in candidates:
        req=row['payload']['request'];current.setdefault((req['kind'],req.get('municipality_ibge') or ''),row)
    drafts=[]
    for row in current.values():
        revision=draft_review.state(ctx,row['id']);req=row['payload']['request']
        drafts.append({'id':row['id'],'kind':req['kind'],'municipality_ibge':req.get('municipality_ibge'),
            'created_at':row['created_at'],'scenario_revision':row['payload']['scenario_revision'],
            'state':'blocked' if revision['export_blocked'] else 'internal_review_recorded' if revision['status']=='reviewed_internal' else 'draft_needs_review',
            'included_if_exported_now':not revision['export_blocked'],'pending':row['validation']['pending'],
            'errors':row['validation']['errors'],'official_final':False})
    resources=[str(sid)]+[str(row['id']) for row in candidates]
    artifacts=ctx.db.all('''SELECT a.id,a.filename,a.media_type,a.revision,e.created_at,e.action
        FROM artifact a JOIN LATERAL (SELECT audit.created_at,audit.action FROM audit_event audit
          WHERE audit.org_id=a.org_id AND audit.metadata->>'artifact_id'=a.id::text
            AND audit.resource_id=ANY(:ids) AND audit.action IN ('irp.draft_exported','irp.dossier_exported','irp.consolidation_exported')
          ORDER BY audit.created_at DESC LIMIT 1) e ON true
        WHERE a.org_id=:o ORDER BY e.created_at DESC,a.id DESC LIMIT 101''',{'o':ctx.org_id,'ids':resources})
    for artifact in artifacts:artifact['download_url']='/api/v1/artifacts/'+str(artifact['id'])+'/download'
    evidence=irp_register.evidence(ctx,sid);support={}
    for municipality in evidence['municipalities']:
        for op in municipality['records']:
            if op['document']:
                d=op['document'];key=str(d['id'])
                record=support.setdefault(key,{'id':d['id'],'filename':d['filename'],'current_revision':d['current_revision'],
                    'review_state':d['review_state'],'original_url':d['original_url'],'links':[],'official_final':None})
                record['links'].append({'municipality_ibge':municipality['ibge'],'kind':op['kind'],'operation_revision':op['revision'],
                    'recorded_document_revision':d['recorded_revision'],'qualification':op['qualification']})
    return normalize({'study_id':sid,'scenario_revision':study['scenario']['current_revision'],
        'draft_versions_count':len(candidates),'current_drafts':drafts,'supporting_documents':list(support.values()),
        'generated_artifacts':artifacts[:100],'artifacts_truncated':len(artifacts)>100,
        'official_final_count':None,'dossier_plan':{'state':'prospective_inventory','eligible_drafts':sum(d['included_if_exported_now'] for d in drafts),
            'structured_reports':2,'original_documents_embedded':False,'private_quotations_included':False},
        'notice':'Minutas e relatórios internos não comprovam assinatura ou publicação. O índice do ZIP registra o conteúdo efetivamente exportado.'})
