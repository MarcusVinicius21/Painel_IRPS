"""Auditable opportunity analysis over one phase, reviewed equivalence and explicit coverage."""
from collections import Counter,defaultdict
from datetime import date,timedelta
from decimal import Decimal
from statistics import median
import calendar,hashlib,json,re
from .db import encoded,identifier,normalize
from .security import fail
from .schemas import ScenarioCreate,Snapshot
from . import scenarios,catalogue

VERSION='opportunities-v1'
MAX_FACTS=20000

def item_key(item,version,unit):
    return 'i-'+hashlib.sha256(encoded([item,version,unit]).encode()).hexdigest()[:24]

def selected_cities(ctx,f):
    known={r['ibge'] for r in ctx.db.all('SELECT ibge FROM municipality')}
    if set(f.municipalities)-known:fail(422,'Confira os códigos dos municípios selecionados.')
    group_cities=set()
    for group in f.groups:
        row=ctx.db.one('SELECT municipalities FROM municipality_group WHERE org_id=:o AND id=:i',{'o':ctx.org_id,'i':group})
        if not row:fail(404,'Este grupo de municípios não está disponível.')
        group_cities.update(row['municipalities'])
    if f.municipalities and f.groups:return sorted(set(f.municipalities)&group_cities)
    if f.municipalities:return sorted(set(f.municipalities))
    if group_cities:return sorted(group_cities)
    # A blank filter starts from completed collections for this dataset. This avoids
    # suggesting that all known municipalities have been covered just because they
    # exist in the catalogue. It falls back to the catalogue before any collection.
    scoped=set()
    for row in ctx.db.all("SELECT scope FROM history_collection WHERE org_id=:o AND dataset=:d AND state='completed'",{'o':ctx.org_id,'d':f.dataset}):
        scope=row['scope'] if isinstance(row['scope'],dict) else json.loads(row['scope'])
        scoped.update(scope.get('municipalities',[]))
    return sorted(scoped or known)

def facts(ctx,f,include_inactive=False):
    ctx.require('read');cities=selected_cities(ctx,f)
    if not cities:return [],cities
    where=['f.classification=:dataset','f.phase=:phase','f.event_date BETWEEN :start AND :end','f.item_id IS NOT NULL','f.unit IS NOT NULL',
           'f.municipality_ibge=ANY(:cities)']
    if not include_inactive:where.extend(['f.is_current',"COALESCE(f.metadata->>'cancelled','false')<>'true'","COALESCE(f.metadata->>'eligible_result','true')<>'false'"])
    params={'dataset':f.dataset,'phase':f.phase,'start':f.start,'end':f.end,'cities':cities,'cap':MAX_FACTS+1}
    for key,col in [('buyers','f.buyer_id::text'),('item_ids','f.item_id'),('suppliers',"f.metadata->'supplier'->>'cnpj'"),('months','extract(month FROM f.event_date)::int'),('years','extract(year FROM f.event_date)::int'),('modalities',"f.metadata->>'modality'")]:
        values=getattr(f,key)
        if values:
            params[key]=[str(x) for x in values] if key=='modalities' else values;where.append(col+'=ANY(:'+key+')')
    for name,col,operator in [('min_quantity','quantity','>='),('max_quantity','quantity','<='),('min_amount','amount','>='),('max_amount','amount','<='),('min_price','unit_price','>='),('max_price','unit_price','<=')]:
        if getattr(f,name) is not None:where.append('f.'+col+operator+':'+name);params[name]=getattr(f,name)
    if f.q:where.append('(f.description ILIKE :q OR b.name ILIKE :q OR m.name ILIKE :q)');params['q']='%'+f.q+'%'
    rows=ctx.db.all("""SELECT f.*,i.name AS item_name,i.family,i.step,b.name AS buyer_name,b.cnpj AS buyer_cnpj,
        b.government_level,m.name AS municipality_name,m.uf,s.url AS source_url,s.consulted_at,s.sha256 AS source_sha256
        FROM procurement_fact f JOIN item_version i ON i.id=f.item_id AND i.version=f.item_version
        LEFT JOIN buyer b ON b.id=f.buyer_id JOIN municipality m ON m.ibge=f.municipality_ibge
        JOIN source_observation s ON s.id=f.source_id WHERE """+' AND '.join(where)+' ORDER BY f.event_date,f.event_identity LIMIT :cap',params)
    if len(rows)>MAX_FACTS:fail(422,'O recorte tem muitos registros para esta análise. Reduza o período ou selecione municípios.','ANALYSIS_LIMIT')
    if f.categories:
        reviewed=(catalogue.active_products(ctx) if f.grouping=='canonical' else
            ctx.db.all('SELECT members FROM opportunity_equivalence WHERE org_id=:o AND category=ANY(:categories)',{'o':ctx.org_id,'categories':f.categories}))
        reviewed=[group for group in reviewed if group['category'] in f.categories]
        members={(m['id'],m['version']) for e in reviewed for m in e['members']}
        rows=[r for r in rows if (r['metadata'].get('category') or r['family']) in f.categories or (r['item_id'],r['item_version']) in members]
    return rows,cities

