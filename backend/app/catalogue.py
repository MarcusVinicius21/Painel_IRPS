"""Traceable item normalization; only a person can approve canonical equivalence."""
from collections import defaultdict
from datetime import date
from decimal import Decimal
import hashlib,re,unicodedata
from .db import encoded,identifier,normalize
from .security import fail
from . import sources
from . import coverage_inventory,modality
from .history_filters import HistoryFilters

ALGORITHM='catalogue-v1'
PACK_RE=re.compile(r'\b(CAIXA|CX|PACOTE|PCT|FARDO|KIT|EMBALAGEM|EMB)\s*(?:DE|COM)?\s*(\d+(?:[,.]\d+)?)\s*(RESMAS?|UNIDADES?|UNID|UND|FOLHAS?|LITROS?|L|KG|QUILOS?|GRAMAS?|G|PARES?|PECAS?|FRASCOS?)\b')
ALIASES={'CX':'CAIXA','PCT':'PACOTE','EMB':'EMBALAGEM','UNID':'UNIDADE','UND':'UNIDADE','L':'LITRO','QUILO':'KG','QUILOS':'KG','G':'GRAMA','PARES':'PAR','PECAS':'PECA','RESMAS':'RESMA','FOLHAS':'FOLHA','FRASCOS':'FRASCO','UNIDADES':'UNIDADE','LITROS':'LITRO','GRAMAS':'GRAMA'}
STOPWORDS={'DE','DA','DO','DAS','DOS','COM','PARA'}
PNCP_PROCESS_RE=re.compile(r'^\d{14}-1-\d+/\d{4}$')


def reliable_obligation(row):
    value=row.get('obligation_id')
    if not value:return None
    if row.get('classification')=='synthetic':return value
    return value if row.get('provider','').startswith('PNCP') and PNCP_PROCESS_RE.fullmatch(value) else None


def fold(value):
    plain=unicodedata.normalize('NFKD',str(value or ''))
    plain=''.join(c for c in plain if not unicodedata.combining(c)).upper()
    return re.sub(r'\s+',' ',re.sub(r'[^A-Z0-9,./]+',' ',plain)).strip()


def token_key(value):
    # Word order alone may vary in public descriptions. This is a suggestion key,
    # never a technical equivalence or automatic merge.
    return ' '.join(sorted(word for word in fold(value).split() if word not in STOPWORDS))


def pack(value):
    match=PACK_RE.search(fold(value))
    if not match:return None
    container,amount,measure=match.groups()
    container=ALIASES.get(container,container)
    measure=ALIASES.get(measure,measure)
    return ':'.join((container,amount.replace(',','.'),measure))


def unit_key(value):
    # PNCP may label a single unit as '1,00 UNIDADE'. No package conversion.
    label=re.sub(r'^1(?:[,.]0+)?\s+(?=[A-Z])','',fold(value))
    word=label.split(' ',1)[0] if label else ''
    return ALIASES.get(word,word)


def observed_identity(ctx,fact_id):
    """Singleton identity from an exact source/version, not cross-item equivalence."""
    ctx.require('opportunity.manage')
    fact=ctx.db.one('''SELECT f.*,s.url FROM procurement_fact f JOIN source_observation s ON s.id=f.source_id
        WHERE f.id=:i AND f.is_current AND f.classification='official' AND s.classification='official'
        AND f.item_id IS NOT NULL AND f.item_version IS NOT NULL''',{'i':fact_id})
    if not fact:fail(404,'Este item oficial não está disponível.')
    norm=normalized_fact(fact)
    if norm['confidence']=='incomplete':fail(422,'A unidade ou embalagem precisa de conferência antes da análise.','SPECIFICATION_REVIEW_REQUIRED')
    ctx.db.execute('SELECT pg_advisory_xact_lock(hashtextextended(:k,0))',{'k':ctx.org_id+':canonical-products'})
    ref={'id':fact['item_id'],'version':fact['item_version']}
    for p in active_products(ctx):
        if ref in p['members']:
            return {'id':str(p['id']),'identity_only':len(p['members'])==1,'created':False}
    pid=identifier()
    ctx.db.execute('''INSERT INTO canonical_product(org_id,id,name,category,classification,unit_key,package_signature,
        members,justification,evidence,reviewed_by) VALUES (:o,:i,:n,'Item identificado na fonte','official',:u,:p,
        CAST(:m AS jsonb),:j,:e,:a)''',{'o':ctx.org_id,'i':pid,'n':fact['description'][:160],
        'u':norm['unit_key'],'p':norm['package_signature'],'m':encoded([ref]),
        'j':'Identidade determinística de um único item e versão. Não aprova equivalência com outros itens, necessidade ou quantidade.',
        'e':fact['url']+' · fato '+str(fact['id'])+' · versão '+str(fact['item_version']),'a':ctx.actor_id})
    ctx.audit('catalogue.source_identity_created',pid,{'fact_id':fact_id,'source_id':str(fact['source_id']),
        'item_id':fact['item_id'],'item_version':fact['item_version'],'cross_item_equivalence':False})
    return {'id':pid,'identity_only':True,'created':True,'cross_item_equivalence_reviewed':False}


