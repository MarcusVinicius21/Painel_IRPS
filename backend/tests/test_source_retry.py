import httpx
import pytest
from app import history, sources
from app.source_retry import host_key, policy
from test_opportunities import collection, fixture_transport


@pytest.fixture(autouse=True)
def isolated_retry_clock(app, login):
    # Persistent backoff belongs to the application; tests must not leave a future
    # circuit deadline that prevents another independent fixture from running.
    assert app.state.settings.auth_mode == 'local_test'
    c = login()
    ctx = c.get('/api/v1/auth/context').json()
    def expire():
        with app.state.database.transaction(ctx['org_id'], ctx['actor_id']) as db:
            db.execute("UPDATE source_backoff SET resume_after=now()-interval '1 second' WHERE org_id=:o", {'o': ctx['org_id']})
    expire()
    yield
    expire()


def expire_qa_pause(app, ctx, cid):
    assert app.state.settings.auth_mode == 'local_test'
    with app.state.database.transaction(ctx['org_id'], ctx['actor_id']) as db:
        db.execute("UPDATE source_backoff SET resume_after=now()-interval '1 second' WHERE org_id=:o", {'o': ctx['org_id']})
        db.execute("UPDATE history_collection SET resume_after=now()-interval '1 second' WHERE org_id=:o AND id=:c", {'o': ctx['org_id'], 'c': cid})


@pytest.mark.parametrize('code,status,state', [('HTTP_401', 401, 'blocked'), ('HTTP_403', 403, 'blocked'),
    ('HTTP_404', 404, 'blocked'), ('INVALID_SOURCE_FORMAT', 200, 'quarantined'),
    ('PAGINATION_UNVERIFIED', None, 'quarantined'), ('SOURCE_CONNECTION', None, 'failed_retryable')])
def test_failure_taxonomy_is_not_success(code, status, state):
    assert policy(code, status, 1)['state'] == state
    assert policy('SOURCE_CONNECTION', None, 3)['state'] == 'blocked'


def test_retry_after_is_not_shortened_and_is_host_scoped():
    assert policy('RATE_LIMIT', 429, 1, 7200)['retry_after'] >= 7200
    assert host_key('PNCP') == host_key('PNCP_ITENS') == host_key('PNCP_RESULTADOS')
    transport = httpx.MockTransport(lambda _: httpx.Response(429, headers={'Retry-After': '7200'}))
    with pytest.raises(sources.SourceFault) as caught:
        sources.public_get('https://pncp.gov.br/test', transport=transport)
    assert caught.value.retry_after >= 7200
    assert len(caught.value.evidence['sha256']) == 64


def test_backoff_grows_exponentially_with_jitter(monkeypatch):
    monkeypatch.setattr('app.source_retry.random.uniform', lambda *_: 1)
    assert policy('SOURCE_CONNECTION', None, 1)['retry_after'] == 61
    assert policy('SOURCE_CONNECTION', None, 2)['retry_after'] == 121
    assert policy('RATE_LIMIT', 429, 1, 7200)['retry_after'] == 7201


def test_timeout_is_retryable_but_has_a_terminal_budget():
    def timeout(request):
        raise httpx.ReadTimeout('controlled QA timeout', request=request)
    with pytest.raises(sources.SourceFault) as caught:
        sources.public_get('https://pncp.gov.br/test', transport=httpx.MockTransport(timeout))
    assert caught.value.code == 'SOURCE_CONNECTION'
    assert policy(caught.value.code, None, 1)['state'] == 'failed_retryable'
    assert policy(caught.value.code, None, 3)['state'] == 'blocked'


def test_three_failures_stop_without_false_completion(app, login):
    c = login()
    ctx = c.get('/api/v1/auth/context').json()
    cid = collection(c)
    calls = []
    transport = httpx.MockTransport(lambda request: (calls.append(str(request.url)) or httpx.Response(503, headers={'Retry-After': '120'})))
    for _ in range(5):
        expire_qa_pause(app, ctx, cid)
        history.advance(app.state.database, ctx['org_id'], ctx['actor_id'], cid, 1, transport)
    assert len(calls) == 3
    result = c.get('/api/v1/history-collections/' + cid).json()
    assert result['pages'] == 0 and result['state'] == 'paused'
    assert result['tasks'] == [{'state': 'blocked', 'count': 1}]
    assert not result['execution']['complete_known_plan']
    assert len(result['recent_errors']) == 3
    assert result['recent_errors'][0]['metadata']['reason'] == 'retry_exhausted'
    assert result['recent_errors'][0]['metadata']['http_status'] == 503