def coverage(ctx,f,cities):
    days=[];current=f.start
    while current<=f.end:
        if (not f.months or current.month in f.months) and (not f.years or current.year in f.years):days.append(current)
        current+=timedelta(days=1)
    denominator=len(days)*len(cities)
    if f.dataset=='official' and f.phase=='publicado_estimado' and not f.modalities:
        return {'phase':f.phase,'verified_days':None,'requested_city_days':denominator,
            'verified_ratio':None,'complete_months':[],'proof':[],'status':'not_established',
            'dataset':f.dataset,'message':'Escolha as modalidades para medir as consultas planejadas. Sem esse recorte, não há percentual verificável.'},set()
    if f.dataset=='official' and f.phase!='publicado_estimado':
        # Result endpoints enumerate known items reached through publication searches.
        # Their consultation time is evidence of that item query, never a complete
        # date window for all homologations in the municipality.
        provider='PNCP_RESULTADOS' if f.phase=='homologado' else None
        observations=ctx.db.all("""SELECT c.id AS collection_id,t.id AS task_id,p.record_count,p.created_at,
            s.url,s.sha256,s.consulted_at,i.municipality_ibge
            FROM history_page p JOIN history_task t ON t.org_id=p.org_id AND t.id=p.task_id
            JOIN history_collection c ON c.org_id=p.org_id AND c.id=p.collection_id
            JOIN source_observation s ON s.id=p.source_id
            JOIN procurement_fact i ON i.id=(t.arguments->>'procurement_id')::uuid
            WHERE p.org_id=:o AND c.dataset='official' AND t.provider=:provider
              AND i.municipality_ibge=ANY(:cities)
              AND EXISTS (SELECT 1 FROM procurement_fact result_fact
                WHERE result_fact.source_id=p.source_id AND result_fact.provider='PNCP_RESULTADOS'
                  AND result_fact.event_date BETWEEN :start AND :end
                  AND result_fact.municipality_ibge=ANY(:cities))
            ORDER BY p.created_at DESC,p.task_id LIMIT 501""",{'o':ctx.org_id,'provider':provider,'cities':cities,
                'start':f.start,'end':f.end}) if provider and cities else []
        proof=[{'phase':f.phase,'collection_id':str(p['collection_id']),'task_id':str(p['task_id']),
            'municipality_ibge':p['municipality_ibge'],'record_count':p['record_count'],
            'url':p['url'],'sha256':p['sha256'],'consulted_at':p['consulted_at']}
            for p in observations[:30]]
        observed=bool(observations)
        message=('Resultados foram consultados para itens conhecidos. Isso não comprova todos os resultados homologados no período.'
            if provider and observed else 'Ainda não há prova de cobertura desta situação no período. Registros isolados não tornam o histórico completo.')
        return {'phase':f.phase,'verified_days':None,'requested_city_days':denominator,
            'verified_ratio':None,'complete_months':[],'proof':proof,'proof_truncated':len(observations)>30,
            'observed_result_pages':len(observations) if provider else 0,
            'status':'observed_items_only' if observed else 'not_established','dataset':f.dataset,
            'message':message},set()
    collections=ctx.db.all("SELECT id,scope,pages,updated_at FROM history_collection WHERE org_id=:o AND dataset=:d AND state='completed' ORDER BY id",{'o':ctx.org_id,'d':f.dataset})
    windows=defaultdict(list);proof=[]
    for c in collections:
        s=c['scope']
        # Official collection indexes publication dates, not dates of homologation/payment.
        compatible=(f.dataset=='official' and f.phase=='publicado_estimado' and s.get('publications') and s.get('items')) or (f.dataset=='synthetic' and s.get('event_dates_complete') is True)
        if not compatible or (f.dataset=='official' and (not f.modalities or not set(f.modalities)<=set(s.get('modalities',[])))):continue
        start=date.fromisoformat(s['start']);end=date.fromisoformat(s['end'])
        for city in set(cities)&set(s.get('municipalities',[])):windows[city].append((start,end))
        proof.append({'collection_id':str(c['id']),'start':s['start'],'end':s['end'],'pages':c['pages'],'dataset':f.dataset})
    covered={city:{d for d in days if any(a<=d<=b for a,b in windows[city])} for city in cities}
    count=sum(len(x) for x in covered.values())
    ratio=Decimal(count)/denominator if denominator else Decimal(0)
    months={d.strftime('%Y-%m') for d in days}
    complete_months={month for month in months if cities and all(all(d in covered[c] for d in days if d.strftime('%Y-%m')==month) for c in cities)
        and f.start<=date.fromisoformat(month+'-01') and f.end>=date(int(month[:4]),int(month[5:]),calendar.monthrange(int(month[:4]),int(month[5:]))[1])}
    return {'phase':f.phase,'verified_days':count,'requested_city_days':denominator,'verified_ratio':ratio,'complete_months':sorted(complete_months),'proof':proof[:30],
        'status':'complete_scope' if ratio==1 else 'partial_or_unverified','dataset':f.dataset,
        'message':'Cobertura restrita ao recorte e às modalidades coletadas. Não comprova todo o histórico municipal.'},complete_months