def normalized_fact(row):
    metadata=row.get('metadata') or {}
    original=row.get('description') or ''
    unit=row.get('unit') or ''
    unit_pack=pack(unit);description_pack=pack(original)
    issues=[]
    if not original:issues.append('description_missing')
    if not unit:issues.append('unit_missing')
    if unit_pack and description_pack and unit_pack!=description_pack:issues.append('package_conflict')
    if description_pack and not unit_pack and unit_key(unit) in ('UNIDADE','UN'):issues.append('package_not_in_unit')
    signature=unit_pack or description_pack
    raw_code=metadata.get('catalogue_code')
    code=str(raw_code).strip() if raw_code is not None and str(raw_code).strip() else None
    namespace='PNCP' if code and row.get('provider','').startswith('PNCP') else row.get('provider') if code else None
    if not code:issues.append('official_code_missing')
    if not signature:issues.append('package_unspecified')
    confidence='incomplete' if not original or not unit or 'package_conflict' in issues or 'package_not_in_unit' in issues else (
        'coded_package' if code and signature else 'coded_unit' if code else 'text_unit')
    return {'original_description':original,'description_key':fold(original),'original_unit':unit,
        'unit_key':unit_key(unit),'package_signature':signature,'catalogue_namespace':namespace,
        'catalogue_code':code,'confidence':confidence,'issues':issues}


def reprocess(ctx,limit=500,offset=0):
    ctx.require('sources.sync')
    rows=ctx.db.all("""SELECT f.id,f.source_id,f.item_id,f.item_version,f.description,f.unit,f.metadata,f.provider
        FROM procurement_fact f WHERE f.item_id IS NOT NULL AND f.item_version IS NOT NULL
        AND (f.classification='official' OR f.org_id=:o)
        ORDER BY f.id LIMIT :limit OFFSET :offset""",{'limit':limit,'offset':offset,'o':ctx.org_id})
    inserted=0
    for row in rows:
        data=normalized_fact(row)
        result=ctx.db.execute("""INSERT INTO item_normalization(org_id,id,fact_id,source_id,algorithm_version,item_id,item_version,
            original_description,description_key,original_unit,unit_key,package_signature,catalogue_namespace,catalogue_code,confidence,issues)
            VALUES (:o,:i,:f,:s,:algorithm,:item,:v,:original_description,:description_key,:original_unit,:unit_key,
            :package_signature,:catalogue_namespace,:catalogue_code,:confidence,CAST(:issues AS jsonb))
            ON CONFLICT(org_id,fact_id,algorithm_version) DO NOTHING""",
            {'o':ctx.org_id,'i':identifier(),'f':row['id'],'s':row['source_id'],'algorithm':ALGORITHM,
             'item':row['item_id'],'v':row['item_version'],**{k:v for k,v in data.items() if k!='issues'},'issues':encoded(data['issues'])})
        inserted+=result.rowcount
    ctx.audit('catalogue.reprocessed',ALGORITHM,{'scanned':len(rows),'inserted':inserted,'offset':offset})
    return {'algorithm':ALGORITHM,'scanned':len(rows),'inserted':inserted,'next_offset':offset+len(rows) if len(rows)==limit else None,
        'facts_preserved':True,'reviews_preserved':True}


def active_products(ctx):
    return ctx.db.all("""SELECT c.* FROM canonical_product c WHERE c.org_id=:o
        AND NOT EXISTS (SELECT 1 FROM canonical_product successor WHERE successor.org_id=c.org_id AND successor.supersedes_id=c.id)
        ORDER BY c.created_at DESC,c.id""",{'o':ctx.org_id})


