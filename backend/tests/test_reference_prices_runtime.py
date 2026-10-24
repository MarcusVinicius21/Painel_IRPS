"""Isolated QA only: no fixture is copied to the operational database."""
from datetime import date,datetime,timezone,timedelta
from uuid import uuid4
import hashlib
import httpx
import pytest
from app import catalogue,sources,price_queries
from app.db import encoded


def context(app,login):
    client=login();identity=client.get('/api/v1/auth/context').json()
    return client,identity


def payload(code):
    return {'resultado':[{'idCompra':'qa-price','numeroItemCompra':1,'codigoItemCatalogo':int(code),
        'descricaoItem':'Item de teste isolado','quantidade':2,'precoUnitario':12.5,
        'nomeUnidadeMedida':'UNIDADE','municipio':'Município informado pela fonte','codigoMunicipio':3131307,
        'niFornecedor':'12345678901','nomeFornecedor':'Pessoa natural excluída'}],'totalPaginas':2,'totalRegistros':11}


def run(app,identity,code,transport=None,kind='material'):
    with app.state.database.transaction(identity['org_id'],identity['actor_id']) as db:
        ctx=sources.job_context(db,identity['org_id'],identity['actor_id'])
        return catalogue.reference_prices(ctx,kind,code,'codigoItemCatalogo',date(2026,1,1),date(2026,10,23),1,transport)


def test_second_query_keeps_values_unit_and_original_hash(app,login):
    _,identity=context(app,login);code=str(int(uuid4().hex[:8],16));calls=[]
    def handle(request):
        calls.append(str(request.url));data=payload(code);data['resultado'][0]['idCompra']=92820605000032026
        return httpx.Response(200,json=data)
    first=run(app,identity,code,httpx.MockTransport(handle));second=run(app,identity,code)
    assert len(calls)==1 and second['cache_hit']
    assert first['records']==second['records'] and second['records'][0]['unit_price']=='12.5'
    assert first['records'][0]['purchase_id']=='92820605000032026'
    assert second['records'][0]['unit']=='UNIDADE' and second['records'][0]['supplier_cnpj'] is None
    assert first['original_response_sha256']==second['original_response_sha256']
    assert first['consulted_at']==second['consulted_at'] and second['has_next_page']
    assert not first['municipal_coverage_claimed'] and not first['pncp_link_required']


def test_same_numeric_code_material_and_service_have_distinct_caches(app,login):
    _,identity=context(app,login);code=str(int(uuid4().hex[:8],16))
    material=run(app,identity,code,httpx.MockTransport(lambda r:httpx.Response(200,json=payload(code))))
    service=run(app,identity,code,httpx.MockTransport(lambda r:httpx.Response(200,json=payload(code))),kind='servico')
    assert material['provider']!=service['provider'] and material['url']!=service['url']
    assert material['records'][0]['catalogue_kind']=='material' and service['records'][0]['catalogue_kind']=='servico'


def test_repeated_remote_bytes_have_new_receipt_but_same_source_fingerprint(app,login,monkeypatch):
    # Windows wall-clock resolution can assign identical instants to two fast
    # requests. Control distinct receipt times without weakening either hash assertion.
    from itertools import count
    base=datetime.now(timezone.utc);ticks=count()
    class ReceiptClock(datetime):
        @classmethod
        def now(cls,tz=None):return base+timedelta(microseconds=next(ticks))
    monkeypatch.setattr(price_queries,'datetime',ReceiptClock)
    _,identity=context(app,login);code=str(int(uuid4().hex[:8],16))
    transport=httpx.MockTransport(lambda r:httpx.Response(200,json=payload(code)))
    first=run(app,identity,code,transport);fresh=run(app,identity,code,transport)
    assert first['records']==fresh['records']
    assert first['original_response_sha256']==fresh['original_response_sha256']
    assert first['stored_sha256']!=fresh['stored_sha256']
    cached=run(app,identity,code)
    assert cached['cache_hit'] and cached['consulted_at']==fresh['consulted_at']