def pct_change(before,after):
    return None if before is None or after is None or before==0 else (after-before)/before*100

def indicators(rows,f,complete_months):
    buckets=defaultdict(list)
    for row in rows:buckets[row['event_date'].strftime('%Y-%m')].append(row)
    monthly=[];cursor=date(f.start.year,f.start.month,1)
    while cursor<=f.end:
        label=cursor.strftime('%Y-%m');r=buckets[label];observed=bool(r);complete=label in complete_months
        amounts=[x['amount'] for x in r if x['amount'] is not None];quantities=[x['quantity'] for x in r if x['quantity'] is not None]
        monthly.append({'month':label,'purchases':len({x['obligation_id'] for x in r}) if observed or complete else None,
            'known_quantity':sum(quantities,Decimal(0)) if quantities or complete else None,
            'known_amount':sum(amounts,Decimal(0)) if amounts or complete else None,'amount_complete':complete and all(x['amount'] is not None for x in r),
            'coverage_complete':complete,'records':len(r)})
        cursor=date(cursor.year+1,1,1) if cursor.month==12 else date(cursor.year,cursor.month+1,1)
    annual=[]
    for year in sorted({int(m['month'][:4]) for m in monthly}):
        months=[m for m in monthly if m['month'].startswith(str(year))]
        comparable=len(months)==12 and all(m['amount_complete'] for m in months)
        amounts=[m['known_amount'] for m in months if m['known_amount'] is not None]
        value=sum(amounts,Decimal(0)) if amounts else None
        previous=next((a for a in annual if a['year']==year-1 and a['comparable_full_year']),None)
        annual.append({'year':year,'known_amount':value,'purchases':len({r['obligation_id'] for r in rows if r['event_date'].year==year}),
            'comparable_full_year':comparable,'variation_pct':pct_change(previous['known_amount'],value) if comparable and previous else None})
    city_counts=Counter()
    for city in {r['municipality_ibge'] for r in rows}:city_counts[city]=len({r['obligation_id'] for r in rows if r['municipality_ibge']==city})
    total=sum(city_counts.values());concentration=sum((Decimal(n)/total)**2 for n in city_counts.values())*10000 if total else None
    dates=sorted({r['event_date'] for r in rows});intervals=[(b-a).days for a,b in zip(dates,dates[1:])]
    active=len(buckets);covered_active=len(set(buckets)&set(complete_months))
    recurrence=Decimal(covered_active)/len(complete_months)*100 if complete_months else None
    price_dates=[r['event_date'] for r in rows if r['unit_price'] is not None and r['metadata'].get('currency','BRL')=='BRL']
    price_end=max(price_dates) if price_dates else f.end;price_start=price_end-timedelta(days=90)
    price_rows=[r for r in rows if r['unit_price'] is not None and r['metadata'].get('currency','BRL')=='BRL' and price_start<=r['event_date']<=price_end]
    prices=[r['unit_price'] for r in price_rows];priced=sum(r['unit_price'] is not None and r['metadata'].get('currency','BRL')=='BRL' for r in rows)
    seasonal=None
    full_years=[a['year'] for a in annual if a['comparable_full_year']]
    if len(full_years)>=2:
        seasonal=[{'month':m,'purchases':sum(x['purchases'] or 0 for x in monthly if int(x['month'][:4]) in full_years and int(x['month'][5:])==m)} for m in range(1,13)]
    return {'records':len(rows),'purchases':len({r['obligation_id'] for r in rows}),'municipalities':len(city_counts),'active_months':active,
        'monthly':monthly,'annual':annual,'recurrence_pct':recurrence,'observed_mean_interval_days':Decimal(sum(intervals))/len(intervals) if intervals else None,
        'concentration_hhi':concentration,'price':{'count':len(prices),'min':min(prices) if prices else None,'median':median(prices) if prices else None,'max':max(prices) if prices else None,
            'start':price_start,'end':price_end,'currency':'BRL','known_price_pct':Decimal(priced)/len(rows)*100 if rows else None,
            'notice':'Preços nominais da mesma unidade, em até 90 dias. Frete, tributos e condições comerciais precisam de revisão.'},
        'seasonality':seasonal,'seasonality_notice':None if seasonal else 'Faltam dois anos completos comparáveis para avaliar sazonalidade.',
        'known_amount':sum((r['amount'] for r in rows if r['amount'] is not None),Decimal(0)) if any(r['amount'] is not None for r in rows) else None,
        'amount_complete':all(r['amount'] is not None for r in rows),'future_purchase_promised':False}