@pytest.mark.parametrize('status,body,state', [(401, '', 'blocked'), (404, '', 'blocked'), (200, 'not-json', 'quarantined'), (200, '{"unexpected":[]}', 'quarantined')])
def test_access_failure_and_schema_change_are_not_retried(app, login, status, body, state):
    c = login()
    ctx = c.get('/api/v1/auth/context').json()
    cid = collection(c)
    expire_qa_pause(app, ctx, cid)
    calls = []
    transport = httpx.MockTransport(lambda request: (calls.append(str(request.url)) or httpx.Response(status, content=body)))
    for _ in range(2):
        history.advance(app.state.database, ctx['org_id'], ctx['actor_id'], cid, 1, transport)
    assert len(calls) == 1
    result = c.get('/api/v1/history-collections/' + cid).json()
    assert result['tasks'] == [{'state': state, 'count': 1}]
    assert result['pages'] == 0 and not result['execution']['complete_known_plan']
    assert len(result['recent_errors'][0]['metadata']['response_evidence']['sha256']) == 64
    assert result['recent_errors'][0]['metadata']['http_status'] == status


def test_transient_error_then_success_keeps_attempt_and_error_history(app, login):
    c = login()
    ctx = c.get('/api/v1/auth/context').json()
    cid = collection(c)
    expire_qa_pause(app, ctx, cid)
    transport, calls = fixture_transport(True)
    history.advance(app.state.database, ctx['org_id'], ctx['actor_id'], cid, 1, transport)
    before = len(calls)
    history.advance(app.state.database, ctx['org_id'], ctx['actor_id'], cid, 1, transport)
    assert len(calls) == before  # Retry-After enforced, not immediate retry.
    expire_qa_pause(app, ctx, cid)
    history.advance(app.state.database, ctx['org_id'], ctx['actor_id'], cid, 1, transport)
    result = c.get('/api/v1/history-collections/' + cid).json()
    assert result['pages'] == 1 and len(result['recent_errors']) == 1
    with app.state.database.transaction(ctx['org_id'], ctx['actor_id']) as db:
        assert db.one('SELECT max(attempts) AS n FROM history_task WHERE org_id=:o AND collection_id=:c', {'o': ctx['org_id'], 'c': cid})['n'] == 2


def test_secondary_identity_source_does_not_close_failed_purchase_scope(app, login):
    c = login()
    ctx = c.get('/api/v1/auth/context').json()
    cid = collection(c)
    expire_qa_pause(app, ctx, cid)
    history.advance(app.state.database, ctx['org_id'], ctx['actor_id'], cid, 1, httpx.MockTransport(lambda _: httpx.Response(503)))
    ibge = {'id': 3131307, 'nome': 'Ipatinga', 'microrregiao': {'mesorregiao': {'UF': {'sigla': 'MG'}}}}
    with app.state.database.transaction(ctx['org_id'], ctx['actor_id']) as db:
        worker = sources.job_context(db, ctx['org_id'], ctx['actor_id'])
        identity = sources.sync(worker, {'provider': 'IBGE', 'municipality_ibge': '3131307'}, httpx.MockTransport(lambda _: httpx.Response(200, json=ibge)))
        assert identity['records'] == 1 and identity['scope']['identity_only']
    primary = c.get('/api/v1/history-collections/' + cid).json()
    assert primary['pages'] == 0 and not primary['execution']['complete_known_plan']


def test_user_pause_during_failed_request_is_not_overwritten(app, login):
    c = login()
    ctx = c.get('/api/v1/auth/context').json()
    cid = collection(c)
    expire_qa_pause(app, ctx, cid)
    def response(request):
        assert c.post('/api/v1/history-collections/' + cid + '/pause').status_code == 200
        return httpx.Response(503)
    history.advance(app.state.database, ctx['org_id'], ctx['actor_id'], cid, 1, httpx.MockTransport(response))
    result = c.get('/api/v1/history-collections/' + cid).json()
    assert result['state'] == 'paused' and result['error_code'] == 'USER_PAUSED'
    assert not result['execution']['complete_known_plan']


def test_host_circuit_also_blocks_single_source_enqueue(app,login):
    from fastapi import HTTPException
    c=login();ctx=c.get('/api/v1/auth/context').json()
    with app.state.database.transaction(ctx['org_id'],ctx['actor_id']) as db:
        db.execute("INSERT INTO source_backoff(org_id,provider,resume_after) VALUES (:o,'PNCP_HOST',now()+interval '120 seconds') ON CONFLICT(org_id,provider) DO UPDATE SET resume_after=EXCLUDED.resume_after",{'o':ctx['org_id']})
    with pytest.raises(HTTPException) as error:
        with app.state.database.transaction(ctx['org_id'],ctx['actor_id']) as db:
            worker=sources.job_context(db,ctx['org_id'],ctx['actor_id'])
            sources.enqueue(worker,{'provider':'PNCP','municipality_ibge':'3131307','start_date':'2025-10-01',
                'end_date':'2025-10-07','modality':6,'page':1,'size':20},'host-circuit-qa')
    assert error.value.status_code==429 and error.value.detail['code']=='SOURCE_BACKOFF'
