"""Reconcile saved request prefixes; never equate request completion with municipal purchases."""
from collections import defaultdict,Counter
from datetime import date
from decimal import Decimal
import json,re
from urllib.parse import urlparse,parse_qs
from sqlalchemy import text
from .db import normalize
from .security import fail

LIST_ENDPOINTS=frozenset(('PNCP_ITENS','PNCP_CONTRATO_TERMOS'))
PERIOD_BASIS={'PNCP':'publication_date','PNCP_ATUALIZACAO':'global_update_date',
    'PNCP_ATAS_PUBLICACAO':'validity_overlap','PNCP_ATAS_ATUALIZACAO':'global_update_date',
    'PNCP_CONTRATOS':'contract_publication_date','PNCP_CONTRATOS_ATUALIZACAO':'global_update_date',
    'PNCP_RESULTADOS':'parent_item_discovery','PNCP_ITENS':'parent_publication_discovery',
    'PNCP_ATAS':'parent_publication_discovery','PNCP_CONTRATOS_COMPRA':'parent_publication_discovery',
    'PNCP_CONTRATO_TERMOS':'parent_contract_discovery','PNCP_PCA':'declared_plan_year','PNCP_PCA_ATUALIZACAO':'global_update_date'}
PATHS={'PNCP':r'/api/consulta/v1/contratacoes/publicacao','PNCP_ATUALIZACAO':r'/api/consulta/v1/contratacoes/atualizacao',
    'PNCP_CONTRATOS':r'/api/consulta/v1/contratos','PNCP_CONTRATOS_ATUALIZACAO':r'/api/consulta/v1/contratos/atualizacao',
    'PNCP_ATAS_PUBLICACAO':r'/api/consulta/v1/atas','PNCP_ATAS_ATUALIZACAO':r'/api/consulta/v1/atas/atualizacao',
    'PNCP_PCA_ATUALIZACAO':r'/api/consulta/v1/pca/atualizacao',
    'PNCP_ITENS':r'/api/pncp/v1/orgaos/\d{14}/compras/\d{4}/\d+/itens',
    'PNCP_RESULTADOS':r'/api/pncp/v1/orgaos/\d{14}/compras/\d{4}/\d+/itens/\d+/resultados',
    'PNCP_ATAS':r'/api/pncp/v1/orgaos/\d{14}/compras/\d{4}/\d+/atas',
    'PNCP_PCA':r'/api/pncp/v1/orgaos/\d{14}/pca/\d{4}/consolidado',
    'PNCP_CONTRATO_TERMOS':r'/api/pncp/v1/orgaos/\d{14}/contratos/\d{4}/\d+/termos',
    'PNCP_CONTRATOS_COMPRA':r'/api/pncp/v1/orgaos/\d{14}/contratos/contratacao/\d{4}/\d+'}


def matching_query(row,url):
    args=row['arguments'];provider=row['provider'];query=parse_qs(url.query);expected={}
    if 'page' in args:expected['pagina']=str(args['page'])
    if 'size' in args:expected['tamanhoPagina']=str(args['size'])
    if args.get('municipality_ibge'):expected['codigoMunicipioIbge']=args['municipality_ibge']
    if 'modality' in args:expected['codigoModalidadeContratacao']=str(args['modality'])
    if args.get('cnpj') and provider!='PNCP_PCA':expected['cnpjOrgao' if provider.startswith('PNCP_CONTRATOS') else 'cnpj']=args['cnpj']
    if provider=='PNCP_PCA' and url.path!=f"/api/pncp/v1/orgaos/{args.get('cnpj')}/pca/{args.get('year')}/consolidado":return False
    for arg,name in [('start_date','dataInicio' if provider=='PNCP_PCA_ATUALIZACAO' else 'dataInicial'),
                     ('end_date','dataFim' if provider=='PNCP_PCA_ATUALIZACAO' else 'dataFinal')]:
        if args.get(arg):expected[name]=args[arg].replace('-','')
    return all(query.get(k)==[v] for k,v in expected.items())


