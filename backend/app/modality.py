"""PNCP modality provenance v1. Never infer a code from request or free text."""
from copy import deepcopy
import re,hashlib
from uuid import UUID
from .db import encoded

VERSION=1
NAMESPACE='PNCP.contratacao.modalidadeId'
LIMITATION='Parte dos registros não informa a modalidade. O filtro permanece indisponível para não ocultá-los.'
PUBLICATIONS={'PNCP','PNCP_ATUALIZACAO'}
LINEAGE={'PNCP_ITENS':'PNCP','PNCP_RESULTADOS':'PNCP_ITENS'}

def unknown(reason):
    return {'version':VERSION,'state':'unknown','namespace':None,'code':None,'reason':reason}

def valid_code(value):
    # Official consultation OpenAPI: modalidadeId is integer/int64. No label guessed.
    return type(value) is int and 0<value<=9223372036854775807

def valid_id(value):
    try:UUID(str(value));return True
    except (ValueError,TypeError,AttributeError):return False

def valid_hash(value):return isinstance(value,str) and bool(re.fullmatch('[a-f0-9]{64}',value))

def publication(record,provider,source_id,source_sha256,revision_hash,requested_code=None):
    if provider not in PUBLICATIONS:return unknown('unsupported_provider')
    if 'modalidadeId' not in record or record['modalidadeId'] is None:return unknown('source_field_missing')
    if not valid_code(record['modalidadeId']):return unknown('source_field_invalid')
    if not valid_id(source_id) or not valid_hash(source_sha256) or not valid_hash(revision_hash) or not record.get('numeroControlePNCP') or hashlib.sha256(encoded(record).encode()).hexdigest()!=revision_hash:
        return unknown('source_proof_missing')
    return {'version':VERSION,'state':'known','namespace':NAMESPACE,'code':str(record['modalidadeId']),
        'evidence':{'provider':provider,'source_id':str(source_id),'source_sha256':source_sha256,
            'record_sha256':revision_hash,'record_identity':record['numeroControlePNCP'],'field':'modalidadeId','source_contract_version':'1.0',
            'request_matches':record['modalidadeId']==requested_code if valid_code(requested_code) else None},
        'lineage':[]}

def normalize(provider,metadata):
    if provider not in PUBLICATIONS|set(LINEAGE):return unknown('unsupported_provider')
    if not isinstance(metadata,dict):return unknown('metadata_not_object')
    proof=(metadata or {}).get('modality_provenance')
    if not isinstance(proof,dict):return unknown('legacy_without_proof')
    if type(proof.get('version')) is not int or proof.get('version')!=VERSION:return unknown('unsupported_version')
    if proof.get('state')=='unknown':return unknown(proof.get('reason') or 'source_field_missing')
    e=proof.get('evidence') or {};chain=proof.get('lineage')
    if not isinstance(e,dict):return unknown('source_proof_missing')
    if e.get('source_contract_version')!='1.0':return unknown('unsupported_source_contract_version')
    code=proof.get('code')
    if proof.get('state')!='known' or proof.get('namespace')!=NAMESPACE or not isinstance(code,str) or not re.fullmatch('[1-9][0-9]{0,18}',code) or not valid_code(int(code)):
        return unknown('invalid_normalized_value')
    if e.get('provider') not in PUBLICATIONS or e.get('field')!='modalidadeId' or not valid_id(e.get('source_id')) or not valid_hash(e.get('source_sha256')) or not valid_hash(e.get('record_sha256')) or not e.get('record_identity'):
        return unknown('source_proof_missing')
    expected=[] if provider in PUBLICATIONS else ['PNCP'] if provider=='PNCP_ITENS' else ['PNCP','PNCP_ITENS']
    if not isinstance(chain,list) or len(chain)!=len(expected):return unknown('lineage_missing')
    for step,parent_provider in zip(chain,expected):
        if not isinstance(step,dict) or step.get('provider')!=parent_provider or not valid_id(step.get('fact_id')) or not valid_hash(step.get('revision_hash')) or not valid_id(step.get('source_id')):
            return unknown('lineage_invalid')
    return deepcopy(proof)

def inherit(parent,child_provider,proof=None):
    if LINEAGE.get(child_provider)!=parent.get('provider'):return unknown('parent_provider_mismatch')
    value=normalize(parent['provider'],{'modality_provenance':proof} if proof is not None else parent.get('metadata'))
    if value['state']!='known':return unknown('parent_modality_unproven')
    if value['evidence']['record_identity']!=parent.get('obligation_id') or not valid_id(parent.get('id')) or not valid_hash(parent.get('revision_hash')) or not valid_id(parent.get('source_id')):
        return unknown('parent_identity_mismatch')
    value['lineage'].append({'provider':parent['provider'],'fact_id':str(parent['id']),
        'revision_hash':parent['revision_hash'],'source_id':str(parent['source_id'])})
    return value

def reject_filter(request):
    from .security import fail
    if set(request.query_params)&{'modality','modalities','modalidade','modalidades','modality_namespace','modality_code'}:
        fail(422,LIMITATION,'HISTORY_MODALITY_UNAVAILABLE')
