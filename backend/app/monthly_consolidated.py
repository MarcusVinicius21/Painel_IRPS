"""Logical monthly union. Originals remain immutable and available through the raw endpoint."""
import base64,binascii,hashlib,json,re,threading,os
from collections import OrderedDict
from datetime import date
from uuid import UUID
from pathlib import Path
from uuid import uuid4
from .db import encoded,normalize
from .monthly_prices import coverage,unit_status
from .security import fail

ALGORITHM='monthly-logical-v1'
_summaries=OrderedDict()
_summary_lock=threading.Lock()

def snapshots(ctx,start,end,kind=None):
    return ctx.db.all("""SELECT DISTINCT ON(kind,month) * FROM price_monthly_snapshot
      WHERE org_id=:o AND month BETWEEN date_trunc('month',CAST(:start AS date)) AND :end
      AND (CAST(:kind AS text) IS NULL OR kind=:kind) AND rejected_rows=0 AND source_rows=accepted_rows+duplicate_rows
      AND month<date_trunc('month',CURRENT_DATE)
      ORDER BY kind,month,imported_at DESC,id DESC""",{'o':ctx.org_id,'start':start,'end':end,'kind':kind})

def scope(ctx,start,end,selected,extra=None):
    return hashlib.sha256(encoded([ALGORITHM,str(ctx.org_id),start,end,[(str(s['id']),s['archive_sha256']) for s in selected],extra]).encode()).hexdigest()

def cte(code_scoped=False):
    # Candidate keys use code/date index; rank ALL selected versions of these keys
    # before filtering code/date/unit. A code-changing revision cannot appear twice.
    candidate=""", keys AS MATERIALIZED (SELECT DISTINCT source_key FROM price_monthly_record
        WHERE org_id=:o AND code=:code AND snapshot_id IN (SELECT id FROM selected)),""" if code_scoped else ','
    join=' JOIN keys k ON k.source_key=r.source_key' if code_scoped else ''
    projection='r.*' if code_scoped else "r.source_key,r.record_sha256,r.code,r.purchase_date,r.source_updated_at,jsonb_build_object('unit',r.body->>'unit','unit_price',r.body->>'unit_price','municipality_code',r.body->>'municipality_code') AS body"
    return """WITH selected AS MATERIALIZED (SELECT * FROM price_monthly_snapshot
       WHERE org_id=:o AND id IN (SELECT value::uuid FROM jsonb_array_elements_text(CAST(:ids AS jsonb))))"""+candidate+"""
      ranked AS MATERIALIZED (SELECT """+projection+""",s.kind,s.month,s.source_url,s.archive_sha256,s.imported_at,
        row_number() OVER(PARTITION BY s.kind,r.source_key ORDER BY s.month DESC,s.imported_at DESC,r.source_updated_at DESC NULLS LAST,r.record_sha256 DESC,s.id DESC) rank,
        count(*) OVER(PARTITION BY s.kind,r.source_key) versions,
        min(r.record_sha256) OVER(PARTITION BY s.kind,r.source_key) first_hash,
        max(r.record_sha256) OVER(PARTITION BY s.kind,r.source_key) last_hash
        FROM price_monthly_record r JOIN selected s ON s.org_id=r.org_id AND s.id=r.snapshot_id"""+join+""" WHERE r.org_id=:o),
      logical AS (SELECT *,first_hash<>last_hash conflict FROM ranked WHERE rank=1)
    """

def period(start,end):
    if end<start or (end-start).days>366:fail(422,'Escolha um período de até 366 dias.')

def decode_cursor(cursor,fingerprint,page):
    try:
        if not isinstance(cursor,str) or len(cursor)>2048:raise ValueError()
        token=json.loads(base64.b64decode(cursor,altchars=b'-_',validate=True))
        after=token['after']
        if token['scope']!=fingerprint or token['page']!=page or not isinstance(after,list) or len(after)!=4:raise ValueError()
        if not all(isinstance(v,str) for v in after):raise ValueError()
        day,key,sha,snapshot=after
        date.fromisoformat(day);UUID(snapshot)
        if not isinstance(key,str) or not 1<=len(key)<=1024 or not re.fullmatch('[0-9a-f]{64}',sha):raise ValueError()
        return dict(zip(['after_date','after_key','after_sha','after_snapshot'],after))
    except (ValueError,TypeError,KeyError,UnicodeError,binascii.Error):
        fail(422,'A consulta mudou. Volte à primeira página.','PRICE_CURSOR_INVALID')