def reviewed_similar(ctx,product_id,offset=0,limit=20):
    """Exact members of a current human-reviewed group, never token candidates."""
    ctx.require('read')
    products=active_products(ctx)
    product=next((p for p in products if str(p['id'])==str(product_id)),None)
    if product is None:fail(404,'Esta equivalência precisa de uma revisão atual.','PRODUCT_NOT_FOUND')
    refs={(m['id'],m['version']) for m in product['members']}
    if len(refs)!=len(product['members']):fail(409,'A equivalência contém versões repetidas. Revise o grupo.','INCOMPATIBLE_ITEMS')
    overlaps=any(refs & {(m['id'],m['version']) for m in p['members']} for p in products if p['id']!=product['id'])
    if overlaps:fail(409,'Há grupos revisados sobrepostos. Confira as equivalências antes de usar.','CANONICAL_OVERLAP')
    if not product.get('reviewed_by') or not product.get('justification') or not product.get('evidence'):
        fail(409,'Falta comprovar a revisão desta equivalência.','EQUIVALENCE_REVIEW_REQUIRED')
    members=encoded([{'id':i,'version':v} for i,v in sorted(refs)])
    rows=ctx.db.all("""SELECT i.id,i.version,i.name,i.unit,i.classification,
        f.id AS fact_id,s.url,s.consulted_at,s.sha256
        FROM item_version i JOIN jsonb_to_recordset(CAST(:members AS jsonb)) AS m(id text,version integer)
          ON i.id=m.id AND i.version=m.version
        LEFT JOIN LATERAL (SELECT f.id,f.source_id FROM procurement_fact f
          WHERE f.item_id=i.id AND f.item_version=i.version AND f.is_current AND f.unit=i.unit
          AND f.classification=:dataset AND (f.classification='official' OR f.org_id=:o)
          ORDER BY f.event_date DESC NULLS LAST,f.id LIMIT 1) f ON true
        LEFT JOIN source_observation s ON s.id=f.source_id
        ORDER BY i.id,i.version""",{'members':members,'dataset':product['classification'],'o':ctx.org_id})
    if len(rows)!=len(refs) or any(r['classification']!=product['classification'] or comparison_issues({'description':r['name'],'unit':r['unit'],'metadata':{}},product) for r in rows):
        fail(409,'Os itens precisam de nova conferência de unidade, embalagem ou versão.','INCOMPATIBLE_ITEMS')
    # The UUID is the immutable group version; superseded versions are never returned.
    review={'version_id':str(product['id']),'supersedes_id':str(product['supersedes_id']) if product.get('supersedes_id') else None,
        'reviewed_by':str(product['reviewed_by']),'reviewed_at':product['created_at'],
        'justification':product['justification'],'evidence':product['evidence']}
    return normalize({'product_id':str(product['id']),'name':product['name'],'classification':product['classification'],
        'unit':product['unit_key'],'package_signature':product['package_signature'],'review':review,
        'records':rows[offset:offset+limit],'total':len(rows),'offset':offset,'limit':limit,
        'notice':'Membros da mesma equivalência revisada, incluindo o item de origem. Abrir um registro não altera o estudo nem soma quantidades.'})


def candidates(ctx,limit=100):
    ctx.require('read')
    rows=ctx.db.all("""SELECT n.item_id,n.item_version,n.description_key,n.original_description,n.original_unit,n.unit_key,
        n.package_signature,n.catalogue_namespace,n.catalogue_code,n.confidence,n.issues,n.source_id,
        f.municipality_ibge,f.phase,s.url,s.consulted_at
        FROM item_normalization n JOIN procurement_fact f ON f.id=n.fact_id
        JOIN source_observation s ON s.id=n.source_id
        WHERE n.org_id=:o AND n.algorithm_version=:algorithm AND f.is_current AND f.classification='official'
        ORDER BY n.item_id,n.item_version LIMIT 10000""",{'o':ctx.org_id,'algorithm':ALGORITHM})
    assigned={(m['id'],m['version']) for p in active_products(ctx) for m in p['members']}
    groups=defaultdict(list)
    for row in rows:
        if (row['item_id'],row['item_version']) in assigned:continue
        if row['catalogue_code']:
            key=('code',row['catalogue_namespace'],row['catalogue_code'],row['unit_key'],row['package_signature'])
        else:key=('tokens',token_key(row['original_description']),row['unit_key'],row['package_signature'])
        groups[key].append(row)
    output=[]
    for key,records in groups.items():
        unique={(r['item_id'],r['item_version']):r for r in records}
        if len(unique)<2:continue
        representative=next(iter(unique.values()))
        output.append({'basis':key[0],'name':representative['original_description'],'unit':representative['original_unit'],
            'catalogue_code':representative['catalogue_code'],'catalogue_namespace':representative['catalogue_namespace'],
            'package_signature':representative['package_signature'],
            'confidence':'strong_candidate' if key[0]=='code' and key[-1] and all(r['confidence']=='coded_package' for r in unique.values()) else 'needs_review',
            'members':[{'id':r['item_id'],'version':r['item_version'],'original_description':r['original_description'],
                'original_unit':r['original_unit'],'issues':r['issues'],'source_url':r['url'],'consulted_at':r['consulted_at']}
                for r in unique.values()],
            'municipalities':sorted({r['municipality_ibge'] for r in records if r['municipality_ibge']}),
            'observed_facts':len(records),'approved':False})
    output.sort(key=lambda item:(-len(item['members']),item['name']))
    return normalize({'records':output[:limit],'total':len(output),'message':'São sugestões. Confirme descrição, unidade e embalagem antes de unir itens.'})