def score(metrics,review,cov,weights,scope_count):
    missing=[]
    if metrics['purchases']<3 or metrics['active_months']<3:missing.append('Faltam compras em pelo menos três meses diferentes.')
    if metrics['municipalities']<2:missing.append('Faltam dois municípios compradores no recorte.')
    if cov['verified_ratio'] is None:missing.append('A cobertura desta situação ainda não foi comprovada por período e município.')
    elif cov['verified_ratio']<Decimal('.8') or len(cov['complete_months'])<12:missing.append('Faltam 12 meses com cobertura verificável de ao menos 80% do recorte.')
    if metrics['price']['count']<3:missing.append('Faltam três preços da mesma unidade no intervalo comparável.')
    if not review:missing.append('Confira os seis critérios de fornecimento e a viabilidade jurídica e operacional.')
    elif review['data']['legal']!='viable' or review['data']['operational']!='viable':missing.append('A revisão jurídica e operacional ainda não indica viabilidade.')
    if missing:return {'value':None,'state':'needs_review_or_data','missing':missing,'formula_version':VERSION,'weights':weights}
    data=review['data'];ease=sum((Decimal(c['rating']-1)*25 for c in data['criteria'].values()),Decimal(0))/6
    components={'recurrence':metrics['recurrence_pct'],'spread':Decimal(metrics['municipalities'])/max(1,scope_count)*100,
        'price':metrics['price']['known_price_pct'],'ease':ease}
    if any(v is None for v in components.values()):return {'value':None,'state':'insufficient_data','missing':['Há um componente sem dados.'],'weights':weights}
    value=sum(components[k]*weights[k]/100 for k in weights).quantize(Decimal('.01'))
    return {'value':value,'state':'reviewed_analysis_priority','components':components,'weights':weights,'missing':[],
        'formula_version':VERSION,'notice':'Prioridade de análise no recorte. Não garante compra, lucro ou autorização administrativa.'}

def equivalence_index(equivalences):
    assigned={};definitions={}
    for e in equivalences:
        key='g-'+str(e['id']);definitions[key]={'key':key,'name':e['name'],'category':e['category'],'unit':e['unit'],'members':e['members'],
            'equivalence':{'reviewed':True,'justification':e['justification'],'evidence':e['evidence'],'reviewed_at':e['created_at']}}
        for m in e['members']:
            member=(m['id'],m['version'])
            if member in assigned:fail(409,'Um item aparece em dois grupos equivalentes. Revise os grupos antes da análise.','EQUIVALENCE_OVERLAP')
            assigned[member]=key
    return assigned,definitions