def query(ctx,kind,code,start,end,page=1,cursor=None,unit=None,uasg=None,municipality=None,supplier=None):
    ctx.require('read');period(start,end)
    if kind not in ('material','servico') or not re.fullmatch(r'\d{1,12}',code):fail(422,'Confira o tipo e o código oficial.')
    if not 1<=page<=100000:fail(422,'Confira a página solicitada.')
    if page>100 and not cursor:fail(422,'Continue pela próxima página.','PRICE_CURSOR_REQUIRED')
    if unit is not None and not 1<=len(unit.strip())<=120:fail(422,'Confira a unidade.')
    for value,pattern in [(uasg,r'\d{1,12}'),(municipality,r'\d{1,12}'),(supplier,r'\d{14}')]:
        if value is not None and not re.fullmatch(pattern,value):fail(422,'Confira os códigos dos filtros.')
    selected=snapshots(ctx,start,end,kind);ids=[str(s['id']) for s in selected]
    params={'o':ctx.org_id,'ids':encoded(ids),'code':code,'start':start,'end':end,'unit':unit.strip() if unit else None,
            'uasg':uasg,'municipality':municipality,'supplier':supplier,'offset':(page-1)*10}
    fingerprint=scope(ctx,start,end,selected,[kind,code,params['unit'],uasg,municipality,supplier])
    prefix=cte(True)+""", filtered AS (SELECT * FROM logical WHERE code=:code AND purchase_date BETWEEN :start AND :end
        AND (CAST(:unit AS text) IS NULL OR btrim(body->>'unit')=:unit) AND (CAST(:uasg AS text) IS NULL OR body->>'uasg'=:uasg)
        AND (CAST(:municipality AS text) IS NULL OR body->>'municipality_code'=:municipality)
        AND (CAST(:supplier AS text) IS NULL OR body->>'supplier_cnpj'=:supplier)) """
    total=ctx.db.one(prefix+'SELECT count(*) n FROM filtered',params)['n']
    condition='';offset=' OFFSET :offset'
    if cursor:
        params.update(decode_cursor(cursor,fingerprint,page));offset=''
        condition=' WHERE (purchase_date,source_key,record_sha256,snapshot_id)>(CAST(:after_date AS date),:after_key,:after_sha,CAST(:after_snapshot AS uuid))'
    rows=ctx.db.all(prefix+'SELECT * FROM filtered'+condition+' ORDER BY purchase_date,source_key,record_sha256,snapshot_id LIMIT 11'+offset,params)
    has_next=len(rows)>10;rows=rows[:10];next_cursor=None
    if has_next:
        row=rows[-1];next_cursor=base64.urlsafe_b64encode(encoded({'scope':fingerprint,'page':page+1,'after':[row['purchase_date'],row['source_key'],row['record_sha256'],str(row['snapshot_id'])]}).encode()).decode()
    known=ctx.db.one("""SELECT EXISTS(SELECT 1 FROM national_catalogue_entry e JOIN national_catalogue_snapshot s ON s.id=e.snapshot_id
       WHERE s.kind=:kind AND e.code=:code) known""",{'kind':'CATMAT' if kind=='material' else 'CATSER','code':code})['known']
    records=[]
    for row in rows:
        reasons=[]
        if row['conflict']:reasons.append('Há versões diferentes deste item. Confira os documentos antes de comparar.')
        if unit_status(row['body'])=='unknown':reasons.append('A fonte não informa a unidade deste registro.')
        if not known:reasons.append('Este código ainda não foi localizado no catálogo deste tipo.')
        records.append({**row['body'],'source_key':row['source_key'],'source_url':row['source_url'],'source_archive_sha256':row['archive_sha256'],
            'source_record_sha256':row['record_sha256'],'source_line':row['line_number'],'source_month':row['month'],
            'source_snapshot_id':row['snapshot_id'],'unit_status':unit_status(row['body']),'phase':'precos_praticados',
            'revision_count':row['versions'],'conflict':row['conflict'],'needs_review':bool(reasons),'review_reasons':reasons,'catalogue_code_verified':known})
    return normalize({'records':records,'state':'needs_review' if any(x['needs_review'] for x in records) else 'available' if records else 'empty_valid_response' if selected else 'not_collected',
        'source_kind':'monthly_consolidated','algorithm':ALGORITHM,'scope_fingerprint':fingerprint,'page':page,'next_cursor':next_cursor,'has_next_page':has_next,
        'total_records_reported':total if selected else None,'total_pages_reported':(total+9)//10 if selected else None,'coverage':coverage(ctx,start,end),
        'scope':{'kind':kind,'code':code,'start':start,'end':end,'imported_months':[s['month'] for s in selected],'unit':unit,'uasg':uasg,'municipality':municipality,'supplier':supplier},
        'consulted_at':max((s['imported_at'] for s in selected),default=None),'url':selected[0]['source_url'] if selected else None,
        'source_error':None,'municipal_coverage_claimed':False,'price_comparability_review_required':True,
        'statistics':{'mean':None,'median':None,'reason':'Código igual não comprova unidade, embalagem e especificação comparáveis.'}})

