"""Local municipal evidence with explicit reviewed/code versus textual candidate states."""
from datetime import date
import re
from . import portfolio,portfolio_rules,catalogue_evidence
from .db import normalize,encoded
from .security import fail

PHASES={'publicado_estimado','homologado','contratado','empenhado','liquidado','pago'}


def source_groups(fact,record):
    """Text is only a review candidate, never a reviewed group/code binding."""
    material=(record or {}).get('materialOuServico')
    kind={'M':'CATMAT','S':'CATSER'}.get(material)
    if not kind:return []
    entries=portfolio_rules.classify({'name':fact['description'],'kind':kind})
    keep={r['group_id'] for r in entries if r['technical_status'] in (portfolio_rules.DIRECT,portfolio_rules.REVIEW)}
    name=portfolio_rules.fold(fact['description'])
    prefixes={'01':r'^(AUTOMOVEL|VEICULO UTILITARIO|ONIBUS|CAMINHAO)\b',
        '03':r'^UNIFORME ESCOLAR\b','04':r'^(CARTEIRA|CADEIRA|MESA) ESCOLAR\b',
        '06':r'^(LIVRO DIDATICO|KIT PEDAGOGICO)\b','10':r'^CESTA BASICA\b',
        '12':r'^UNIFORME PROFISSIONAL\b','13':r'^(SERINGA|AGULHA HIPODERMICA|CATETER|LUVA CIRURGICA|GAZE)\b',
        '15':r'^CAFE\b','17':r'^(NOBREAK|NOTEBOOK|MICROCOMPUTADOR|IMPRESSORA|ROTEADOR|SWITCH)\b'}
    excluded={r['group_id'] for r in entries if r['technical_status']==portfolio_rules.EXCLUDED}
    if kind=='CATMAT':
        keep|={group for group,pattern in prefixes.items() if group not in excluded and re.search(pattern,name)}
        if re.search(r'^CONECTOR\b.*\bRJ\s?-?45\b',name) or re.search(r'^PLACA PERIFERICA\b.*\b(PC|COMPUTADOR|PERIFERICOS)\b',name):keep.add('17')
        if re.search(r'\b(VETERINARIO|VETERINARIA|EQUINO|OVINO)\b',name):keep.discard('13')
    return sorted(keep)


