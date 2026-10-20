"""Evidence of completed requests, never an assertion of all municipal purchases."""
from collections import defaultdict
from datetime import date,timedelta
from decimal import Decimal
from .db import normalize
from .security import fail

PROVIDERS={
    'PNCP':('Publicações PNCP','publicado_estimado'),
    'PNCP_ATUALIZACAO':('Atualizações PNCP','publicado_estimado'),
    'PNCP_ITENS':('Itens de publicações PNCP','publicado_estimado'),
    'PNCP_RESULTADOS':('Resultados de itens PNCP','homologado'),
    'PNCP_CONTRATOS':('Contratos PNCP','contratado'),
    'PNCP_CONTRATOS_ATUALIZACAO':('Atualizações de contratos PNCP','contratado'),
    'PNCP_ATAS':('Atas PNCP','ata_registro'),
    'PNCP_ATAS_ATUALIZACAO':('Atualizações de atas PNCP','ata_registro'),
    'PNCP_PCA':('Planos anuais PNCP','planejado'),
    'PNCP_PCA_ATUALIZACAO':('Atualizações de planos PNCP','planejado'),
    'COMPRAS_CATMAT':('Catálogo de materiais Compras.gov.br','catalogo'),
    'COMPRAS_CATSER':('Catálogo de serviços Compras.gov.br','catalogo'),
    'COMPRAS_PRECOS_MATERIAL':('Preços de materiais Compras.gov.br','referencia_preco'),
    'COMPRAS_PRECOS_SERVICO':('Preços de serviços Compras.gov.br','referencia_preco'),
    'TCE_MG_SICOM':('Dados abertos TCE-MG/Sicom','não integrado'),
    'PORTAL_MUNICIPAL':('Portal municipal','não integrado'),
}


def dates(start,end):
    current=start
    while current<=end:
        yield current
        current+=timedelta(days=1)