def review_context_fingerprint(rows,definition,filters,cities,cov):
    return hashlib.sha256(encoded({'version':VERSION,'rows':[(str(r['id']),r['revision_hash']) for r in rows],
        'definition':definition,'filters':filters.model_dump(exclude={'offset','limit','order','weights'}),
        'municipalities':cities,'coverage':cov}).encode()).hexdigest()

def build(ctx,f):
    rows,cities=facts(ctx,f);cov,complete=coverage(ctx,f,cities)
    if f.grouping=='canonical':
        assigned={};definitions={}
        for product in catalogue.active_products(ctx):
            if product['classification']!=f.dataset:continue
            key='p-'+str(product['id'])
            definitions[key]={'key':key,'name':product['name'],'category':product['category'],
                'unit':product['unit_key'],'package_signature':product['package_signature'],
                'members':product['members'],'canonical_product':True,
                'equivalence':{'reviewed':True,'justification':product['justification'],
                    'evidence':product['evidence'],'reviewed_at':product['created_at']}}
            for member in product['members']:
                ref=(member['id'],member['version'])
                if ref in assigned:fail(409,'Um item aparece em dois produtos revisados. Confira o catálogo.','CANONICAL_OVERLAP')
                assigned[ref]=key
    else:
        equivalences=ctx.db.all('SELECT * FROM opportunity_equivalence WHERE org_id=:o ORDER BY created_at DESC,id',{'o':ctx.org_id})
        assigned,definitions=equivalence_index(equivalences)
    grouped=defaultdict(list)
    for row in rows:
        key=assigned.get((row['item_id'],row['item_version'])) or item_key(row['item_id'],row['item_version'],row['unit'])
        if key not in definitions:definitions[key]={'key':key,'name':row['item_name'],'category':row['metadata'].get('category') or row['family'],'unit':row['unit'],
            'members':[{'id':row['item_id'],'version':row['item_version']}],'equivalence':{'reviewed':False,'same_item_version_only':True}}
        grouped[key].append(row)
    if len(grouped)>1000:fail(422,'Selecione uma categoria ou reduza o período para comparar até mil grupos por vez.')
    reviews={r['opportunity_key']:r for r in ctx.db.all('SELECT DISTINCT ON (opportunity_key) opportunity_key,revision,data,context_fingerprint,created_at,actor_id FROM opportunity_review WHERE org_id=:o ORDER BY opportunity_key,revision DESC',{'o':ctx.org_id})}
    result=[]
    for key,records in grouped.items():
        d=definitions[key];metrics=indicators(records,f,complete)
        latest=reviews.get(key)
        context_fingerprint=review_context_fingerprint(records,d,f,cities,cov)
        review=latest if latest and latest['context_fingerprint']==context_fingerprint else None
        fingerprint=hashlib.sha256(encoded({'version':VERSION,'rows':[(str(r['id']),r['revision_hash']) for r in records],'definition':d,'filters':f.model_dump(exclude={'offset','limit','order'})}).encode()).hexdigest()
        result.append({**d,'metrics':metrics,'review':review,'review_revision':latest['revision'] if latest else 0,
            'review_status':'current' if review else 'context_changed' if latest else 'not_reviewed',
            'review_context_fingerprint':context_fingerprint,'priority':score(metrics,review,cov,f.weights,len(cities)),
            'classification':f.dataset,'phase':f.phase,'fingerprint':fingerprint,'_rows':records})
    return result,cov,cities

def query(ctx,f):
    candidates,cov,cities=build(ctx,f)
    key={'recurrence':lambda r:(r['metrics']['active_months'],r['metrics']['purchases']),
         'municipalities':lambda r:(r['metrics']['municipalities'],r['metrics']['purchases']),
         'value':lambda r:(r['metrics']['known_amount'] is not None,r['metrics']['known_amount'] or Decimal(0),r['metrics']['purchases']),
         'priority':lambda r:(r['priority']['value'] is not None,r['priority']['value'] or Decimal(0),r['metrics']['purchases'])}[f.order]
    candidates.sort(key=key,reverse=True)
    summaries=[{k:v for k,v in c.items() if k!='_rows'} for c in candidates[f.offset:f.offset+f.limit]]
    return normalize({'records':summaries,'total':len(candidates),'offset':f.offset,'limit':f.limit,'coverage':cov,'municipality_count':len(cities),
        'record_limit':MAX_FACTS,'message':'Registros de uma única situação. Informação ausente não significa ausência de compras.','formula_version':VERSION})

