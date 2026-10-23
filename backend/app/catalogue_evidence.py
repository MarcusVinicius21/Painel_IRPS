"""Exact PNCP catalogue declarations and explicit human review candidates.

An association to a taxonomy code never merges item specifications or units.
"""
import json,re,hashlib
from urllib.parse import urlparse
from . import catalogue,national_catalogue
from .security import fail
from .db import normalize

CATALOGUE_URL='https://catalogo.compras.gov.br/cnbs-web/busca'

def declaration(record):
    raw=record.get('catalogo');code=record.get('catalogoCodigoItem');kind=None
    if isinstance(raw,dict) and raw.get('id')==1 and raw.get('url')==CATALOGUE_URL:
        name=catalogue.fold(raw.get('nome',''))
        if name=='CATALOGO DO COMPRAS.GOV.BR':kind={'M':'CATMAT','S':'CATSER'}.get(record.get('materialOuServico'))
    code=str(code) if code is not None else None
    if code is not None and not re.fullmatch(r'\d{1,20}',code):code=None
    return {'catalogue_object':raw,'code':code,'namespace':kind,'namespace_verified':bool(kind and code),
        'basis':'Objeto catálogo CNBS, URL oficial e materialOuServico; não somente um número.'}

def original_record(fact):
    if not fact.get('source_sha256') or hashlib.sha256(fact['source_body'].encode()).hexdigest()!=fact['source_sha256']:return None
    try:body=json.loads(fact['source_body'])
    except (ValueError,TypeError):return None
    if not isinstance(body,list):return None
    number=(fact.get('metadata') or {}).get('purchase',{}).get('number')
    records=[r for r in body if isinstance(r,dict) and r.get('numeroItem')==number]
    if len(records)!=1:return None
    record=records[0]
    if record.get('descricao')!=fact['description'] or record.get('unidadeMedida')!=fact['unit']:return None
    return record

def facts(ctx,q='',limit=50):
    term=catalogue.fold(q)
    return ctx.db.all('''SELECT DISTINCT ON(f.item_id,f.item_version) f.*,s.url AS source_url,s.body AS source_body,
        s.sha256 AS source_sha256,s.consulted_at,b.name AS buyer_name,b.cnpj AS buyer_cnpj,b.government_level,
        m.name AS municipality_name
        FROM procurement_fact f JOIN source_observation s ON s.id=f.source_id
        LEFT JOIN buyer b ON b.id=f.buyer_id LEFT JOIN municipality m ON m.ibge=f.municipality_ibge
        WHERE f.is_current AND f.classification='official' AND s.classification='official' AND f.provider='PNCP_ITENS'
        AND translate(upper(f.description),'ÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇÑ','AAAAAEEEEIIIIOOOOOUUUUCN') ILIKE :q
        ORDER BY f.item_id,f.item_version,f.event_date DESC,f.id LIMIT :n''',{'q':'%'+term+'%','n':limit})

def automatic_checks(entry,fact,record):
    declared=declaration(record or {});norm=catalogue.normalized_fact(fact)
    title=catalogue.fold(entry['name']);description=catalogue.fold(fact['description'])
    expected_pack=catalogue.pack(entry['name'])
    errors=[]
    if not declared['namespace_verified']:errors.append('catalogue_namespace_or_code_missing')
    elif declared['namespace']!=entry['kind'] or declared['code']!=entry['code']:errors.append('catalogue_namespace_or_code_conflict')
    if not national_catalogue.snapshot_info({**entry,'row_count':entry.get('snapshot_count',0),'active_count':0,'inactive_count':0,'id':entry['snapshot_id']})['official_snapshot']:errors.append('snapshot_origin_unverified')
    if len(title)<10 or not (description==title or description.startswith(title+' ')):errors.append('description_needs_review')
    if norm['confidence']=='incomplete' or not fact.get('unit'):errors.append('unit_or_package_needs_review')
    if expected_pack and expected_pack!=norm['package_signature']:errors.append('package_conflict')
    return {'eligible':not errors,'reasons':errors,'declaration':declared,
        'unit_basis':'Unidade original do órgão, sem conversão. O CSV nacional não define unidade de fornecimento.',
        'technical_equivalence_between_purchases':False}

def checked_entry(ctx,snapshot,code):
    entry=national_catalogue.entry(ctx,snapshot,code)
    snapshot_row=ctx.db.one('SELECT row_count FROM national_catalogue_snapshot WHERE id=:s',{'s':snapshot})
    entry['snapshot_count']=snapshot_row['row_count']
    return entry

def candidates(ctx,snapshot,code,q=''):
    entry=checked_entry(ctx,snapshot,code)
    words=catalogue.fold(entry['name']).split()
    specific=next((w for w in ['NOBREAK','LIDOCAINA','ANESTESICO','CAFE','PAPEL','TREINAMENTO','VEICULO','UNIFORME'] if w in words),None)
    term=q or specific or next((w for w in words if len(w)>4 and w not in {'MATERIAL','SERVICO','FORNECIMENTO','UNIDADE','CONTRATACAO'}),'')
    records=[];active=catalogue.active_products(ctx)
    for fact in facts(ctx,term,51):
        record=original_record(fact);checks=automatic_checks(entry,fact,record)
        declared=checks['declaration'];ref={'id':fact['item_id'],'version':fact['item_version']}
        product=next((p for p in active if ref in p['members']),None)
        records.append({'fact_id':fact['id'],'item_id':fact['item_id'],'item_version':fact['item_version'],
            'description':fact['description'],'unit':fact['unit'],'package':catalogue.pack(fact['description']),
            'municipality_ibge':fact['municipality_ibge'],'municipality_name':fact['municipality_name'],
            'buyer_name':fact['buyer_name'],'buyer_cnpj':fact['buyer_cnpj'],'government_level':fact['government_level'],
            'source_url':fact['source_url'],'source_sha256':fact['source_sha256'],'consulted_at':fact['consulted_at'],
            'declaration':declared,'automatic_checks':checks,'product_id':product['id'] if product else None,
            'status':'official_declared_identity' if checks['eligible'] else 'requires_human_review'})
    return normalize({'records':records[:50],'candidate_count':len(records[:50]),'truncated':len(records)>50,'discovery_term':term,
        'notice':'Candidatos não comprovam equivalência. Confira descrição, unidade, embalagem e fonte. Não representam todas as compras.'})

def verify_auto(ctx,snapshot,code,product,fact_id):
    entry=checked_entry(ctx,snapshot,code)
    fact=ctx.db.one('''SELECT f.*,s.body AS source_body,s.url AS source_url,s.sha256 AS source_sha256
        FROM procurement_fact f JOIN source_observation s ON s.id=f.source_id
        WHERE f.id=:i AND f.is_current AND f.classification='official' AND s.classification='official' AND f.provider='PNCP_ITENS' ''',{'i':fact_id})
    if not fact:fail(422,'A fonte atual deste item precisa ser conferida.','CATALOGUE_SOURCE_REQUIRED')
    if product['members']!=[{'id':fact['item_id'],'version':fact['item_version']}]:
        fail(422,'A associação automática aceita apenas a identidade deste item e versão.','SINGLE_ITEM_REQUIRED')
    checks=automatic_checks(entry,fact,original_record(fact))
    if not checks['eligible']:fail(422,'A fonte não permite vincular este código automaticamente. Confira os candidatos.','CATALOGUE_REVIEW_REQUIRED')
    return {'mode':'official_source','fact_id':str(fact['id']),'source_url':fact['source_url'],'source_sha256':fact['source_sha256'],
        'checks':checks,'human_technical_approval':False,'merged_other_items':False}
