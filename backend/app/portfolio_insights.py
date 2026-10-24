"""Identity-level observations, not aggregate demand, consumption or predictions."""
from collections import defaultdict
from decimal import Decimal
from statistics import median
from . import catalogue,portfolio_history
from .db import normalize


def summarize(rows):
    identities=defaultdict(list);suppliers=[]
    for r in rows:
        key=tuple(r.get(k) for k in ('municipality_ibge','buyer_cnpj','item_id','item_version','description','unit','currency','provider','phase'))
        identities[key].append(r)
        if r.get('supplier'):
            suppliers.append({'supplier':r['supplier'],'role':r['supplier_role'],'fact_id':r['id'],
                'process':r['obligation_id'],'municipality_ibge':r['municipality_ibge'],'buyer_cnpj':r['buyer_cnpj'],
                'source_url':r['source_url'],'source_id':r['source_id'],'consulted_at':r['consulted_at'],
                'origin':'supplier_fact','commercial_relationship_with_consormulti_proven':False})
    result=[]
    for key,group in identities.items():
        first=group[0];unit=first.get('unit');norm=catalogue.normalized_fact(first)
        comparable=bool(unit and first.get('item_id') and first.get('item_version') and norm['confidence']!='incomplete')
        if norm['package_signature'] and not catalogue.pack(unit):comparable=False
        quantities=[Decimal(r['quantity']) for r in group if r.get('quantity') is not None] if comparable else []
        amounts=[Decimal(r['amount']) for r in group if r.get('amount') is not None]
        prices=[Decimal(r['unit_price']) for r in group if r.get('unit_price') is not None] if comparable and first.get('currency')=='BRL' else []
        processes={r['obligation_id'] for r in group if catalogue.PNCP_PROCESS_RE.fullmatch(r.get('obligation_id') or '') and r['obligation_id'][:14]==r['buyer_cnpj']}
        result.append({k:first.get(k) for k in ('municipality_ibge','buyer_cnpj','buyer_name','item_id','item_version','description','unit','currency','provider','phase')} |
            {'observed_records':len(group),'identified_processes':len(processes) if processes else None,
             'observed_quantity':sum(quantities,Decimal(0)) if quantities else None,
             'documented_amount':sum(amounts,Decimal(0)) if amounts else None,
             'quantity_complete':comparable and len(quantities)==len(group),'amount_complete':len(amounts)==len(group),
             'comparable_unit_price_median':median(prices) if prices else None,'price_records':len(prices),
             'observed_months':sorted({str(r['event_date'])[:7] for r in group}),
             'recurrence_percentage':None,'monthly_consumption':None,'forecast':None,
             'coverage_status':'partial','group_assignment_requires_review':any(r['group_match_state']=='description_candidate_requires_review' for r in group),
             'fact_ids':[r['id'] for r in group],'source_ids':sorted({r['source_id'] for r in group}),
             'origin':'municipal_procurement','comparability':'exact_source_item_version_specification_unit_currency_phase'})
    return normalize({'records':result,'supplier_evidence':suppliers,'overall_quantity':None,'overall_amount':None,
        'coverage_status':'partial','notice':'Compare cada item e situação. Meses observados não comprovam recorrência ou consumo.'})


def compare(ctx,**filters):
    return summarize(portfolio_history.history(ctx,**filters,_all=True)['records'])
