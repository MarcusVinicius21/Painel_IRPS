"""Lazy municipal windows over the existing PNCP queue, not a second collector."""
from datetime import date,timedelta
from . import municipal_plan,modality
from .opportunity_schemas import HistoricalScope

def windows(today):
    current=date(today.year,today.month,1);start=date(current.year-1,current.month,1);rows=[]
    while start<=today:
        following=date(start.year+(start.month==12),start.month%12+1,1)
        rows.append((start,min(following-timedelta(days=1),today)));start=following
    return rows

def plan_city(ctx,city,start,end):
    # Existing planner deduplicates scope and reuses fully evidenced windows.
    body=HistoricalScope(municipalities=[city],start=start,end=end,modalities=sorted(modality.COLLECTABLE_CODES),
                         publications=True,updates=False,items=False,results=False,size=20,max_pages=2000)
    return municipal_plan.create_publication_plan(ctx,body)

def municipality_summary(ctx,city,start,end):
    from .portfolio_coverage import matrix
    report=matrix(ctx,start,end,[city]);rows=report['records']
    return {'municipality_ibge':city,'verified_requests':sum(r['verified_requests'] for r in rows),
            'observed_months':sorted({r['month'] for r in rows if r['verified_requests']}),
            'failed_or_blocked':sum(r['failed_or_blocked'] for r in rows),
            'state':'partial' if any(r['verified_requests'] for r in rows) else 'not_collected',
            'municipal_purchase_completeness':None,
            'request_reconciliation_percent':None,
            'limitation':'Detailed denominators remain per source/request prefix; no aggregate market percentage.'}