def summary(ctx,start,end):
    """Separate aggregate endpoint with bounded, snapshot-scoped tenant cache."""
    ctx.require('read');period(start,end);selected=snapshots(ctx,start,end);fingerprint=scope(ctx,start,end,selected)
    coverage_now=coverage(ctx,start,end)
    with _summary_lock:
        if fingerprint in _summaries:return {**_summaries[fingerprint],'coverage':coverage_now}
        cache=Path(__file__).resolve().parents[2]/'.runtime'/'price-summary'/str(UUID(str(ctx.org_id)))/(fingerprint+'.json')
        if cache.exists() and cache.stat().st_size<2_000_000:
            try:
                saved=json.loads(cache.read_text(encoding='utf-8'))
                if saved['scope_fingerprint']==fingerprint and saved['algorithm']==ALGORITHM:
                    _summaries[fingerprint]=saved
                    while len(_summaries)>16:_summaries.popitem(last=False)
                    return {**saved,'coverage':coverage_now}
            except (ValueError,KeyError,OSError):pass
        params={'o':ctx.org_id,'ids':encoded([str(s['id']) for s in selected]),'start':start,'end':end}
        prefix=cte()+", scoped AS MATERIALIZED (SELECT * FROM logical WHERE purchase_date BETWEEN :start AND :end) "
        result_row=ctx.db.one(prefix+"""SELECT (SELECT jsonb_build_object('logical_records',count(*),'conflicts',count(*) FILTER(WHERE conflict),
          'unknown_unit',count(*) FILTER(WHERE btrim(coalesce(body->>'unit',''))=''),
          'unknown_price',count(*) FILTER(WHERE body->>'unit_price' IS NULL),
          'source_municipalities',count(DISTINCT nullif(btrim(body->>'municipality_code'),'')),
          'source_codes_with_price',count(DISTINCT (kind,code)) FILTER(WHERE body->>'unit_price' IS NOT NULL)) FROM scoped) totals,
          (SELECT coalesce(jsonb_agg(q ORDER BY q.kind),'[]') FROM (
             SELECT c.kind,count(*) codes_with_price FROM (SELECT DISTINCT kind,code FROM scoped WHERE body->>'unit_price' IS NOT NULL) c
             WHERE EXISTS(SELECT 1 FROM national_catalogue_entry e JOIN national_catalogue_snapshot s ON s.id=e.snapshot_id
             WHERE s.kind=CASE WHEN c.kind='material' THEN 'CATMAT' ELSE 'CATSER' END AND e.code=c.code) GROUP BY c.kind) q) codes,
          (SELECT coalesce(jsonb_agg(q ORDER BY q.month,q.kind),'[]') FROM (
             SELECT to_char(purchase_date,'YYYY-MM') AS month,kind,count(*) logical_records,count(*) FILTER(WHERE conflict) conflicts
             FROM scoped GROUP BY 1,kind) q) series""",params)
        result=normalize({'algorithm':ALGORITHM,'scope_fingerprint':fingerprint,'start':start,'end':end,'source_kind':'monthly_consolidated',
            'physical_rows_in_selected_files':sum(s['accepted_rows'] for s in selected),'totals':result_row['totals'] if selected else None,
            'catalogue_codes_with_price':result_row['codes'],'monthly_series':result_row['series'],'coverage':coverage_now,
            'municipal_coverage_claimed':False,'quantities_aggregated':False,'price_statistics_available':False})
        _summaries[fingerprint]=result
        while len(_summaries)>16:_summaries.popitem(last=False)
        try:
            cache.parent.mkdir(parents=True,exist_ok=True);temp=cache.with_suffix('.tmp-'+uuid4().hex)
            temp.write_text(encoded(result),encoding='utf-8');os.replace(temp,cache)
        except OSError:pass  # Cache is optional; a successful exact query remains valid.
        return result