def detail(ctx,key,f,offset=0,limit=100):
    candidates,cov,cities=build(ctx,f);candidate=next((c for c in candidates if c['key']==key),None)
    if not candidate:fail(404,'Esta oportunidade não apareceu no recorte. Confira os filtros.')
    rows=candidate.pop('_rows');candidate['coverage']=cov
    candidate['records']=rows[offset:offset+limit];candidate['records_total']=len(rows);candidate['records_offset']=offset;candidate['records_limit']=limit
    candidate['buyers']=[{'ibge':city,'name':next(r['municipality_name'] for r in rows if r['municipality_ibge']==city),
        'purchases':len({r['obligation_id'] for r in rows if r['municipality_ibge']==city}),
        'known_amount':sum((r['amount'] for r in rows if r['municipality_ibge']==city and r['amount'] is not None),Decimal(0))} for city in sorted({r['municipality_ibge'] for r in rows})]
    suppliers={r['metadata']['supplier']['cnpj']:r['metadata']['supplier'] for r in rows if r['metadata'].get('supplier',{}).get('cnpj')}
    candidate['suppliers']=list(suppliers.values())
    obligations=sorted({r['obligation_id'] for r in rows})
    candidate['contracts']=ctx.db.all("SELECT f.id,f.description,f.amount,f.phase,f.event_date,f.metadata,s.url AS source_url FROM procurement_fact f JOIN source_observation s ON s.id=f.source_id WHERE f.classification=:d AND f.is_current AND f.provider='PNCP_CONTRATOS' AND f.obligation_id=ANY(:ob) ORDER BY f.event_date DESC LIMIT 100",{'d':f.dataset,'ob':obligations})
    candidate['contract_notice']='Contratos vinculados ficam separados. Seus valores não são somados aos itens homologados.'
    return normalize(candidate)

def group_create(ctx,body):
    ctx.require('opportunity.manage');known={r['ibge'] for r in ctx.db.all('SELECT ibge FROM municipality')}
    if len(set(body.municipalities))!=len(body.municipalities) or set(body.municipalities)-known:fail(422,'Confira os municípios deste grupo.')
    gid=identifier();ctx.db.execute('INSERT INTO municipality_group(org_id,id,name,municipalities,created_by) VALUES (:o,:i,:n,CAST(:m AS jsonb),:a)',{'o':ctx.org_id,'i':gid,'n':body.name,'m':encoded(body.municipalities),'a':ctx.actor_id})
    ctx.audit('opportunity.municipality_group',gid);return {'id':gid}

def equivalence_create(ctx,body):
    ctx.require('opportunity.manage');members=[m.model_dump() for m in body.members]
    if len({(m['id'],m['version']) for m in members})!=len(members):fail(422,'Remova os itens repetidos.')
    classes=set()
    for m in members:
        item=ctx.db.one('SELECT unit,classification FROM item_version WHERE id=:i AND version=:v',{'i':m['id'],'v':m['version']})
        if not item or item['unit']!=body.unit:fail(422,'Os itens precisam ter a mesma unidade documentada. Conversão exige outro método revisado.')
        classes.add(item['classification'])
    if len(classes)!=1:fail(422,'Não misture itens oficiais e fictícios na equivalência.')
    ctx.db.execute('SELECT pg_advisory_xact_lock(hashtextextended(:k,0))',{'k':ctx.org_id+':equivalence-members'})
    requested={(m['id'],m['version']) for m in members}
    for existing in ctx.db.all('SELECT members FROM opportunity_equivalence WHERE org_id=:o',{'o':ctx.org_id}):
        if requested & {(m['id'],m['version']) for m in existing['members']}:
            fail(409,'Um item já pertence a outro grupo equivalente. Revise o grupo existente.','EQUIVALENCE_OVERLAP')
    gid=identifier();ctx.db.execute('INSERT INTO opportunity_equivalence(org_id,id,name,category,unit,members,justification,evidence,reviewed_by) VALUES (:o,:i,:n,:c,:u,CAST(:m AS jsonb),:j,:e,:a)',{'o':ctx.org_id,'i':gid,'n':body.name,'c':body.category,'u':body.unit,'m':encoded(members),'j':body.justification,'e':body.evidence,'a':ctx.actor_id})
    ctx.audit('opportunity.equivalence_reviewed',gid,{'members':len(members)});return {'id':gid,'key':'g-'+gid}

