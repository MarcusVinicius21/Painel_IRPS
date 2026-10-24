"""Versioned, read-only envelope for the documented Ipatinga payment JSON.

No ingestion is enabled while source period/identity semantics remain unverified.
"""
import hashlib,json
from datetime import date
from urllib.parse import urlparse,parse_qs
from .municipal_finance import payment_candidates,FinanceEvidenceError

SCHEMA='actcon-ipatinga-payments-observed-v1'
MAX_BYTES=4*1024*1024


def review_response(ctx, *, url, status, body, sha256, start:date, end:date, schema=SCHEMA, retry_after=None):
    ctx.require('sources.sync')
    if schema!=SCHEMA:raise ValueError('UNVERIFIED_PORTAL_SCHEMA')
    if start>end or start.year!=end.year:raise ValueError('SPLIT_FINANCIAL_PERIOD_BY_YEAR')
    parsed=urlparse(url);q=parse_qs(parsed.query)
    if (parsed.scheme!='https' or parsed.hostname!='dadosabertos-portalfacil.azurewebsites.net'
        or parsed.username or parsed.password or parsed.port not in (None,443) or parsed.fragment
        or parsed.path!='/api/pagamentos' or set(q)!={'type','idCliente','page','pageSize','numAno'}
        or q['type']!=['json'] or q['idCliente']!=['97'] or q['numAno']!=[str(start.year)]
        or q['pageSize']!=['100'] or len(q['page'])!=1 or not q['page'][0].isdigit()
        or not 1<=int(q['page'][0])<=10000):raise ValueError('UNVERIFIED_PORTAL_URL')
    if not isinstance(body,bytes) or len(body)>MAX_BYTES or hashlib.sha256(body).hexdigest()!=sha256:
        raise ValueError('INVALID_PORTAL_EVIDENCE')
    result={'schema':SCHEMA,'source_url':url,'sha256':sha256,'http_status':status,
        'municipality_ibge':'3131307','phase':'pago','start':start.isoformat(),'end':end.isoformat(),
        'can_ingest':False,'database_mutated':False,'coverage':None,'records_imported':None}
    if status in (429,503):
        try:delay=int(retry_after)
        except (TypeError,ValueError):delay=60
        return {**result,'state':'retry_later','retry_after_seconds':min(max(delay,60),86400),
            'automatic_attempts':0}
    if status!=200:return {**result,'state':'source_unavailable','reason':'HTTP_'+str(status)}
    try:
        candidates=payment_candidates(json.loads(body),start=start,end=end)
    except (json.JSONDecodeError,UnicodeDecodeError,FinanceEvidenceError) as exc:
        reason=str(exc) if isinstance(exc,FinanceEvidenceError) else 'INVALID_JSON_OR_LAYOUT_CHANGE'
        return {**result,'state':'rejected','reason':reason}
    # Receipt can be compared across attempts without claiming a persisted import.
    receipt=hashlib.sha256((SCHEMA+'|'+url+'|'+start.isoformat()+'|'+end.isoformat()+'|'+sha256).encode()).hexdigest()
    return {**result,'state':'candidates_require_review','receipt_sha256':receipt,
        'candidate_records':candidates['candidates'],'source_rows':candidates['source_rows'],
        'exact_duplicate_rows':candidates['exact_duplicate_rows'],
        'reason':'SOURCE_PERIOD_AND_FINANCIAL_IDENTITY_NOT_YET_APPROVED'}
