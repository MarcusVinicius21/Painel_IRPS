"""Monthly request evidence, never market or municipal purchase completeness."""
from collections import defaultdict
from datetime import date
from decimal import Decimal
from . import campaign_audit


def summarize(groups):
    planned=sum(g['materialized_tasks'] for g in groups)
    verified=sum(g['verified_pages'] for g in groups)
    known=bool(groups) and all(g['expected_pages'] is not None for g in groups)
    denominator=sum(g['expected_pages'] for g in groups) if known else None
    ratio=str(Decimal(verified)*100/denominator) if denominator and verified<=denominator else None
    conflicts=any(g.get('count_reconciliation')=='mismatch' or g['errors'] for g in groups)
    if conflicts:ratio=None
    failures=sum(sum(n for state,n in g['task_states'].items() if state in ('blocked','quarantined','failed','failed_retryable')) for g in groups)
    state=('not_collected' if not groups else 'blocked' if not verified and failures else
        'not_collected' if not verified else 'needs_review' if conflicts else 'available'
        if all(g.get('fully_reconciled',False) and not g['source_errors'] for g in groups) else 'partial')
    return {'coverage_status':state,'materialized_requests':planned,'verified_requests':verified,
        'expected_pages':denominator,'request_reconciliation_pct':ratio,
        'reconciled_groups':sum(bool(g['pagination_reconciled']) for g in groups),'groups':len(groups),
        'failed_or_blocked':failures,'last_sync':max((g.get('last_sync') for g in groups if g.get('last_sync')),default=None),
        'municipal_purchase_completeness':None,'denominator':'Documented pages of the materialized request prefixes; not purchases or the whole municipality.'}


def matrix(ctx,start,end,municipalities=()):
    report=campaign_audit.audit(ctx,start,end,municipalities,all_groups=True)
    cities=report['scope']['municipalities'];groups=report['groups']
    cnpj_cities=defaultdict(set)
    for b in ctx.db.all("SELECT cnpj,municipality_ibge FROM buyer WHERE org_id=:o AND classification='official' AND government_level='M'",{'o':ctx.org_id}):
        if b['cnpj'] and b['municipality_ibge']:cnpj_cities[b['cnpj']].add(b['municipality_ibge'])
    parent_ids=sorted({g['scope'].get('procurement_id') or g['scope'].get('contract_id') for g in groups if g['scope'].get('procurement_id') or g['scope'].get('contract_id')})
    parents={}
    if parent_ids:
        parents={str(r['id']):r for r in ctx.db.all('''SELECT f.id,f.municipality_ibge,f.event_date,f.metadata,b.cnpj,b.government_level
            FROM procurement_fact f JOIN buyer b ON b.id=f.buyer_id AND b.org_id=f.org_id
            WHERE f.org_id=:o AND f.id=ANY(CAST(:ids AS uuid[])) AND f.classification='official' ''',{'o':ctx.org_id,'ids':parent_ids})}
    grouped=defaultdict(list);months=[];cursor=date(start.year,start.month,1)
    while cursor<=end:
        months.append(cursor.strftime('%Y-%m'));cursor=date(cursor.year+(cursor.month==12),cursor.month%12+1,1)
    providers=sorted({g['provider'] for g in groups})
    for g in groups:
        scope=g['scope'];city=scope.get('municipality_ibge');mapped={city} if city else cnpj_cities.get(scope.get('cnpj'),set())
        begin=scope.get('start_date');finish=scope.get('end_date')
        if not begin:
            parent=parents.get(scope.get('procurement_id') or scope.get('contract_id'))
            if parent and parent['government_level']=='M':
                mapped={parent['municipality_ibge']};begin=str(parent['metadata'].get('publication_date') or parent['event_date'])[:10];finish=begin
            else:mapped=set()
        if not begin or not finish:continue
        for city in mapped & set(cities):
            for month in months:
                if begin[:7]<=month<=finish[:7]:grouped[(city,month,g['provider'])].append(g)
    cells=[{'municipality_ibge':city,'month':month,'provider':provider,
        'period_basis':campaign_audit.PERIOD_BASIS.get(provider,'unknown'),
        **summarize(grouped[(city,month,provider)])}
        for city in cities for month in months for provider in providers]
    return {'records':cells,'start':str(start),'end':str(end),'municipalities':cities,'months':months,
        'origin':'municipal_request_evidence','source_completeness_claimed':False,
        'notice':'Consultas da coleção municipal geral. Não são percentuais de compras nem de cobertura do portfólio.',
        'source_blocks':[{'provider':'TCE_MG','state':'blocked','reason':'Recurso oficial não validado'},
            {'provider':'PORTAL_IPATINGA','state':'needs_review','reason':'Exportação devolveu período diferente'},
            {'provider':'PORTAL_TIMOTEO','state':'blocked','reason':'Acesso anônimo retornou 403'}]}
