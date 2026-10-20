"""Traceable item normalization; only a person can approve canonical equivalence."""
from collections import defaultdict
from datetime import date
from decimal import Decimal
import hashlib,re,unicodedata
from .db import encoded,identifier,normalize
from .security import fail
from . import sources
from . import coverage_inventory

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
    word=fold(value).split(' ',1)[0] if fold(value) else ''
    return ALIASES.get(word,word)


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


def products(ctx,phase='homologado',start=None,end=None,municipalities=None):
    ctx.require('read')
    start=start or date(2020,1,1);end=end or date.today()
    if municipalities is not None:
        municipalities=list(dict.fromkeys(municipalities))
        if not municipalities:fail(422,'Selecione pelo menos um município.','MUNICIPALITY_REQUIRED')
    result=[]
    for product in active_products(ctx):
        refs={(m['id'],m['version']) for m in product['members']}
        rows=ctx.db.all("""SELECT f.id,f.provider,f.classification,f.item_id,f.item_version,f.obligation_id,f.municipality_ibge,f.event_date,
            f.quantity,f.amount,f.unit_price,f.description,f.unit,f.source_id,s.url,s.consulted_at
            FROM procurement_fact f JOIN source_observation s ON s.id=f.source_id
            WHERE f.classification=:dataset AND f.phase=:phase AND f.is_current
              AND (:phase<>'homologado' OR COALESCE(f.metadata->>'eligible_result','true')='true')
              AND f.event_date BETWEEN :start AND :end AND f.item_id=ANY(:ids)
              AND (:all_cities OR f.municipality_ibge=ANY(:cities))
              AND (f.classification='official' OR f.org_id=:o)
            ORDER BY f.event_date,f.id LIMIT 20001""",
            {'dataset':product['classification'],'phase':phase,'start':start,'end':end,'ids':[m['id'] for m in product['members']],'o':ctx.org_id,
             'all_cities':municipalities is None,'cities':municipalities or []})
        if len(rows)>20000:fail(422,'Selecione um período menor para analisar este produto.','CATALOGUE_LIMIT')
        rows=[r for r in rows if (r['item_id'],r['item_version']) in refs]
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


def product_history(ctx,product_id,phase,start,end,municipalities):
    """Observed facts per selected city. Unknown coverage never becomes zero demand."""
    ctx.require('read')
    if not municipalities:fail(422,'Selecione pelo menos um município.','MUNICIPALITY_REQUIRED')
    cities=list(dict.fromkeys(municipalities))
    known=ctx.db.all('SELECT ibge,name,uf FROM municipality WHERE ibge=ANY(:ids) ORDER BY name',{'ids':cities})
    if len(known)!=len(cities):fail(422,'Confira os municípios selecionados.','MUNICIPALITY_UNKNOWN')
    product=next((p for p in active_products(ctx) if str(p['id'])==str(product_id)),None)
    if product is None:fail(404,'Este produto revisado não está disponível.','PRODUCT_NOT_FOUND')
    refs={(m['id'],m['version']) for m in product['members']}
    rows=ctx.db.all("""SELECT f.id,f.provider,f.classification,f.event_identity,f.revision_hash,f.obligation_id,
        f.municipality_ibge,f.item_id,f.item_version,f.event_date,f.quantity,f.unit_price,f.amount,
        f.description,f.unit,f.metadata,f.source_id,s.url,s.consulted_at,s.sha256
        FROM procurement_fact f JOIN source_observation s ON s.id=f.source_id
        WHERE f.classification=:dataset AND (f.classification='official' OR f.org_id=:org)
          AND f.is_current AND f.item_id=ANY(:items) AND f.phase=:phase
          AND f.event_date BETWEEN :start AND :end AND f.municipality_ibge=ANY(:cities)
          AND (:phase<>'homologado' OR COALESCE(f.metadata->>'eligible_result','true')='true')
        ORDER BY f.event_date,f.id LIMIT 20001""",
        {'dataset':product['classification'],'org':ctx.org_id,'items':[m['id'] for m in product['members']],
         'phase':phase,'start':start,'end':end,'cities':cities})
    if len(rows)>20000:fail(422,'Escolha um período menor para analisar este produto.','CATALOGUE_LIMIT')
    # A later revision replaces a fact. A repeated event identity is one observed line,
    # whereas several item lines in one obligation are not several purchases.
    unique={}
    for row in rows:
        if (row['item_id'],row['item_version']) in refs:
            unique[(row['provider'],row['event_identity'])]=row
    by_city=defaultdict(list)
    for row in unique.values():by_city[row['municipality_ibge']].append(row)
    coverage=coverage_inventory.inventory(ctx,start,end,cities) if product['classification']=='official' else {'records':[]}
    output=[]
    for city in known:
        facts=by_city[city['ibge']]
        compatible=[];excluded=[];processes=set();events={};months=set();years=set()
        for row in facts:
            norm=normalized_fact(row)
            reason=[]
            if norm['unit_key']!=product['unit_key']:reason.append('unit_mismatch')
            if norm['package_signature']!=product['package_signature']:reason.append('package_mismatch')
            if norm['confidence']=='incomplete':reason.append('specification_review_required')
            if reason:excluded.append({'fact_id':str(row['id']),'reasons':reason})
            else:compatible.append(row)
            obligation=reliable_obligation(row)
            if obligation:processes.add(obligation)
            if row['event_date']:
                months.add(row['event_date'].strftime('%Y-%m'));years.add(row['event_date'].year)
                if obligation:events.setdefault(obligation,row['event_date'])
        amounts=[r['amount'] for r in compatible if r['amount'] is not None]
        quantities=[r['quantity'] for r in compatible if r['quantity'] is not None]
        prices=[r['unit_price'] for r in compatible if r['unit_price'] is not None]
        dates=sorted(set(events.values()))
        evidence=[{'fact_id':str(r['id']),'provider':r['provider'],'event_identity':r['event_identity'],
            'process_id':r['obligation_id'],'item_id':r['item_id'],'item_version':r['item_version'],
            'description':r['description'],'unit':r['unit'],'quantity':r['quantity'],
            'unit_price':r['unit_price'],'amount':r['amount'],'event_date':r['event_date'],
            'url':r['url'],'consulted_at':r['consulted_at'],'sha256':r['sha256']}
            for r in facts]
        related=[r for r in coverage['records'] if r['municipality_ibge']==city['ibge'] and r['phase']==phase
                 and r['tasks']]
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
            'recurrence_percentage':None,'coverage_state':('demonstration' if product['classification']=='synthetic'
                else 'partial' if related else 'not_collected'),
            'source_completeness_ratio':None,'coverage':related,'excluded_from_totals':excluded,
            'evidence':evidence[:100],'evidence_truncated':len(evidence)>100,
            'notice':'Meses observados não comprovam recorrência. Ausência de registro não comprova ausência de compra.'})
    return normalize({'product':{'id':str(product['id']),'name':product['name'],'unit':product['unit_key'],
        'package_signature':product['package_signature'],'classification':product['classification'],
        'members':product['members'],'reviewed_at':product['created_at']},
        'scope':{'phase':phase,'start':start,'end':end,'municipalities':cities},'municipalities':output,
        'method':'Fatos atuais por identidade de evento; processos por obrigação identificada. Quantidade apenas em unidade e embalagem compatíveis.',
        'source_completeness_claimed':False})