def review_save(ctx,key,body):
    ctx.require('opportunity.manage')
    if not re.fullmatch(r'(i-[0-9a-f]{24}|[gp]-[0-9a-f-]{36})',key):fail(422,'Confira a oportunidade escolhida.')
    ctx.db.execute('SELECT pg_advisory_xact_lock(hashtextextended(:k,0))',{'k':ctx.org_id+':review:'+key})
    candidates,_,_=build(ctx,body.filters)
    current=next((candidate for candidate in candidates if candidate['key']==key),None)
    if not current:fail(404,'Esta oportunidade não apareceu no recorte. Confira os filtros.')
    if current['review_context_fingerprint']!=body.expected_context_fingerprint:
        fail(409,'O recorte mudou. Abra a análise atual antes de salvar a revisão.','REVIEW_CONTEXT_CHANGED')
    old=ctx.db.one('SELECT max(revision) AS revision FROM opportunity_review WHERE org_id=:o AND opportunity_key=:k',{'o':ctx.org_id,'k':key})['revision'] or 0
    if old!=body.revision:fail(409,'A revisão mudou. Atualize antes de salvar.')
    data=body.model_dump(exclude={'revision','filters','expected_context_fingerprint'});rev=old+1
    ctx.db.execute('INSERT INTO opportunity_review(org_id,opportunity_key,revision,data,context_fingerprint,actor_id) VALUES (:o,:k,:v,CAST(:d AS jsonb),:f,:a)',{'o':ctx.org_id,'k':key,'v':rev,'d':encoded(data),'f':current['review_context_fingerprint'],'a':ctx.actor_id})
    ctx.audit('opportunity.viability_reviewed',key,{'revision':rev,'legal':body.legal,'operational':body.operational});return {'revision':rev}

def to_scenario(ctx,key,body,idempotency_key):
    ctx.require('scenario.write')
    if not idempotency_key or not 8<=len(idempotency_key)<=120:fail(422,'Atualize a página antes de criar o rascunho.')
    digest=hashlib.sha256(encoded(body.model_dump()).encode()).hexdigest()
    ctx.db.execute('SELECT pg_advisory_xact_lock(hashtextextended(:k,0))',{'k':ctx.org_id+ctx.actor_id+idempotency_key})
    previous=ctx.db.one("SELECT * FROM job WHERE org_id=:o AND actor_id=:a AND kind='opportunity.scenario' AND idempotency_key=:k",{'o':ctx.org_id,'a':ctx.actor_id,'k':idempotency_key})
    if previous:
        if previous['input_hash']!=digest:fail(409,'Esta ação já foi usada para outro rascunho.')
        return scenarios.get_scenario(ctx,previous['result']['scenario_id'])
    d=detail(ctx,key,body.filters)
    if d['fingerprint']!=body.expected_fingerprint:fail(409,'Os dados mudaram. Confira a oportunidade antes de criar o cenário.')
    if len(set(body.participants))!=len(body.participants) or set(body.participants)-{b['ibge'] for b in d['buyers']}:fail(422,'Escolha os municípios compradores apresentados nesta oportunidade.')
    representative=d['members'][0]
    snapshot=Snapshot(period=body.period,participants=body.participants,items=[representative],inputs={},prices={},allocations={},
        justification='Rascunho a partir de '+key+'. Histórico não comprova necessidade futura. Confirmar equivalência, estoque, recebimentos, anuência e revisão jurídica/operacional. Fonte do recorte: '+body.expected_fingerprint)
    result=scenarios.create_scenario(ctx,ScenarioCreate(title=body.title,classification='synthetic' if body.filters.dataset=='synthetic' else 'internal',snapshot=snapshot))
    ctx.db.execute("INSERT INTO job(org_id,id,actor_id,kind,idempotency_key,input_hash,arguments,state,result) VALUES (:o,:i,:a,'opportunity.scenario',:k,:h,'{}','completed',CAST(:r AS jsonb))",{'o':ctx.org_id,'i':identifier(),'a':ctx.actor_id,'k':idempotency_key,'h':digest,'r':encoded({'scenario_id':result['id']})})
    ctx.audit('opportunity.scenario_created',result['id'],{'opportunity':key,'inputs_inferred':False});return result