def create_product(ctx,body):
    ctx.require('opportunity.manage')
    members=[m.model_dump() for m in body.members]
    refs={(m['id'],m['version']) for m in members}
    if len(refs)!=len(members):fail(422,'Remova os itens repetidos.')
    ctx.db.execute('SELECT pg_advisory_xact_lock(hashtextextended(:k,0))',{'k':ctx.org_id+':canonical-products'})
    active=active_products(ctx)
    previous=next((p for p in active if str(p['id'])==str(body.supersedes_id)),None) if body.supersedes_id else None
    if body.supersedes_id and not previous:fail(409,'O grupo mudou. Abra a versão atual antes de revisar.','CANONICAL_VERSION_CHANGED')
    for product in active:
        if previous and product['id']==previous['id']:continue
        if refs & {(m['id'],m['version']) for m in product['members']}:
            fail(409,'Um item já pertence a outro produto revisado. Confira os grupos.','CANONICAL_OVERLAP')
    normalized=ctx.db.all("""SELECT DISTINCT ON (n.item_id,n.item_version) n.item_id,n.item_version,n.unit_key,
        n.package_signature,f.classification FROM item_normalization n JOIN procurement_fact f ON f.id=n.fact_id
        WHERE n.org_id=:o AND n.algorithm_version=:algorithm AND f.is_current
        ORDER BY n.item_id,n.item_version,n.created_at DESC""",{'o':ctx.org_id,'algorithm':ALGORITHM})
    found={(r['item_id'],r['item_version']):r for r in normalized}
    if refs-set(found):fail(422,'Atualize a análise dos itens antes de criar este produto.','NORMALIZATION_REQUIRED')
    units={found[ref]['unit_key'] for ref in refs}
    packages={found[ref]['package_signature'] for ref in refs}
    classes={found[ref]['classification'] for ref in refs}
    if len(units)!=1 or len(packages)!=1 or len(classes)!=1 or not next(iter(units)):
        fail(422,'Os itens têm unidades, embalagens ou origens incompatíveis. Separe os produtos.','INCOMPATIBLE_ITEMS')
    pid=identifier()
    ctx.db.execute("""INSERT INTO canonical_product(org_id,id,name,category,classification,unit_key,package_signature,
        members,justification,evidence,reviewed_by,supersedes_id)
        VALUES (:o,:i,:n,:category,:classification,:unit,:package,CAST(:members AS jsonb),:j,:e,:a,:supersedes)""",
        {'o':ctx.org_id,'i':pid,'n':body.name,'category':body.category,'classification':next(iter(classes)),
         'unit':next(iter(units)),'package':next(iter(packages)),'members':encoded(members),
         'j':body.justification,'e':body.evidence,'a':ctx.actor_id,'supersedes':str(body.supersedes_id) if body.supersedes_id else None})
    ctx.audit('catalogue.product_reviewed',pid,{'members':len(members),'supersedes':str(body.supersedes_id) if body.supersedes_id else None})
    return {'id':pid,'members':members,'reviewed':True,'supersedes_id':body.supersedes_id}


def validated_municipalities(ctx,municipalities):
    """None means the unrestricted summary; an explicit empty list is invalid."""
    cities=list(dict.fromkeys(municipalities))
    if not cities:fail(422,'Selecione pelo menos um município.','MUNICIPALITY_REQUIRED')
    if any(not re.fullmatch(r'\d{7}',code) for code in cities):
        fail(422,'Confira os códigos dos municípios selecionados.','MUNICIPALITY_UNKNOWN')
    known=ctx.db.all('SELECT ibge FROM municipality WHERE ibge=ANY(:ids)',{'ids':cities})
    if len(known)!=len(cities):fail(422,'Confira os municípios selecionados.','MUNICIPALITY_UNKNOWN')
    return cities


