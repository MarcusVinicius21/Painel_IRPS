import httpx
import hashlib
from app.catalogue_enrichment import fetch,_cache

def test_secondary_response_preserves_checksum_and_consultation_time():
    _cache.clear();response=httpx.Response(200,json={'codigo_item':463562,'descricao_item':'CAFÉ'})
    result=fetch('item',code='463562',transport=httpx.MockTransport(lambda _:response))
    assert result['sha256']==hashlib.sha256(response.content).hexdigest()
    assert result['http_status']==200 and result['consulted_at']
    assert result['official'] is False and result['purchase_history_implied'] is False


def test_exact_optional_item_cache_and_official_divergence_never_replace_local():
    _cache.clear();calls=[]
    def respond(r):
        calls.append(r);return httpx.Response(200,json={'codigo_item':123,'descricao_item':'OUTRA DESCRIÇÃO','likes':99999})
    transport=httpx.MockTransport(respond)
    a=fetch('item',code='123',official_description='CAFÉ',transport=transport)
    b=fetch('item',code='123',official_description='CAFÉ',transport=transport)
    assert a['state']=='needs_review' and not a['official'] and not a['purchase_history_implied']
    assert 'likes' not in a['records'][0] and b['cache_hit'] and len(calls)==1


def test_catser_never_queries_material_endpoint():
    def no_call(r):raise AssertionError('CATSER must not use CATMAT endpoint')
    assert fetch('item',kind='CATSER',code='14729',transport=httpx.MockTransport(no_call))['state']=='not_supported'


def test_404_429_timeout_and_mismatched_code_are_not_empty_official_success():
    _cache.clear()
    for status,state in [(404,'not_found'),(429,'retry_later'),(503,'retry_later'),(403,'unavailable')]:
        r=fetch('item',code='123',transport=httpx.MockTransport(lambda _:httpx.Response(status)))
        assert r['state']==state and not r['official'] and r['attempts']==1
    def timeout(request):raise httpx.ReadTimeout('QA timeout',request=request)
    assert fetch('item',code='123',transport=httpx.MockTransport(timeout))['state']=='unavailable'
    assert fetch('item',code='123',transport=httpx.MockTransport(lambda _:httpx.Response(200,json={'codigo_item':999,'descricao_item':'QA'})))['state']=='unavailable'