def test_legacy_good_snapshot_is_read_without_reparsing_or_mutation(app,login):
    _,identity=context(app,login);code=str(int(uuid4().hex[:8],16))
    first=run(app,identity,code,httpx.MockTransport(lambda r:httpx.Response(200,json=payload(code))))
    with app.state.database.transaction(identity['org_id'],identity['actor_id']) as db:
        ctx=sources.job_context(db,identity['org_id'],identity['actor_id'])
        legacy=encoded({'resultado':first['records'],'totalPaginas':2,'totalRegistros':11}).encode()
        sid=sources.observe(ctx,first['provider'],first['url'],200,legacy,{'original_response_sha256':first['original_response_sha256']})
        before=db.one('SELECT body,sha256 FROM source_observation WHERE id=:i',{'i':sid})
    again=run(app,identity,code)
    assert again['records']==first['records'] and again['cache_hit']
    with app.state.database.transaction(identity['org_id'],identity['actor_id']) as db:
        assert db.one('SELECT body,sha256 FROM source_observation WHERE id=:i',{'i':sid})==before


def test_source_failure_preserves_stale_data_and_does_not_claim_empty(app,login,monkeypatch):
    _,identity=context(app,login);code=str(int(uuid4().hex[:8],16))
    first=run(app,identity,code,httpx.MockTransport(lambda r:httpx.Response(200,json=payload(code))))
    failed=run(app,identity,code,httpx.MockTransport(lambda r:httpx.Response(503,headers={'Retry-After':'120'})))
    assert failed['state']=='partial' and failed['records']==first['records']
    assert failed['source_error']['upstream_http_status']==503 and failed['source_error']['retry_after']==120
    assert failed['consulted_at']==first['consulted_at']


@pytest.mark.parametrize('status,expected',[(429,'RATE_LIMIT'),(502,'HTTP_502'),(400,'HTTP_400')])
def test_error_without_history_is_explicit_and_bounded(app,login,status,expected):
    client,identity=context(app,login);code=str(int(uuid4().hex[:8],16))
    result=run(app,identity,code,httpx.MockTransport(lambda r:httpx.Response(status,headers={'Retry-After':'90'})))
    assert result['state']=='source_unavailable' and result['records']==[]
    assert result['total_records_reported'] is None and result['source_error']['code']==expected
    assert result['source_error']['upstream_http_status']==status
    if status==429:
        response=client.get('/api/v1/catalogue-intelligent/reference-prices',params={'kind':'material','code':code,'start':'2026-01-01','end':'2026-10-23'})
        assert response.status_code==429 and int(response.headers['Retry-After'])>0
        assert response.json()['source_error']['code']=='SOURCE_COOLDOWN'
    if status==400:assert result['source_error']['retryable'] is False


@pytest.mark.parametrize('response,code',[('malformed','INVALID_SOURCE_FORMAT'),('different_code','PRICE_CODE_MISMATCH')])
def test_bad_response_is_not_presented_as_prices(app,login,response,code):
    _,identity=context(app,login);item=str(int(uuid4().hex[:8],16))
    transport=httpx.MockTransport(lambda r:httpx.Response(200,text='{') if response=='malformed' else httpx.Response(200,json=payload(str(int(item)+1))))
    result=run(app,identity,item,transport)
    assert result['state']=='source_unavailable' and result['source_error']['code']==code and result['records']==[]


def test_documented_empty_is_different_from_failure_and_missing_values(app,login):
    client,identity=context(app,login);code=str(int(uuid4().hex[:8],16))
    result=run(app,identity,code,httpx.MockTransport(lambda r:httpx.Response(204)))
    assert result['state']=='empty_valid_response' and result['total_records_reported']==0 and result['source_error'] is None
    missing=payload(code);missing['resultado'][0].update(quantidade=None,precoUnitario=None,nomeUnidadeMedida=None)
    result=run(app,identity,code,httpx.MockTransport(lambda r:httpx.Response(200,json=missing)))
    assert result['records'][0]['quantity'] is None and result['records'][0]['unit_price'] is None and result['records'][0]['unit'] is None

    invalid=client.get('/api/v1/catalogue-intelligent/reference-prices',params={'kind':'material','code':code,'start':'2024-01-01','end':'2026-10-23'})
    assert invalid.status_code==422 and invalid.json()['detail']['code']=='PRICE_PERIOD_INVALID'