def verified(row):
    url=urlparse(row.get('url') or '')
    return bool(row['state']=='done' and row.get('http_status') in (200,204)
        and row.get('source_classification')=='official' and row.get('source_provider')==row['provider']
        and re.fullmatch(r'[0-9a-f]{64}',row.get('sha256') or '') and row.get('consulted_at') and row.get('body_hash_matches') is True
        and url.scheme=='https' and url.hostname=='pncp.gov.br' and not url.username and url.port in (None,443)
        and re.fullmatch(PATHS.get(row['provider'],'(?!)'),url.path) and matching_query(row,url)
        and (row.get('source_metadata') or {}).get('scope')==row['arguments'])


def reconcile(rows):
    groups=defaultdict(list)
    for row in rows:
        args={k:v for k,v in row['arguments'].items() if k!='page'}
        groups[(str(row['collection_id']),row['provider'],json.dumps(args,sort_keys=True))].append(row)
    result=[]
    for (cid,provider,raw),tasks in sorted(groups.items()):
        scope=json.loads(raw);good=[r for r in tasks if verified(r)]
        pages={r['arguments'].get('page',1):r for r in good}
        expected={r['result'].get('expected_pages') for r in good if r.get('result')}
        known=[n for n in expected if type(n) is int and 0<=n<=10000]
        errors=[];count_state='not_verifiable';expected_count=None;total=None
        if len(pages)!=len(good):errors.append('duplicate_page_identity')
        if len(expected)>1:errors.append('pagination_totals_changed')
        if provider in LIST_ENDPOINTS:
            size=scope.get('size');last=max(pages,default=0)
            if type(size) is int and size>0 and last and set(pages)==set(range(1,last+1)):
                if all(pages[n]['record_count']==size for n in range(1,last)) and 0<=pages[last]['record_count']<size:total=last
        elif len(expected)==1 and len(known)==1:
            total=max(known[0],1)
            if known[0]==0 and any(r['record_count'] for r in good):errors.append('zero_pages_with_records')
        missing=[n for n in range(1,total+1) if n not in pages] if total is not None else None
        complete=bool(total is not None and not missing and len(pages)==total and not errors)
        counts={r['result'].get('expected_records') for r in good if r.get('result')}
        if len(counts)==1:
            candidate=next(iter(counts))
            if type(candidate) is int and candidate>=0:expected_count=candidate
        observed=sum(r['record_count'] for r in good)
        if complete and expected_count is not None:
            count_state='reconciled' if observed==expected_count else 'mismatch'
            if count_state=='mismatch':errors.append('record_count_mismatch')
        if any(r['state']=='done' and not verified(r) for r in tasks):errors.append('done_without_sufficient_evidence')
        result.append({'collection_id':cid,'provider':provider,'scope':scope,'period_basis':PERIOD_BASIS.get(provider,'not_verified'),
            'collection_state':tasks[0].get('collection_state'),
            'collection_pages':tasks[0].get('collection_pages'),'known_page_budget':tasks[0].get('max_pages'),
            'collection_limited':tasks[0].get('collection_state')=='limited',
            'max_attempts_seen':max(r.get('attempts',0) for r in tasks),
            'materialized_tasks':len(tasks),'verified_pages':len(good),'expected_pages':total,'missing_pages':missing,
            'last_sync':max((str(r['consulted_at']) for r in good if r.get('consulted_at')),default=None),
            'pagination_reconciled':complete,'observed_rows':observed,'expected_records':expected_count,
            'fully_reconciled':complete and count_state=='reconciled' and not errors,
            'count_reconciliation':count_state,'errors':errors,'task_states':dict(Counter(r['state'] for r in tasks)),
            'source_errors':sorted({r['error_code'] for r in tasks if r.get('error_code')}),
            'municipal_purchase_completeness':None})
    verified_tasks=sum(verified(r) for r in rows)
    return {'materialized_tasks':len(rows),'verified_completed_tasks':verified_tasks,
        'materialized_request_percent':str(Decimal(verified_tasks)*100/len(rows)) if rows else None,
        'denominator':'Somente tarefas materializadas no recorte; novas páginas e documentos podem ampliar o plano.',
        'groups':result,'group_count':len(result),'pagination_reconciled_groups':sum(g['pagination_reconciled'] for g in result),
        'fully_reconciled_groups':sum(g['fully_reconciled'] for g in result),
        'groups_with_errors':sum(bool(g['errors'] or g['source_errors']) for g in result),
        'municipal_purchase_completeness':None}


