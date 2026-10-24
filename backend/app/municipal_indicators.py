"""SQL aggregates at exact source-item/version/unit, never inferred equivalence."""
from datetime import date
import re
from . import catalogue
from .db import normalize
from .security import fail

PHASES={'publicado_estimado','homologado','contratado','empenhado','liquidado','pago','entregue','consumido','estorno'}


def indicators(ctx, *, start, end, phase, municipalities=None, item_id=None,item_version=None,
               provider=None,period='month',cursor=None,limit=50,dataset='official'):
    ctx.require('read')
    ctx.db.execute("SET LOCAL statement_timeout='15000'")
    if phase not in PHASES or period not in ('month','quarter','year') or dataset not in ('official','synthetic'):
        fail(422,'Confira a situação, o período e a origem dos dados.')
    if end<start or (end-start).days>1826 or end>date.today():fail(422,'Escolha um período passado de até cinco anos.')
    if bool(item_id)!=(item_version is not None):fail(422,'Escolha o item e sua versão juntos.')
    if cursor is not None and not re.fullmatch(r'[0-9a-f]{32}',cursor):fail(422,'O marcador de página não é válido.')
    if not 1<=limit<=100:fail(422,'Escolha até 100 linhas por página.')
    cities=sorted(set(municipalities or []))
    if len(cities)>118:fail(422,'Escolha até 118 municípios.')
    if cities:
        known=ctx.db.all('SELECT ibge FROM municipality WHERE ibge=ANY(:cities)',{'cities':cities})
        if {r['ibge'] for r in known}!=set(cities):fail(422,'Confira os códigos dos municípios.','UNKNOWN_MUNICIPALITY')
    clauses=['f.org_id=:org','f.is_current','f.classification=:dataset','s.classification=:dataset',
        'f.phase=:phase','f.event_date BETWEEN :start AND :end',"b.government_level='M'"]
    params={'org':ctx.org_id,'dataset':dataset,'phase':phase,'start':start,'end':end,
        'period':period,'cursor':cursor or '', 'take':limit+1}
    for name,value,clause in [('cities',cities,'f.municipality_ibge=ANY(:cities)'),
        ('item',item_id,'f.item_id=:item'),('version',item_version,'f.item_version=:version'),
        ('provider',provider,'f.provider=:provider')]:
        if value is not None and value!=[]:clauses.append(clause);params[name]=value
    rows=ctx.db.all("""WITH grouped AS (
        SELECT f.municipality_ibge,b.id AS buyer_id,b.cnpj AS buyer_cnpj,b.name AS buyer_name,
            f.provider,f.phase,f.item_id,f.item_version,f.unit,f.description,
            COALESCE(f.metadata->>'currency','BRL') AS currency,
            COALESCE(f.metadata->>'record_level','unspecified') AS record_level,
            date_trunc(:period,f.event_date)::date AS period_start,
            count(*) AS observed_records,
            count(DISTINCT f.obligation_id) FILTER(WHERE f.provider IN ('PNCP','PNCP_ITENS','PNCP_RESULTADOS','PNCP_CONTRATOS')
                AND f.obligation_id ~ '^[0-9]{14}-1-[0-9]+/[0-9]{4}$'
                AND left(f.obligation_id,14)=b.cnpj) AS identified_processes,
            sum(f.quantity) FILTER(WHERE f.item_id IS NOT NULL AND f.item_version IS NOT NULL
                AND f.unit=i.unit AND f.description=i.name AND f.metadata->>'record_level'='item') AS compatible_quantity,
            count(f.quantity) FILTER(WHERE f.item_id IS NOT NULL AND f.item_version IS NOT NULL
                AND f.unit=i.unit AND f.description=i.name AND f.metadata->>'record_level'='item') AS quantity_records,
            sum(f.amount) AS documented_amount,count(f.amount) AS amount_records,
            min(f.event_date) AS first_observed,max(f.event_date) AS last_observed,
            (array_agg(DISTINCT f.id::text ORDER BY f.id::text))[1:100] AS fact_ids,
            (array_agg(DISTINCT s.id::text ORDER BY s.id::text))[1:100] AS source_ids,
            count(DISTINCT s.id) AS source_count,
            bool_and(COALESCE(f.metadata->>'financial_execution_proven','false')='true') AS financial_execution_proven,
            min(s.consulted_at) AS earliest_consulted,max(s.consulted_at) AS latest_consulted
        FROM procurement_fact f JOIN source_observation s ON s.id=f.source_id
        JOIN buyer b ON b.id=f.buyer_id AND b.org_id=f.org_id
        LEFT JOIN item_version i ON i.id=f.item_id AND i.version=f.item_version
        WHERE """+' AND '.join(clauses)+"""
        GROUP BY f.municipality_ibge,b.id,b.cnpj,b.name,f.provider,f.phase,f.item_id,f.item_version,
            f.unit,f.description,COALESCE(f.metadata->>'currency','BRL'),
            COALESCE(f.metadata->>'record_level','unspecified'),date_trunc(:period,f.event_date)::date
    ), keyed AS (SELECT *,md5(jsonb_build_array(municipality_ibge,buyer_id,provider,phase,item_id,
        item_version,unit,description,currency,record_level,period_start)::text) AS group_key FROM grouped)
    SELECT * FROM keyed WHERE group_key>:cursor ORDER BY group_key LIMIT :take""",params)
    has_more=len(rows)>limit;rows=rows[:limit]
    for row in rows:
        norm=catalogue.normalized_fact(row)
        if norm['confidence']=='incomplete':row['compatible_quantity']=None;row['quantity_records']=0
        row.update(package_signature=norm['package_signature'],quantity_complete=row['quantity_records']==row['observed_records'],
            amount_complete=row['amount_records']==row['observed_records'],partial=True,
            quantity_is_consumption=False,comparison_issues=norm['issues'],
            fact_ids_truncated=row['observed_records']>len(row['fact_ids']),
            source_ids_truncated=row['source_count']>len(row['source_ids']),
            amount_basis='source_documented_value_'+row['record_level'])
        if not row['identified_processes']:row['identified_processes']=None
    return normalize({'records':rows,'next_cursor':rows[-1]['group_key'] if has_more else None,
        'limit':limit,'phase':phase,'period':period,'start':start,'end':end,'municipalities':cities,
        'dataset':dataset,'source_completeness_claimed':False,'municipal_coverage':None,
        'method':'Current source events; exact item/version/unit/specification. Phases, sources and global instruments remain separate.',
        'notice':'Totais documentados parciais. Fases e itens diferentes não são somados. Ausência de registros não comprova ausência de compras.'})