def inventory(ctx,start,end,cities):
    ctx.require('read')
    if end<start or (end-start).days>1826:fail(422,'Escolha até cinco anos para conferir a cobertura.')
    known=ctx.db.all("SELECT ibge,name,uf FROM municipality WHERE ibge=ANY(:cities) ORDER BY name",{'cities':cities}) if cities else ctx.db.all("SELECT ibge,name,uf FROM municipality WHERE uf='MG' ORDER BY name LIMIT 20")
    if cities and len(known)!=len(set(cities)):fail(422,'Confira os municípios selecionados.')
    selected={r['ibge'] for r in known}
    buyers=ctx.db.all("SELECT municipality_ibge,cnpj,name,unit_code FROM buyer WHERE classification='official' AND municipality_ibge=ANY(:cities) ORDER BY name LIMIT 5000",{'cities':list(selected)})
    city_buyers=defaultdict(list)
    for buyer in buyers:city_buyers[buyer['municipality_ibge']].append(buyer)
    buyer_inventory=ctx.db.all("""SELECT f.municipality_ibge,b.id AS buyer_id,b.cnpj,b.name,b.unit_code,
        f.provider,f.phase,f.metadata->>'modality' AS modality,count(*) AS observed_facts,
        count(DISTINCT f.obligation_id) AS observed_processes,min(f.event_date) AS earliest,
        max(f.event_date) AS latest
        FROM procurement_fact f JOIN buyer b ON b.id=f.buyer_id
        WHERE f.classification='official' AND f.is_current AND f.event_date BETWEEN :start AND :end
          AND f.municipality_ibge=ANY(:cities)
        GROUP BY f.municipality_ibge,b.id,b.cnpj,b.name,b.unit_code,f.provider,f.phase,f.metadata->>'modality'
        ORDER BY f.municipality_ibge,b.name,f.provider,f.phase LIMIT 10001""",
        {'start':start,'end':end,'cities':list(selected)})
    if len(buyer_inventory)>10000:fail(422,'Divida o período para conferir os órgãos compradores.','BUYER_INVENTORY_LIMIT')
    tasks=ctx.db.all("""SELECT t.id,t.provider,t.arguments,t.state,t.collection_id,c.state AS collection_state,
        c.scope,p.record_count,p.result,s.url,s.sha256,s.consulted_at,
        parent.municipality_ibge AS parent_city,parent.event_date AS parent_date
        FROM history_task t JOIN history_collection c ON c.id=t.collection_id AND c.org_id=t.org_id
        LEFT JOIN history_page p ON p.task_id=t.id AND p.org_id=t.org_id
        LEFT JOIN source_observation s ON s.id=p.source_id
        LEFT JOIN procurement_fact parent ON parent.id=(CASE WHEN t.arguments->>'procurement_id' ~
          '^[0-9a-fA-F-]{36}$' THEN (t.arguments->>'procurement_id')::uuid ELSE NULL END)
        WHERE t.org_id=:o AND c.dataset='official' ORDER BY c.created_at,t.task_key LIMIT 50001""",{'o':ctx.org_id})
    if len(tasks)>50000:fail(422,'Divida o período ou os municípios para conferir esta coleta.','INVENTORY_LIMIT')
    cnpjs={c:{str(b['cnpj']) for b in city_buyers[c] if b['cnpj']} for c in selected}
    grouped=defaultdict(list)
    for task in tasks:
        args=task['arguments'];provider=task['provider']
        if args.get('start_date') and args.get('end_date'):
            try:
                if date.fromisoformat(args['end_date'])<start or date.fromisoformat(args['start_date'])>end:continue
            except ValueError:continue
        elif task['parent_date'] and not start<=task['parent_date']<=end:continue
        elif args.get('year') and not start.year<=int(args['year'])<=end.year:continue
        city=args.get('municipality_ibge') or task['parent_city']
        if not city and args.get('cnpj'):
            city=next((c for c in selected if str(args['cnpj']) in cnpjs[c]),None)
        if city not in selected:continue
        modality=args.get('modality') if provider in ('PNCP','PNCP_ATUALIZACAO') else None
        grouped[(city,provider,modality)].append(task)
    records=[]
    for city in known:
        code=city['ibge']
        for provider,(label,phase) in PROVIDERS.items():
            keys=[key for key in grouped if key[0]==code and key[1]==provider]
            if not keys:keys=[(code,provider,None)]
            for key in sorted(keys,key=lambda x:(x[2] is None,x[2] or 0)):
                rows=grouped.get(key,[])
                complete=sum(r['state']=='done' and r['url'] is not None for r in rows)
                observed=sum(r['record_count'] or 0 for r in rows)
                proof=[{'url':r['url'],'sha256':r['sha256'],'consulted_at':r['consulted_at'],
                    'record_count':r['record_count'],'task_id':str(r['id'])} for r in rows if r['url']][:25]
                planned_days=set();verified_days=set();pagination=[]
                if provider in ('PNCP','PNCP_ATUALIZACAO'):
                    for seed in (r for r in rows if r['arguments'].get('page')==1):
                        args=seed['arguments']
                        try:a=max(start,date.fromisoformat(args['start_date']));b=min(end,date.fromisoformat(args['end_date']))
                        except (KeyError,ValueError):continue
                        if a>b:continue
                        window=set(dates(a,b));planned_days.update(window)
                        siblings=[r for r in rows if r['collection_id']==seed['collection_id']
                            and r['arguments'].get('start_date')==args['start_date']
                            and r['arguments'].get('end_date')==args['end_date']]
                        expected=seed['result'].get('expected_pages') if seed['result'] else None
                        pages={r['arguments'].get('page') for r in siblings if r['state']=='done' and r['url']}
                        reconciled=isinstance(expected,int) and expected>=0 and set(range(1,max(1,expected)+1))<=pages
                        if reconciled:verified_days.update(window)
                        pagination.append({'start':args['start_date'],'end':args['end_date'],
                            'expected_pages':expected,'completed_pages':len(pages),'pages_reconciled':reconciled})
                denominator=len(planned_days)
                ratio=Decimal(len(verified_days))/denominator if denominator else None
                status='request_reconciled' if denominator and verified_days==planned_days else 'partial' if rows else 'not_collected'
                if provider in ('TCE_MG_SICOM','PORTAL_MUNICIPAL') and not rows:status='connector_pending'
                records.append({'municipality_ibge':code,'municipality_name':city['name'],'uf':city['uf'],
                    'provider':provider,'source_label':label,'phase':phase,'modality':key[2],
                    'buyer_count':len(city_buyers[code]),'buyers':city_buyers[code][:20],
                    'tasks':len(rows),'completed_tasks':complete,'records_returned':observed,
                    'planned_days':denominator or None,'reconciled_days':len(verified_days) if denominator else None,
                    'request_completion_ratio':ratio,'source_completeness_ratio':None,
                    'pagination':pagination[:25],'proof':proof,'proof_truncated':len(rows)>25,
                    'status':status,'message':('Percentual mostra somente consultas planejadas e paginadas; não mede todas as compras do município.'
                        if ratio is not None else 'Ainda não há denominador verificável para medir esta situação.')})
    return normalize({'start':start,'end':end,'municipalities':known,'records':records,
        'buyer_inventory':buyer_inventory,'buyer_inventory_basis':'Órgãos vinculados ao código IBGE informado pela fonte; a identidade municipal e a ausência de outras compras não são presumidas.',
        'basis':'Consultas concluídas nos recortes configurados. Ausência de registro não prova ausência de compra.',
        'official_phase_completeness_claimed':False})
