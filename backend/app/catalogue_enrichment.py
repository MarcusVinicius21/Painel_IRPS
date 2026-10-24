"""Optional secondary CATMAT metadata; never replaces official local evidence."""
from collections import OrderedDict
from threading import Lock
from time import monotonic
import re
import hashlib
from datetime import datetime,timezone
import httpx

_cache=OrderedDict();_lock=Lock();TTL=300;MAX_BYTES=1024*1024


def fetch(operation,*,kind='CATMAT',code=None,q=None,size=25,official_description=None,transport=None):
    if kind!='CATMAT':return {'state':'not_supported','reason':'CATSER_NOT_DOCUMENTED','official':False,'records':[]}
    params={}
    if operation=='item':
        if not re.fullmatch(r'\d{1,20}',str(code or '')):raise ValueError('CATMAT_CODE_REQUIRED')
        path='/item/'+str(code)
    elif operation=='search':
        if not isinstance(q,str) or not 1<=len(q.strip())<=150 or not 1<=size<=100:raise ValueError('INVALID_SEARCH')
        path='/search';params={'q':q.strip(),'size':size}
    elif operation=='categories':path='/categories'
    else:raise ValueError('UNSUPPORTED_SECONDARY_OPERATION')
    url=str(httpx.Request('GET','https://catmat.com.br/api/v1'+path,params=params).url)
    key=(url,official_description)
    with _lock:
        saved=_cache.get(key)
        if saved and monotonic()-saved[0]<TTL:return {**saved[1],'cache_hit':True}
    base={'official':False,'source':'CATMAT.com.br · fonte complementar','url':url,
        'purchase_history_implied':False,'records':[],'cache_hit':False,'attempts':1}
    try:
        with httpx.Client(timeout=httpx.Timeout(12,connect=5),follow_redirects=False,transport=transport,
                headers={'User-Agent':'IRPS-optional-catalogue/1.0'}) as client:
            with client.stream('GET',url) as r:
                if r.status_code!=200:
                    return {**base,'state':'not_found' if r.status_code==404 else 'retry_later' if r.status_code in (429,503) else 'unavailable',
                        'http_status':r.status_code,'retry_after':r.headers.get('retry-after')}
                body=bytearray()
                for part in r.iter_bytes():
                    body.extend(part)
                    if len(body)>MAX_BYTES:raise ValueError('SECONDARY_RESPONSE_LIMIT')
        import json
        data=json.loads(body)
        rows=[data] if operation=='item' else data.get('hits',[]) if operation=='search' and isinstance(data,dict) else data
        if not isinstance(rows,list) or len(rows)>100:raise ValueError('SECONDARY_SCHEMA_CHANGED')
        records=[]
        for row in rows:
            if not isinstance(row,dict):raise ValueError('SECONDARY_SCHEMA_CHANGED')
            if operation=='categories':
                if not isinstance(row.get('value'),str):raise ValueError('SECONDARY_SCHEMA_CHANGED')
                records.append({'category':row['value'][:300]});continue
            received=str(row.get('codigo_item') or '')
            if not received.isdigit() or not isinstance(row.get('descricao_item'),str):raise ValueError('SECONDARY_SCHEMA_CHANGED')
            if operation=='item' and received!=str(code):raise ValueError('SECONDARY_CODE_MISMATCH')
            records.append({'kind':'CATMAT','code':received,'description':row['descricao_item'][:10000],
                'group':str(row.get('grupo') or '')[:300],'class':str(row.get('classe') or '')[:300]})
        from .portfolio_rules import fold
        divergence=bool(official_description and records and fold(records[0]['description'])!=fold(official_description))
        result={**base,'state':'needs_review' if divergence else 'available','records':records,
            'http_status':200,'sha256':hashlib.sha256(body).hexdigest(),'consulted_at':datetime.now(timezone.utc).isoformat(),
            'official_snapshot_divergence':divergence,'notice':'Confira a descrição oficial no IRPS. Esta fonte não comprova compras.'}
        with _lock:
            _cache[key]=(monotonic(),result)
            while len(_cache)>128:_cache.popitem(last=False)
        return result
    except (httpx.HTTPError,ValueError,TypeError) as exc:
        return {**base,'state':'unavailable','error_type':type(exc).__name__,'reason':'SECONDARY_QUERY_FAILED'}
