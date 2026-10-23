"""Bounded Compras.gov price queries; sanitized snapshots are never parsed as raw API rows."""
import hashlib,json,re
from datetime import datetime,timezone
import httpx
from . import sources
from .db import encoded,normalize
from .security import fail


def query(ctx,kind,code,code_type,start,end,page=1,transport=None):
    ctx.require('sources.sync')
    if end<start or (end-start).days>366:fail(422,'Escolha até um ano para comparar preços.','PRICE_PERIOD_INVALID')
    if not re.fullmatch(r'\d{1,12}',code):fail(422,'Confira o código oficial do catálogo.','PRICE_CODE_INVALID')
    if kind=='material':
        if code_type not in ('codigoItemCatalogo','codigoPdm'):fail(422,'Escolha o tipo de código do material.','PRICE_CODE_TYPE_INVALID')
        endpoint='https://dadosabertos.compras.gov.br/modulo-pesquisa-preco/1_consultarMaterial'
        params={'tipo':code_type,'codigo':code}
    elif kind=='servico':
        if code_type!='codigoItemCatalogo':fail(422,'Serviços usam o código do item de catálogo.','PRICE_CODE_TYPE_INVALID')
        endpoint='https://dadosabertos.compras.gov.br/modulo-pesquisa-preco/3_consultarServico'
        params={'codigoItemCatalogo':code}
    else:fail(422,'Escolha material ou serviço.','PRICE_KIND_INVALID')
    if page<1 or page>100:fail(422,'Escolha uma página entre 1 e 100.','PRICE_PAGE_INVALID')
    params.update(dataCompraInicio=start.isoformat(),dataCompraFim=end.isoformat(),pagina=page,tamanhoPagina=10)
    provider='COMPRAS_PRECOS_MATERIAL' if kind=='material' else 'COMPRAS_PRECOS_SERVICO'
    url=str(httpx.Request('GET',endpoint,params=params).url)
    scope={'kind':kind,'code':code,'code_type':code_type,'start':start,'end':end,'page':page}
    preserved=ctx.db.all("""SELECT * FROM source_observation WHERE org_id=:o AND provider=:p AND url=:u
        AND classification='official' AND http_status IN (200,204)
        ORDER BY consulted_at DESC LIMIT 6""",{'o':ctx.org_id,'p':provider,'u':url})
    cached=None
    for saved in preserved:
        try:body=json.loads(saved['body'])
        except (ValueError,TypeError):continue
        rows=body.get('resultado') if isinstance(body,dict) else None
        if not isinstance(rows,list):continue
        if saved['metadata'].get('price_response_version')!=2:
            # Explicit compatibility with good legacy sanitized pages; reject the all-null cache defect.
            if not rows or any(not isinstance(r,dict) or r.get('catalogue_code') is None or not r.get('purchase_id') for r in rows):continue
            if code_type=='codigoItemCatalogo' and any(str(r['catalogue_code'])!=code for r in rows):continue
        cached=saved;break

    def response(saved,state=None,error=None):
        body=json.loads(saved['body']) if saved else {'resultado':[],'totalPaginas':None,'totalRegistros':None}
        records=[{**r,'purchase_id':str(r['purchase_id']) if r.get('purchase_id') is not None else None} for r in body['resultado']]
        return normalize({'records':records,'url':url,'scope':scope,'provider':provider,
            'consulted_at':saved['consulted_at'] if saved else None,'stored_sha256':saved['sha256'] if saved else None,
            'original_response_sha256':saved['metadata'].get('original_response_sha256') if saved else None,
            'page':page,'total_pages_reported':body.get('totalPaginas'),'total_records_reported':body.get('totalRegistros'),
            'has_next_page':isinstance(body.get('totalPaginas'),int) and page<body['totalPaginas'],
            'state':state or ('available' if records else 'empty_valid_response'),'source_error':error,
            'cache_hit':bool(saved and saved.get('_cache_hit')),'municipal_coverage_claimed':False,
            'price_comparability_review_required':True,'pncp_link_required':False,
            'message':'Preços observados no Compras.gov.br. Confira especificação, unidade, local e data. Não representam pagamento nem consumo.'})

    if cached and transport is None and (datetime.now(timezone.utc)-cached['consulted_at']).total_seconds()<300:
        return response({**cached,'_cache_hit':True})
    cooldown=ctx.db.one('SELECT extract(epoch FROM resume_after-now()) seconds FROM source_backoff WHERE org_id=:o AND provider=:p AND resume_after>now()',{'o':ctx.org_id,'p':provider})
    try:
        if cooldown and transport is None:raise sources.SourceFault('SOURCE_COOLDOWN',None,int(cooldown['seconds'])+1)
        url,status,raw,data=sources.public_get(endpoint,params,transport)
        if data is None:data={'resultado':[],'totalPaginas':0,'totalRegistros':0}
        if not isinstance(data,dict) or not isinstance(data.get('resultado'),list):raise sources.SourceFault('INVALID_PRICE_FORMAT',status)
        records=[]
        for row in data['resultado'][:10]:
            if not isinstance(row,dict):raise sources.SourceFault('INVALID_PRICE_FORMAT',status)
            if code_type=='codigoItemCatalogo' and str(row.get('codigoItemCatalogo'))!=code:
                raise sources.SourceFault('PRICE_CODE_MISMATCH',status)
            supplier=str(row.get('niFornecedor') or '')
            records.append({'purchase_id':str(row['idCompra']) if row.get('idCompra') is not None else None,'item_number':row.get('numeroItemCompra'),
                'catalogue_code':row.get('codigoItemCatalogo'),'catalogue_kind':kind,
                'description':row.get('descricaoItem'),'specification':row.get('descricaoDetalhadaItem'),
                'quantity':sources.documented_number(row.get('quantidade')),
                'unit_price':sources.documented_number(row.get('precoUnitario')),
                'unit':row.get('nomeUnidadeFornecimento') or row.get('nomeUnidadeMedida') or row.get('siglaUnidadeFornecimento') or row.get('siglaUnidadeMedida'),
                'package':{k:row[k] for k in ['capacidadeUnidadeFornecimento','siglaUnidadeMedida','nomeUnidadeFornecimento'] if row.get(k) is not None},
                'purchase_date':row.get('dataCompra'),'result_date':row.get('dataResultado'),
                'uasg':row.get('codigoUasg'),'purchasing_unit':row.get('nomeUasg'),'agency':row.get('nomeOrgao'),
                'municipality_code':row.get('codigoMunicipio'),'municipality_name':row.get('municipio'),'state':row.get('estado'),
                'supplier_cnpj':supplier if re.fullmatch(r'\d{14}',supplier) else None})
        # Each actual HTTP retrieval has its own immutable receipt, even when upstream bytes repeat.
        # Otherwise observe() returns an old id and the five-minute cache never becomes fresh again.
        safe={'price_response_version':2,'retrieved_at':datetime.now(timezone.utc),'resultado':records,'totalPaginas':data.get('totalPaginas'),'totalRegistros':data.get('totalRegistros')}
        sid=sources.observe(ctx,provider,url,status,encoded(safe).encode(),{'price_response_version':2,'scope':scope,
            'original_response_sha256':hashlib.sha256(raw).hexdigest(),'person_names_excluded':True,'municipal_coverage_claimed':False})
        saved=ctx.db.one('SELECT * FROM source_observation WHERE id=:id',{'id':sid})
        return response(saved)
    except sources.SourceFault as exc:
        retryable=exc.code not in ('HTTP_400','HTTP_404','HTTP_422','PRICE_CODE_MISMATCH')
        wait=exc.retry_after if retryable else None
        if retryable and exc.code!='SOURCE_COOLDOWN':
            ctx.db.execute('''INSERT INTO source_backoff(org_id,provider,resume_after) VALUES(:o,:p,now()+make_interval(secs=>:s))
                ON CONFLICT(org_id,provider) DO UPDATE SET resume_after=EXCLUDED.resume_after''',{'o':ctx.org_id,'p':provider,'s':wait})
        error={'code':exc.code,'upstream_http_status':exc.status,'retry_after':wait,'retryable':retryable,'attempted_at':datetime.now(timezone.utc),
            'message':'Não foi possível consultar esta fonte agora. Os outros resultados continuam disponíveis.'}
        ctx.audit('prices.source_failed',provider,{'code':exc.code,'upstream_http_status':exc.status,'scope':scope})
        return response(cached,'partial' if cached else 'source_unavailable',error)
