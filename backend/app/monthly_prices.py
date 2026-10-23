"""Append-only monthly source import and code lookup, separate from canonical/PNCP facts."""
import base64,csv,hashlib,io,json,re,zipfile
from datetime import date
from pathlib import Path
from uuid import uuid4
import psycopg
from psycopg.types.json import Jsonb
from .db import encoded,normalize
from .security import fail
from .sources import documented_number


def normalize_row(row,kind,month):
    code=row.get('codigo_item_catalogo','').strip();purchase=row.get('id_compra','').strip();item=row.get('id_item_compra','').strip()
    if not re.fullmatch(r'\d{1,12}',code) or not purchase or not item:raise ValueError('missing_source_identity_or_code')
    try:day=date.fromisoformat(row['data_compra'][:10])
    except (KeyError,ValueError):raise ValueError('invalid_purchase_date')
    if day.strftime('%Y-%m')!=month:raise ValueError('date_outside_source_month')
    supplier=row.get('ni_fornecedor','')
    body={'purchase_id':purchase,'item_number':row.get('numero_item_compra'),'catalogue_code':code,'catalogue_kind':kind,
      'description':row.get('descricao_item'),'specification':row.get('descricao_detalhada_item'),
      'quantity':documented_number(row.get('quantidade')),'unit_price':documented_number(row.get('preco_unitario')),
      'unit':row.get('nome_unidade_fornecimento') or row.get('nome_unidade_medida') or row.get('sigla_unidade_medida') or None,
      'package':{k:row[k] for k in ['capacidade_unidade_fornecimento','sigla_unidade_medida','nome_unidade_fornecimento'] if row.get(k)},
      'purchase_date':day.isoformat(),'result_date':row.get('data_resultado') or None,'uasg':row.get('codigo_uasg'),
      'purchasing_unit':row.get('nome_uasg'),'agency':row.get('nome_orgao'),'municipality_code':row.get('codigo_municipio') or None,
      'municipality_name':row.get('municipio') or None,'state':row.get('estado') or None,
      'supplier_cnpj':supplier if re.fullmatch(r'\d{14}',supplier) else None}
    return purchase+':'+item,code,day,body