def history(ctx,*,group,start,end,phase,municipalities=(),code=None,snapshot=None,buyer=None,
            provider=None,offset=0,limit=25,candidates=True,item_id=None,item_version=None,_all=False):
    ctx.require('read')
    if group not in {f'{i:02}' for i in range(1,21)} or phase not in PHASES:fail(422,'Confira o grupo e a situação.')
    if end<start or (end-start).days>366 or end>date.today():fail(422,'Escolha até doze meses passados.')
    if bool(code)!=bool(snapshot):fail(422,'Informe código e versão do catálogo juntos.')
    if bool(item_id)!=(item_version is not None):fail(422,'Escolha o item municipal e sua versão juntos.')
    if not 0<=offset<=20000 or not 1<=limit<=50:fail(422,'Confira a página de resultados.')
    selected=portfolio.run(ctx)
    if not selected:return {'records':[],'total':0,'state':'not_initialized','source_completeness_claimed':False}
    known={r['ibge'] for r in ctx.db.all('SELECT ibge FROM municipality')};cities=sorted(set(municipalities) or known)
    if set(cities)-known or len(cities)>118:fail(422,'Confira os municípios selecionados.')
    links=ctx.db.all('''SELECT l.*,s.kind FROM portfolio_code_link l JOIN national_catalogue_snapshot s ON s.id=l.snapshot_id
        WHERE l.org_id=:o AND l.run_id=:r AND l.group_code=:g AND l.technical_status IN ('DIRECT_TECHNICAL','NEEDS_TECH_REVIEW')
        AND (CAST(:snapshot AS uuid) IS NULL OR l.snapshot_id=CAST(:snapshot AS uuid) AND l.code=:code)''',
        {'o':ctx.org_id,'r':selected['id'],'g':group,'snapshot':snapshot,'code':code})
    keys={(r['kind'],r['code']) for r in links}
    reviewed=ctx.db.all('''SELECT n.snapshot_id,n.code,p.members FROM national_product_link n
        JOIN canonical_product p ON p.org_id=n.org_id AND p.id=n.product_id
        WHERE n.org_id=:o AND p.classification='official'
        AND NOT EXISTS(SELECT 1 FROM canonical_product newer WHERE newer.org_id=p.org_id AND newer.supersedes_id=p.id)''',{'o':ctx.org_id})
    reviewed_items={(str(m['id']),m['version']) for r in reviewed if any(str(l['snapshot_id'])==str(r['snapshot_id']) and l['code']==r['code'] for l in links) for m in r['members']}
    clauses=['f.org_id=:o','f.classification=\'official\'','s.classification=\'official\'','f.is_current',
        'f.municipality_ibge=ANY(:cities)',"b.government_level='M'",'f.phase=:phase','f.event_date BETWEEN :start AND :end']
    params={'o':ctx.org_id,'cities':cities,'phase':phase,'start':start,'end':end}
    if buyer:clauses.append('b.cnpj=:buyer');params['buyer']=buyer
    if provider:clauses.append('f.provider=:provider');params['provider']=provider
    if item_id:clauses.append('f.item_id=:item AND f.item_version=:version');params.update(item=item_id,version=item_version)
    rows=ctx.db.all('''SELECT f.*,b.name AS buyer_name,b.cnpj AS buyer_cnpj,s.url AS source_url,s.sha256 AS source_sha256,
        s.body AS source_body,s.consulted_at,m.name AS municipality_name,
        parent.description AS parent_description,parent.unit AS parent_unit,parent.metadata AS parent_metadata,
        ps.body AS parent_source_body,ps.sha256 AS parent_source_sha256,ps.id AS parent_source_id
        FROM procurement_fact f JOIN source_observation s ON s.id=f.source_id
        JOIN buyer b ON b.id=f.buyer_id AND b.org_id=f.org_id JOIN municipality m ON m.ibge=f.municipality_ibge
        LEFT JOIN procurement_fact parent ON parent.id::text=f.metadata->>'parent_id' AND parent.org_id=f.org_id
            AND parent.provider='PNCP_ITENS' AND parent.item_id=f.item_id AND parent.item_version=f.item_version
        LEFT JOIN source_observation ps ON ps.id=parent.source_id AND ps.classification='official'
        WHERE '''+' AND '.join(clauses)+' ORDER BY f.event_date DESC,f.id LIMIT 20001',params)
    if len(rows)>20000:fail(422,'Reduza o período ou selecione um órgão.','PORTFOLIO_HISTORY_LIMIT')
    matched=[]
    for row in rows:
        state=None;record=catalogue_evidence.original_record(row) if row['provider']=='PNCP_ITENS' else None
        if row['provider']=='PNCP_RESULTADOS' and row.get('parent_source_id'):
            record=catalogue_evidence.original_record({'description':row['parent_description'],'unit':row['parent_unit'],
                'metadata':row['parent_metadata'],'source_body':row['parent_source_body'],'source_sha256':row['parent_source_sha256']})
        declared=catalogue_evidence.declaration(record or {})
        if (row.get('item_id'),row.get('item_version')) in reviewed_items:state='reviewed_catalogue_link'
        elif declared['namespace_verified'] and (declared['namespace'],declared['code']) in keys:state='official_declared_code_not_cross_item_equivalence'
        elif candidates and not code:
            # Results retain the item version, but group triage still needs the
            # original item observation, not the award supplier narrative.
            if group in source_groups(row,record):state='description_candidate_requires_review'
        if not state:continue
        supplier=(row['metadata'].get('supplier') or {})
        verified_supplier=bool(row['provider'] in ('PNCP_RESULTADOS','PNCP_CONTRATOS')
            and re.fullmatch(r'\d{14}',str(supplier.get('cnpj') or '')))
        matched.append({k:row[k] for k in ('id','item_id','item_version','municipality_ibge','municipality_name',
            'buyer_name','buyer_cnpj','provider','phase','event_date','description','unit','quantity','unit_price','amount',
            'obligation_id','source_id','source_url','source_sha256','consulted_at')} |
            {'group_match_state':state,'catalogue_namespace':declared['namespace'],'catalogue_code':declared['code'],
            'currency':row['metadata'].get('currency','BRL'),
            'group_evidence_source_id':str(row.get('parent_source_id') or row['source_id']),
            'supplier':supplier if verified_supplier else None,'supplier_role':'adjudicatário' if row['phase']=='homologado' and verified_supplier else 'contratado' if verified_supplier else None,
            'coverage_status':'partial','origin':'municipal_procurement','included_in_group_totals':False,
            'quantity_is_consumption':False,'financial_execution_proven':row['metadata'].get('financial_execution_proven',False)})
    return normalize({'records':matched if _all else matched[offset:offset+limit],'total':len(matched),'offset':offset,'limit':limit,
        'next_offset':offset+limit if offset+limit<len(matched) else None,'state':'available' if matched else 'no_matches_in_observed_scope',
        'group':group,'run_id':selected['id'],'rule_version':selected['rule_version'],'municipalities':cities,
        'start':start,'end':end,'phase':phase,'source_completeness_claimed':False,'coverage_status':'partial',
        'notice':'Candidatos por descrição exigem revisão. Ausência de vínculo não comprova ausência de compras.',
        'comparative_quantity':None,'comparative_amount':None})