def products(ctx,phase='homologado',start=None,end=None,municipalities=None):
    ctx.require('read')
    start=start or date(2020,1,1);end=end or date.today()
    if municipalities is not None:
        municipalities=validated_municipalities(ctx,municipalities)
    result=[]
    for product in active_products(ctx):
        members=encoded([{'item_id':m['id'],'item_version':m['version']} for m in product['members']])
        rows=ctx.db.all("""SELECT f.id,f.provider,f.classification,f.item_id,f.item_version,f.obligation_id,f.municipality_ibge,f.event_date,
            f.quantity,f.amount,f.unit_price,f.description,f.unit,f.source_id,s.url,s.consulted_at
            FROM procurement_fact f JOIN source_observation s ON s.id=f.source_id
            WHERE f.classification=:dataset AND f.phase=:phase AND f.is_current
              AND (:phase<>'homologado' OR COALESCE(f.metadata->>'eligible_result','true')='true')
              AND f.event_date BETWEEN :start AND :end
              AND (f.item_id,f.item_version) IN (
                SELECT member.item_id,member.item_version FROM jsonb_to_recordset(CAST(:members AS jsonb))
                AS member(item_id text,item_version integer))
              AND (:all_cities OR f.municipality_ibge=ANY(:cities))
              AND (f.classification='official' OR f.org_id=:o)
            ORDER BY f.event_date,f.id LIMIT 20001""",
            {'dataset':product['classification'],'phase':phase,'start':start,'end':end,'members':members,'o':ctx.org_id,
             'all_cities':municipalities is None,'cities':municipalities or []})
        if len(rows)>20000:fail(422,'Selecione um período ou municípios menores para analisar este produto.','CATALOGUE_LIMIT')
        comparable=[r for r in rows if (n:=normalized_fact(r))['unit_key']==product['unit_key']
            and n['package_signature']==product['package_signature'] and n['confidence']!='incomplete']
        quantities=[r['quantity'] for r in comparable if r['quantity'] is not None]
        amounts=[r['amount'] for r in comparable if r['amount'] is not None]
        result.append({'id':str(product['id']),'name':product['name'],'category':product['category'],
            'classification':product['classification'],'phase':phase,'unit':product['unit_key'],
            'package_signature':product['package_signature'],'members':product['members'],
            'observed_records':len(rows),'processes':len({p for r in rows if (p:=reliable_obligation(r))}),
            'municipalities':sorted({r['municipality_ibge'] for r in rows if r['municipality_ibge']}),
            'active_months':len({r['event_date'].strftime('%Y-%m') for r in rows if r['event_date']}),
            'observed_quantity':sum(quantities,Decimal(0)) if quantities else None,
            'known_amount':sum(amounts,Decimal(0)) if amounts else None,
            'quantity_complete':bool(rows) and len(comparable)==len(rows) and len(quantities)==len(rows),
            'sources':[{'url':r['url'],'consulted_at':r['consulted_at'],'description':r['description'],
                'unit':r['unit'],'fact_id':str(r['id'])} for r in rows[:25]],
            'source_count':len(rows),'source_list_truncated':len(rows)>25,
            'reviewed_at':product['created_at'],'supersedes_id':product['supersedes_id'],
            'notice':'Quantidade observada nesta situação. Não comprova consumo nem necessidade futura.'})
    return normalize({'records':result,'phase':phase,'start':start,'end':end,'municipalities':municipalities,
                      'municipality_scope':'all' if municipalities is None else 'selected','total':len(result)})


def comparison_issues(row, product):
    """One predicate for the displayed scope and the existing numerical totals."""
    norm=normalized_fact(row);reasons=[]
    if norm['unit_key']!=product['unit_key']:reasons.append('unit_mismatch')
    if norm['package_signature']!=product['package_signature']:reasons.append('package_mismatch')
    if norm['confidence']=='incomplete':reasons.append('specification_review_required')
    return reasons


def _history_facts(ctx,product,phase,start,end,cities,provider=None,providers_only=False):
    members=encoded([{'item_id':m['id'],'item_version':m['version']} for m in product['members']])
    columns='DISTINCT f.provider' if providers_only else """f.id,f.provider,f.classification,f.event_identity,f.revision_hash,f.obligation_id,
        f.municipality_ibge,f.item_id,f.item_version,f.event_date,f.quantity,f.unit_price,f.amount,
        f.description,f.unit,f.metadata,f.source_id,s.url,s.consulted_at,s.sha256,s.provider AS observation_provider,b.name AS buyer_name,b.cnpj AS buyer_cnpj,b.government_level"""
    ordering='f.provider' if providers_only else 'f.event_date,f.id'
    limit=201 if providers_only else 20001
    return ctx.db.all(f"""SELECT {columns}
        FROM procurement_fact f JOIN source_observation s ON s.id=f.source_id LEFT JOIN buyer b ON b.id=f.buyer_id
        WHERE f.classification=:dataset AND (f.classification='official' OR f.org_id=:org)
          AND f.is_current AND f.phase=:phase
          AND (f.item_id,f.item_version) IN (
            SELECT member.item_id,member.item_version FROM jsonb_to_recordset(CAST(:members AS jsonb))
            AS member(item_id text,item_version integer))
          AND f.event_date BETWEEN :start AND :end AND f.municipality_ibge=ANY(:cities)
          AND (:phase<>'homologado' OR COALESCE(f.metadata->>'eligible_result','true')='true')
          AND (CAST(:provider AS text) IS NULL OR f.provider=:provider)
        ORDER BY {ordering} LIMIT {limit}""",
        {'dataset':product['classification'],'org':ctx.org_id,'members':members,
         'phase':phase,'start':start,'end':end,'cities':cities,'provider':provider})