def recover_saved_counts(ctx,rows):
    """Read immutable response headers, streaming bodies rather than requerying PNCP."""
    ids=sorted({str(r['source_id']) for r in rows if r.get('source_id') and r.get('http_status')==200
        and r.get('result') and r['result'].get('expected_records') is None})
    if not ids:return
    counts={};invalid=set()
    response=ctx.db.conn.execute(text("SELECT id,body FROM source_observation WHERE classification='official' AND id=ANY(CAST(:ids AS uuid[]))"),
        {'ids':ids},execution_options={'stream_results':True,'yield_per':10})
    try:
        for row in response.mappings():
            sid=str(row['id'])
            try:
                payload=json.loads(row['body']);value=payload.get('totalRegistros') if isinstance(payload,dict) else None
                if type(value) is int and value>=0:counts[sid]=value
            except (ValueError,TypeError):invalid.add(sid)
    finally:response.close()
    for row in rows:
        sid=str(row.get('source_id'))
        if sid in invalid:row['body_hash_matches']=False
        if sid in counts and (row.get('result') or {}).get('expected_records') is None:
            row['result']={**(row.get('result') or {}),'expected_records':counts[sid]}


def audit(ctx,start,end,municipalities=(),offset=0,limit=100,*,all_groups=False):
    ctx.require('sources.sync')
    if end<start or (end-start).days>366 or end>date.today():fail(422,'Escolha até doze meses encerrados para a conciliação.')
    known={r['ibge'] for r in ctx.db.all('SELECT ibge FROM municipality')}
    cities=sorted(set(municipalities) or known)
    if set(cities)-known:fail(422,'Confira os municípios do recorte.')
    if not 0<=offset<=100000 or not 1<=limit<=1000:fail(422,'Confira a paginação da auditoria.')
    rows=ctx.db.all("""SELECT t.id,t.collection_id,t.provider,t.arguments,t.state,t.error_code,t.attempts,
        c.state AS collection_state,c.pages AS collection_pages,c.scope->>'max_pages' AS max_pages,p.result,p.record_count,p.source_id,
        s.provider AS source_provider,s.metadata AS source_metadata,s.classification AS source_classification,
        s.http_status,s.sha256,s.url,s.consulted_at,
        s.sha256=encode(sha256(convert_to(s.body,'UTF8')),'hex') AS body_hash_matches
        FROM history_task t JOIN history_collection c ON c.id=t.collection_id AND c.org_id=t.org_id
        LEFT JOIN procurement_fact parent ON parent.id::text=COALESCE(t.arguments->>'procurement_id',t.arguments->>'contract_id')
        LEFT JOIN history_page p ON p.task_id=t.id AND p.org_id=t.org_id
        LEFT JOIN source_observation s ON s.id=p.source_id
        WHERE t.org_id=:o AND c.dataset='official' AND t.provider LIKE 'PNCP%'
        AND c.scope->>'start'<=:end AND c.scope->>'end'>=:start
        AND ((t.arguments ? 'start_date' AND t.arguments->>'start_date'<=:end AND t.arguments->>'end_date'>=:start)
            OR (NOT (t.arguments ? 'start_date') AND parent.id IS NOT NULL
                AND left(COALESCE(parent.metadata->>'publication_date',parent.event_date::text),10) BETWEEN :start AND :end)
            OR (t.provider='PNCP_PCA' AND t.arguments->>'year' BETWEEN left(:start,4) AND left(:end,4))
            OR (NOT (t.arguments ? 'start_date') AND parent.id IS NULL AND t.provider<>'PNCP_PCA'))
        AND EXISTS(SELECT 1 FROM jsonb_array_elements_text(c.scope->'municipalities') city WHERE city=ANY(:cities))
        AND (:all_cities OR t.arguments->>'municipality_ibge'=ANY(:cities) OR parent.municipality_ibge=ANY(:cities)
            OR EXISTS(SELECT 1 FROM buyer b WHERE b.org_id=:o AND b.classification='official'
                AND b.cnpj=t.arguments->>'cnpj' AND b.municipality_ibge=ANY(:cities)))
        ORDER BY t.collection_id,t.task_key LIMIT 50001""",{'o':ctx.org_id,'start':str(start),'end':str(end),'cities':cities,'all_cities':not municipalities})
    if len(rows)>50000:fail(422,'Divida o período ou os municípios antes de conciliar.','AUDIT_LIMIT')
    recover_saved_counts(ctx,rows)
    report=reconcile(rows);groups=report.pop('groups')
    lineage=ctx.db.one("""SELECT
        count(*) FILTER(WHERE f.provider IN ('PNCP_ITENS','PNCP_RESULTADOS') AND parent.id IS NULL) AS missing_parent,
        count(*) FILTER(WHERE f.provider='PNCP_RESULTADOS' AND parent.id IS NOT NULL
            AND (f.item_id IS DISTINCT FROM parent.item_id OR f.item_version IS DISTINCT FROM parent.item_version)) AS incompatible_result_parent,
        count(*) FILTER(WHERE f.provider='PNCP_CONTRATOS' AND (f.quantity IS NOT NULL OR f.unit_price IS NOT NULL)) AS global_contract_with_item_numbers
        ,count(*) FILTER(WHERE f.provider='PNCP' AND NOT EXISTS(SELECT 1 FROM history_task t
            WHERE t.org_id=f.org_id AND t.provider='PNCP_ITENS' AND t.arguments->>'procurement_id'=f.id::text)) AS current_publications_without_item_task
        ,count(*) FILTER(WHERE f.provider='PNCP_ITENS' AND f.metadata->>'has_result'='true' AND f.item_id IS NOT NULL
            AND NOT EXISTS(SELECT 1 FROM history_task t WHERE t.org_id=f.org_id AND t.provider='PNCP_RESULTADOS'
                AND t.arguments->>'procurement_id'=f.id::text)) AS current_result_candidates_without_task
        FROM procurement_fact f LEFT JOIN procurement_fact parent ON parent.id::text=f.metadata->>'parent_id'
          AND parent.classification='official' AND ((f.provider='PNCP_ITENS' AND parent.provider='PNCP')
            OR (f.provider='PNCP_RESULTADOS' AND parent.provider='PNCP_ITENS'))
        WHERE f.org_id=:o AND f.classification='official' AND f.is_current
        AND f.municipality_ibge=ANY(:cities) AND f.event_date BETWEEN :start AND :end""",
        {'o':ctx.org_id,'cities':cities,'start':start,'end':end})
    return normalize({**report,'scope':{'start':start,'end':end,'municipalities':cities},'lineage':lineage,
        'groups':groups if all_groups else groups[offset:offset+limit],'offset':0 if all_groups else offset,
        'limit':len(groups) if all_groups else limit,
        'next_offset':offset+limit if not all_groups and offset+limit<len(groups) else None,
        'limitations':['Percentual de tarefas não representa cobertura de compras municipais.',
            'Vigência, publicação, atualização e data do resultado são bases temporais distintas.',
            'Linhas e revisões não são compras independentes.','Ausência de registro não é zero compras.']})