def import_archive(url,org,path,kind,month,expected_sha,source_url,metadata=None):
    if kind not in ('material','servico') or not re.fullmatch(r'\d{4}-\d{2}',month):raise ValueError('Invalid monthly scope')
    day=date.fromisoformat(month+'-01');path=Path(path)
    with path.open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
    if sha!=expected_sha:raise ValueError('Archive checksum mismatch')
    sid=str(uuid4());rejected=[];rows=0
    with zipfile.ZipFile(path) as archive:
        entries=archive.infolist()
        if len(entries)!=1 or not entries[0].filename.endswith('.csv') or entries[0].file_size>300*1024*1024:raise ValueError('Archive scope or size rejected')
        if archive.testzip() is not None:raise ValueError('Archive CRC mismatch')
        with psycopg.connect(url.replace('+psycopg','')) as conn:
            conn.execute("SELECT set_config('irps.org_id',%s,true)",(str(org),))
            conn.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',('monthly:'+str(org)+kind+month,))
            prior=conn.execute('SELECT id,source_rows,accepted_rows,rejected_rows,duplicate_rows FROM price_monthly_snapshot WHERE org_id=%s AND kind=%s AND month=%s AND archive_sha256=%s',(org,kind,day,sha)).fetchone()
            if prior:return {'snapshot_id':str(prior[0]),'source_rows':prior[1],'accepted_rows':prior[2],'rejected_rows':prior[3],'duplicate_rows':prior[4],'idempotent':True}
            conn.execute('CREATE TEMP TABLE price_stage(source_key text,record_sha256 text,line_number integer,code text,purchase_date date,source_updated_at text,body jsonb) ON COMMIT DROP')
            with archive.open(entries[0]) as source:
                reader=csv.DictReader(io.TextIOWrapper(source,encoding='utf-8-sig'),delimiter=';')
                if not {'id_compra','id_item_compra','codigo_item_catalogo','data_compra','preco_unitario','quantidade'}.issubset(reader.fieldnames or []):raise ValueError('Missing source columns')
                columns=reader.fieldnames
                with conn.cursor().copy('COPY price_stage FROM STDIN') as copy:
                    for line,row in enumerate(reader,2):
                        rows+=1
                        if rows>500000:raise ValueError('Pilot exceeds 500000 rows')
                        try:
                            if None in row or any(v is None for v in row.values()):raise ValueError('invalid_column_count')
                            key,code,purchased,body=normalize_row(row,kind,month)
                        except ValueError as exc:
                            rejected.append({'line':line,'reason':str(exc),'row_sha256':hashlib.sha256(encoded(row).encode()).hexdigest()});continue
                        copy.write_row((key,hashlib.sha256(encoded(row).encode()).hexdigest(),line,code,purchased,row.get('data_hora_atualizacao_item') or None,Jsonb(body)))
            if not rows:raise ValueError('Empty monthly archive')
            accepted=conn.execute('SELECT count(*) FROM (SELECT DISTINCT source_key,record_sha256 FROM price_stage) q').fetchone()[0]
            duplicates=rows-len(rejected)-accepted
            conflicts=conn.execute('SELECT count(*) FROM (SELECT source_key FROM price_stage GROUP BY source_key HAVING count(DISTINCT record_sha256)>1) q').fetchone()[0]
            meta={**(metadata or {}),'columns':columns,'conflicting_source_keys':conflicts,'rejections':rejected,'personal_names_excluded':True,'partition':'data_compra','source_archive_name':entries[0].filename}
            conn.execute('INSERT INTO price_monthly_snapshot(org_id,id,kind,month,archive_sha256,source_url,metadata,source_rows,accepted_rows,rejected_rows,duplicate_rows) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(org,sid,kind,day,sha,source_url,Jsonb(meta),rows,accepted,len(rejected),duplicates))
            conn.execute('''INSERT INTO price_monthly_record SELECT %s,%s,source_key,record_sha256,line_number,code,purchase_date,source_updated_at,body FROM
                (SELECT DISTINCT ON(source_key,record_sha256) * FROM price_stage ORDER BY source_key,record_sha256,line_number) q''',(org,sid))
            actual=conn.execute('SELECT count(*) FROM price_monthly_record WHERE org_id=%s AND snapshot_id=%s',(org,sid)).fetchone()[0]
            if actual!=accepted:raise ValueError('Monthly import reconciliation failed')
    return {'snapshot_id':sid,'kind':kind,'month':month,'sha256':sha,'source_rows':rows,'accepted_rows':accepted,'rejected_rows':len(rejected),'duplicate_rows':duplicates,'conflicting_source_keys':conflicts,'rejections':rejected,'idempotent':False,'source_url':source_url,'complete_file_import':len(rejected)==0}


def query(ctx,kind,code,start,end,page=1,cursor=None):
    ctx.require('read')
    if kind not in ('material','servico') or not re.fullmatch(r'\d{1,12}',code):fail(422,'Confira o tipo e o código oficial.')
    if end<start or (end-start).days>366 or page<1 or page>100000:fail(422,'Confira o periodo e a pagina.')
    if page>100 and not cursor:fail(422,'Continue pela proxima pagina.','PRICE_CURSOR_REQUIRED')
    snapshots=ctx.db.all('''SELECT DISTINCT ON(month) * FROM price_monthly_snapshot WHERE org_id=:o AND kind=:k
        AND month<=:end AND month>=date_trunc('month',CAST(:start AS date)) ORDER BY month,imported_at DESC,id DESC''',{'o':ctx.org_id,'k':kind,'start':start,'end':end})
    ids=[str(s['id']) for s in snapshots];params={'o':ctx.org_id,'c':code,'start':start,'end':end,'ids':encoded(ids),'offset':(page-1)*10}
    where="org_id=:o AND code=:c AND purchase_date BETWEEN :start AND :end AND snapshot_id IN (SELECT value::uuid FROM jsonb_array_elements_text(CAST(:ids AS jsonb)))"
    total=ctx.db.one('SELECT count(*) n FROM price_monthly_record WHERE '+where,params)['n']
    fingerprint=hashlib.sha256(encoded([str(ctx.org_id),kind,code,start,end,ids]).encode()).hexdigest()
    condition='';offset=' OFFSET :offset' if not cursor else ''
    if cursor:
        try:
            if len(cursor)>2048:raise ValueError()
            token=json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())
            if token['scope']!=fingerprint or len(token['after'])!=4:raise ValueError()
            params.update(dict(zip(['after_date','after_key','after_sha','after_snapshot'],token['after'])))
            date.fromisoformat(params['after_date'])
        except (ValueError,KeyError,TypeError,UnicodeError):fail(422,'A consulta mudou. Volte à primeira página.','PRICE_CURSOR_INVALID')
        condition=' AND (purchase_date,source_key,record_sha256,snapshot_id)>(CAST(:after_date AS date),:after_key,:after_sha,CAST(:after_snapshot AS uuid))'
    rows=ctx.db.all('SELECT * FROM (SELECT *,count(*) OVER(PARTITION BY source_key) revision_count FROM price_monthly_record WHERE '+where+') q WHERE true'+condition+' ORDER BY purchase_date,source_key,record_sha256,snapshot_id LIMIT 10'+offset,params)
    next_cursor=base64.urlsafe_b64encode(encoded({'scope':fingerprint,'after':[rows[-1]['purchase_date'],rows[-1]['source_key'],rows[-1]['record_sha256'],str(rows[-1]['snapshot_id'])]}).encode()).decode() if rows and page*10<total else None
    known=ctx.db.one('''SELECT EXISTS(SELECT 1 FROM national_catalogue_entry e JOIN national_catalogue_snapshot s ON s.id=e.snapshot_id
        WHERE s.kind=:kind AND e.code=:code) AS known''',{'kind':'CATMAT' if kind=='material' else 'CATSER','code':code})['known']
    mapped={str(s['id']):s for s in snapshots};records=[]
    for row in rows:
        snap=mapped[str(row['snapshot_id'])]
        reasons=[]
        if row['revision_count']>1:reasons.append('Há versões deste registro. Confira antes de comparar.')
        if not row['body'].get('unit'):reasons.append('A fonte não informa a unidade deste registro.')
        if not known:reasons.append('Este código ainda não foi localizado no catálogo deste tipo.')
        records.append({**row['body'],'source_url':snap['source_url'],'source_archive_sha256':snap['archive_sha256'],'source_line':row['line_number'],
            'source_record_sha256':row['record_sha256'],'revision_count':row['revision_count'],'needs_review':bool(reasons),'review_reasons':reasons,'catalogue_code_verified':known,'source_key':row['source_key']})
    return normalize({'records':records,'state':'needs_review' if any(r['needs_review'] for r in records) else 'available' if records else 'empty_valid_response' if snapshots else 'not_collected',
        'next_cursor':next_cursor,'source_kind':'monthly_file','url':snapshots[0]['source_url'] if snapshots else None,'page':page,
        'total_pages_reported':(total+9)//10 if snapshots else None,'total_records_reported':total if snapshots else None,'has_next_page':page*10<total,
        'consulted_at':max((s['imported_at'] for s in snapshots),default=None),'scope':{'kind':kind,'code':code,'start':start,'end':end,'imported_months':[s['month'] for s in snapshots]},
        'source_error':None,'rejected_source_rows':sum(s['rejected_rows'] for s in snapshots),'municipal_coverage_claimed':False,'price_comparability_review_required':True,
        'message':'Somente os meses importados foram consultados. São linhas e versões do Compras.gov.br, não novas compras PNCP.'})