def history_filter_options(ctx,product_id,phase,start,end,municipalities):
    ctx.require('read');cities=validated_municipalities(ctx,municipalities)
    product=next((p for p in active_products(ctx) if str(p['id'])==str(product_id)),None)
    if product is None:fail(404,'Este produto revisado não está disponível.','PRODUCT_NOT_FOUND')
    records=_history_facts(ctx,product,phase,start,end,cities,providers_only=True)
    if len(records)>200:fail(422,'Reduza o recorte para consultar as fontes.','HISTORY_PROVIDER_LIMIT')
    return {'providers':[r['provider'] for r in records],'modality_available':False,
        'modality_limitation':modality.LIMITATION,'modality_normalization_version':modality.VERSION,
        'modality_unknown_handling':'not_filtered',
        'provider_field':'procurement_fact.provider','provider_matching':'exact',
        'scope':normalize({'phase':phase,'start':start,'end':end,'municipalities':cities,'classification':product['classification']})}


def product_history(ctx,product_id,phase,start,end,municipalities,filters=None):
    """Observed facts per selected city. Unknown coverage never becomes zero demand."""
    ctx.require('read')
    cities=validated_municipalities(ctx,municipalities)
    known=ctx.db.all('SELECT ibge,name,uf FROM municipality WHERE ibge=ANY(:ids) ORDER BY name',{'ids':cities})
    product=next((p for p in active_products(ctx) if str(p['id'])==str(product_id)),None)
    if product is None:fail(404,'Este produto revisado não está disponível.','PRODUCT_NOT_FOUND')
    filters=filters or HistoryFilters()
    rows=_history_facts(ctx,product,phase,start,end,cities,filters.provider)
    if len(rows)>20000:fail(422,'Escolha um período ou municípios menores para analisar este produto.','CATALOGUE_LIMIT')
    # A later revision replaces a fact. A repeated event identity is one observed line,
    # whereas several item lines in one obligation are not several purchases.
    unique={}
    for row in rows:
        unique[(row['provider'],row['event_identity'])]=row
    filter_exclusions=[]
    if filters.only_comparable:
        for key,row in list(unique.items()):
            reasons=comparison_issues(row,product)
            if reasons:
                filter_exclusions.append({'fact_id':str(row['id']),'municipality_ibge':row['municipality_ibge'],'reasons':reasons})
                del unique[key]
    by_city=defaultdict(list)
    for row in unique.values():by_city[row['municipality_ibge']].append(row)
    coverage=coverage_inventory.inventory(ctx,start,end,cities) if product['classification']=='official' else {'records':[]}
    output=[];all_compatible=[]
    for city in known:
        facts=by_city[city['ibge']]
        compatible=[];excluded=[];processes=set();events={};months=set();years=set()
        for row in facts:
            reason=comparison_issues(row,product)
            if reason:excluded.append({'fact_id':str(row['id']),'reasons':reason})
            else:compatible.append(row)
            obligation=reliable_obligation(row)
            if obligation:processes.add(obligation)
            if row['event_date']:
                months.add(row['event_date'].strftime('%Y-%m'));years.add(row['event_date'].year)
                if obligation:events.setdefault(obligation,row['event_date'])
        all_compatible.extend(compatible)
        amounts=[r['amount'] for r in compatible if r['amount'] is not None]
        quantities=[r['quantity'] for r in compatible if r['quantity'] is not None]
        prices=[r['unit_price'] for r in compatible if r['unit_price'] is not None]
        dates=sorted(set(events.values()))
        evidence=[{'fact_id':str(r['id']),'provider':r['provider'],'event_identity':r['event_identity'],
            'source_id':str(r['source_id']),'observation_provider':r.get('observation_provider'),'process_id':r['obligation_id'],'item_id':r['item_id'],'item_version':r['item_version'],
            'description':r['description'],'unit':r['unit'],'quantity':r['quantity'],
            'buyer_name':r.get('buyer_name'),'buyer_cnpj':r.get('buyer_cnpj'),'government_level':r.get('government_level'),
            'unit_price':r['unit_price'],'amount':r['amount'],'event_date':r['event_date'],
            'url':r['url'],'consulted_at':r['consulted_at'],'sha256':r['sha256'],
            'modality':modality.normalize(r['provider'],r['metadata'])}
            for r in facts]
        related=[r for r in coverage['records'] if r['municipality_ibge']==city['ibge'] and r['phase']==phase
                 and r['tasks'] and (not filters.provider or r['provider']==filters.provider)]
        coverage_state=coverage_inventory.phase_state(related,start,end)
        windows=[]
        for count in (1,3,6,12):
            index=end.year*12+end.month-count
            requested=date(index//12,index%12+1,1)
            first=max(start,requested)
            selected=[r for r in compatible if first<=r['event_date']<=end]
            vals=[r['quantity'] for r in selected if r['quantity'] is not None]
            windows.append({'months':count,'requested_start':requested,'start':first,'end':end,
                'observed_quantity':sum(vals,Decimal(0)) if vals else None,
                'comparable_records':len(selected),'processes_identified':len({p for r in selected if (p:=reliable_obligation(r))}),
                'fact_ids':[str(r['id']) for r in selected],
                'partial':True,'monthly_average':None,'recurrence_percentage':None,
                'limitation':'Total observado parcial. Não há denominador comprovado de toda a demanda municipal.',
                'scope_covers_requested_window':start<=requested})
        annual=[]
        for year in sorted(years):
            annual_rows=[r for r in compatible if r['event_date'].year==year]
            annual_q=[r['quantity'] for r in annual_rows if r['quantity'] is not None]
            annual.append({'year':year,'observed_quantity':sum(annual_q,Decimal(0)) if annual_q else None,
                'comparable_records':len(annual_rows),'partial':True})
        output.append({'municipality':city,'classification':product['classification'],'phase':phase,
            'observed_records':len(facts),'distinct_processes':len(processes) if processes else None,
            'processes_identified':len(processes),'comparable_records':len(compatible),
            'observed_quantity':sum(quantities,Decimal(0)) if quantities else None,
            'quantity_complete':bool(facts) and not excluded and len(quantities)==len(facts),
            'documented_amount':sum(amounts,Decimal(0)) if amounts else None,
            'unit_prices':prices,'first_observed':min((r['event_date'] for r in facts if r['event_date']),default=None),
            'last_observed':max((r['event_date'] for r in facts if r['event_date']),default=None),
            'observed_months':sorted(months),'observed_years':sorted(years),
            'interval_days':[ (b-a).days for a,b in zip(dates,dates[1:])],
            'temporal_windows':windows,'annual':annual,
            'recurrence_percentage':None,'coverage_state':('demonstration' if product['classification']=='synthetic'
                else coverage_state),
            'source_completeness_ratio':None,'coverage':related,'excluded_from_totals':excluded,
            'evidence':evidence[:100],'evidence_truncated':len(evidence)>100,
            'notice':'Meses observados não comprovam recorrência. Ausência de registro não comprova ausência de compra.'})
    summary,windows=historical_summary(list(unique.values()),all_compatible,product,phase,start,end,cities)
    summary['filters']=filters.model_dump()
    return normalize({'filter_exclusions':filter_exclusions,'contract_version':2,'summary':summary,'temporal_windows':windows,'observed_series':observed_series(all_compatible,known,phase,start,end,filters.model_dump(),product),'product':{'id':str(product['id']),'name':product['name'],'unit':product['unit_key'],
        'package_signature':product['package_signature'],'classification':product['classification'],
        'members':product['members'],'reviewed_at':product['created_at']},
        'scope':{'phase':phase,'start':start,'end':end,'municipalities':cities,'filters':filters.model_dump()},'municipalities':output,
        'method':'Fatos atuais por identidade de evento; processos por obrigação identificada. Quantidade apenas em unidade e embalagem compatíveis.',
        'source_completeness_claimed':False})



def observed_series(compatible, municipalities, phase, start, end, filters, product):
    """Only reconciled, scope-filtered compatible facts; no inference of zero or consumption.

    Geographic groups are disjoint municipality/UF partitions, never providers. Source
    references use the full eligible set, independently of truncated evidence previews.
    """
    def bucket(rows):
        values=[r['quantity'] for r in rows if r['quantity'] is not None]
        return {'observed_quantity':sum(values,Decimal(0)) if values else None,
                'comparable_records':len(rows),'quantity_complete':bool(rows) and len(values)==len(rows),
                'fact_ids':sorted(str(r['id']) for r in rows),
                'source_ids':sorted({str(r['source_id']) for r in rows}),
                'sources':list({str(r['source_id']):{'id':str(r['source_id']),
                    'provider':r['provider'],'url':r.get('url'),'consulted_at':r['consulted_at'],
                    'sha256':r.get('sha256')} for r in rows}.values()),
                'providers':sorted({r['provider'] for r in rows}),
                'consulted_at':sorted({r['consulted_at'].isoformat() for r in rows if r['consulted_at']}),
                'partial':True,'coverage_verified':False}
    monthly=[];cursor=date(start.year,start.month,1)
    while cursor<=end:
        index=cursor.year*12+cursor.month
        following=date(index//12,index%12+1,1)
        rows=[r for r in compatible if cursor<=r['event_date']<following]
        monthly.append({'month':cursor.strftime('%Y-%m'),'start':max(start,cursor),
                        'end':min(end,following.fromordinal(following.toordinal()-1)),**bucket(rows)})
        cursor=following
    municipal=[{'municipality':m,**bucket([r for r in compatible if r['municipality_ibge']==m['ibge']])}
               for m in municipalities]
    states=[]
    for uf in sorted({m['uf'] or 'UF não informada' for m in municipalities}):
        ids={m['ibge'] for m in municipalities if (m['uf'] or 'UF não informada')==uf}
        states.append({'uf':uf,'municipalities':sorted(ids),
                       **bucket([r for r in compatible if r['municipality_ibge'] in ids])})
    return {'version':1,'monthly':monthly,'municipalities':municipal,'states':states,
            'phase':phase,'start':start,'end':end,'filters':filters,
            'unit':product['unit_key'],'classification':product['classification'],
            'partial':True,'source_completeness_claimed':False,
            'limitation':'Quantidades observadas parciais. Meses sem informação não representam zero compras. Não há previsão ou média de consumo.'}


def historical_summary(facts, compatible, product, phase, start, end, cities):
    """Aggregate reconciled facts, not municipal totals or truncated evidence lists.

    The caller owns filtering and (provider, event_identity) reconciliation. Reliable
    PNCP obligations are globally scoped IDs, so one process in two cities counts once.
    Missing process IDs cannot establish that two lines are different processes.
    """
    processes={p for row in facts if (p:=reliable_obligation(row))}
    quantities=[r['quantity'] for r in compatible if r['quantity'] is not None]
    amounts=[r['amount'] for r in compatible if r['amount'] is not None]
    limitation='Totais parciais dos registros encontrados. Não comprovam consumo nem necessidade futura.'
    summary={
        'municipalities_with_records':len({r['municipality_ibge'] for r in facts}),
        'selected_municipalities':len(cities),'observed_records':len(facts),
        'comparable_records':len(compatible),'excluded_records':len(facts)-len(compatible),
        'distinct_processes':len(processes) if processes else None,
        'processes_identified':len(processes),
        'process_identity_complete':bool(facts) and all(reliable_obligation(r) for r in facts),
        'observed_quantity':sum(quantities,Decimal(0)) if quantities else None,
        'documented_amount':sum(amounts,Decimal(0)) if amounts else None,
        'quantity_complete':bool(facts) and len(quantities)==len(facts),
        'amount_complete':bool(facts) and len(amounts)==len(facts),
        'unit':product['unit_key'],'package_signature':product['package_signature'],
        'classification':product['classification'],'phase':phase,'start':start,'end':end,
        'currency':'BRL','partial':True,'source_completeness_claimed':False,
        'limitation':limitation,
        'method':'Current facts reconciled by provider/event_identity; globally identifiable obligations counted once; compatible unit/package only.',
    }
    windows=[]
    for months in (1,3,6,12):
        index=end.year*12+end.month-months
        requested=date(index//12,index%12+1,1);first=max(start,requested)
        selected=[r for r in compatible if first<=r['event_date']<=end]
        values=[r['quantity'] for r in selected if r['quantity'] is not None]
        windows.append({'months':months,'requested_start':requested,'start':first,'end':end,
            'observed_quantity':sum(values,Decimal(0)) if values else None,
            'comparable_records':len(selected),
            'processes_identified':len({p for r in selected if (p:=reliable_obligation(r))}),
            'quantity_complete':bool(selected) and len(values)==len(selected),
            'fact_ids':[str(r['id']) for r in selected],
            'scope_covers_requested_window':start<=requested,'partial':True,
            'monthly_average':None,'recurrence_percentage':None,'limitation':limitation})
    return summary,windows


def reference_prices(ctx,kind,code,code_type,start,end,page=1,transport=None):
    """Existing public contract; one bounded official page with versioned sanitized cache."""
    from .price_queries import query
    return query(ctx,kind,code,code_type,start,end,page,transport)