def reference_prices(ctx,kind,code,code_type,start,end,page=1,transport=None):
    """One documented Compras.gov.br page; never a municipal coverage assertion."""
    ctx.require('sources.sync')
    if end<start or (end-start).days>366:fail(422,'Escolha até um ano para comparar preços.')
    if not re.fullmatch(r'\d{1,12}',code):fail(422,'Confira o código oficial do catálogo.')
    if kind=='material':
        if code_type not in ('codigoItemCatalogo','codigoPdm'):fail(422,'Escolha o tipo de código do material.')
        endpoint='https://dadosabertos.compras.gov.br/modulo-pesquisa-preco/1_consultarMaterial'
        params={'tipo':code_type,'codigo':code}
    elif kind=='servico':
        if code_type!='codigoItemCatalogo':fail(422,'Serviços usam o código do item de catálogo.')
        endpoint='https://dadosabertos.compras.gov.br/modulo-pesquisa-preco/3_consultarServico'
        params={'codigoItemCatalogo':code}
    else:fail(422,'Escolha material ou serviço.')
    params.update({'dataCompraInicio':start.isoformat(),'dataCompraFim':end.isoformat(),
        'pagina':page,'tamanhoPagina':10})
    provider='COMPRAS_PRECOS_MATERIAL' if kind=='material' else 'COMPRAS_PRECOS_SERVICO'
    url,status,raw,data=sources.cached_get(ctx,provider,endpoint,params,transport)
    if data is None:data={'resultado':[],'totalPaginas':0,'totalRegistros':0}
    if not isinstance(data,dict) or not isinstance(data.get('resultado'),list):raise sources.SourceFault('INVALID_PRICE_FORMAT')
    records=[]
    for row in data['resultado'][:10]:
        value=str(row.get('niFornecedor') or '')
        records.append({'purchase_id':row.get('idCompra'),'item_number':row.get('numeroItemCompra'),
            'catalogue_code':row.get('codigoItemCatalogo'),'description':row.get('descricaoItem'),
            'quantity':sources.documented_number(row.get('quantidade')),
            'unit_price':sources.documented_number(row.get('precoUnitario')),
            'unit':row.get('nomeUnidadeFornecimento') or row.get('siglaUnidadeFornecimento'),
            'purchase_date':row.get('dataCompra'),'result_date':row.get('dataResultado'),
            'uasg':row.get('codigoUasg'),'agency':row.get('nomeOrgao'),
            'municipality_code':row.get('codigoMunicipio'),'state':row.get('estado'),
            'supplier_cnpj':value if re.fullmatch(r'\d{14}',value) else None})
    safe={'resultado':records,'totalPaginas':data.get('totalPaginas'),'totalRegistros':data.get('totalRegistros')}
    sid=sources.observe(ctx,provider,url,status,encoded(safe).encode(),
        {'scope':{'kind':kind,'code':code,'code_type':code_type,'start':start,'end':end,'page':page},
         'original_response_sha256':hashlib.sha256(raw).hexdigest(),'person_names_excluded':True,
         'municipal_coverage_claimed':False})
    observation=ctx.db.one('SELECT consulted_at,sha256 FROM source_observation WHERE id=:id',{'id':sid})
    return normalize({'records':records,'url':url,'consulted_at':observation['consulted_at'],
        'stored_sha256':observation['sha256'],'original_response_sha256':hashlib.sha256(raw).hexdigest(),
        'page':page,'total_pages_reported':data.get('totalPaginas'),'total_records_reported':data.get('totalRegistros'),
        'municipal_coverage_claimed':False,'price_comparability_review_required':True,
        'message':'Preços observados em compras públicas. Compare especificação, unidade, local e data antes de usar como referência.'})
