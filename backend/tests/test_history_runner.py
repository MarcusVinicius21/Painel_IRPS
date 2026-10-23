from sqlalchemy import text
from app import history
from app.history_runner import run_tick
from test_opportunities import collection, fixture_transport


def test_preview_then_bounded_restart_reuses_same_queue(app, login):
    c = login()
    ctx = c.get('/api/v1/auth/context').json()
    org, actor = ctx['org_id'], ctx['actor_id']
    cid = collection(c)
    transport, calls = fixture_transport()
    preview = run_tick(app.state.database, org, actor, [cid], transport=transport)
    assert preview['executed'] is False and calls == [] and preview['collections'][0]['pages'] == 0
    first = run_tick(app.state.database, org, actor, [cid], execute=True, max_attempts=2, transport=transport, sleep=lambda _: None)
    assert first['attempts'] == 2 and first['pages'] == 2
    second = run_tick(app.state.database, org, actor, [cid], execute=True, max_attempts=20, transport=transport, sleep=lambda _: None)
    assert second['collections'][0]['state'] == 'completed'
    assert second['municipal_completeness'] is None
    assert len(calls) == len(set(calls))


def test_another_runner_cannot_advance_same_organization(app, login):
    c = login()
    ctx = c.get('/api/v1/auth/context').json()
    cid = collection(c)
    transport, calls = fixture_transport()
    key = 'irps-public-history-runner:' + ctx['org_id']
    with app.state.database.engine.connect() as lease:
        lease.execute(text('SELECT pg_advisory_lock(hashtextextended(:key,0))'), {'key': key})
        lease.commit()
        try:
            result = run_tick(app.state.database, ctx['org_id'], ctx['actor_id'], [cid], execute=True, transport=transport, sleep=lambda _: None)
            assert result['busy'] is True and calls == []
        finally:
            lease.execute(text('SELECT pg_advisory_unlock(hashtextextended(:key,0))'), {'key': key})
            lease.commit()


def test_user_pause_is_preserved(app, login):
    c = login()
    ctx = c.get('/api/v1/auth/context').json()
    cid = collection(c)
    assert c.post('/api/v1/history-collections/' + cid + '/pause').status_code == 200
    transport, calls = fixture_transport()
    result = run_tick(app.state.database, ctx['org_id'], ctx['actor_id'], [cid], execute=True, transport=transport, sleep=lambda _: None)
    assert calls == [] and result['pages'] == 0
    assert result['collections'][0]['state'] == 'paused'
    assert result['collections'][0]['error_code'] == 'USER_PAUSED'


def test_expired_worker_lease_is_recovered_without_recreating_collection(app, login):
    c = login()
    ctx = c.get('/api/v1/auth/context').json()
    cid = collection(c)
    with app.state.database.transaction(ctx['org_id'], ctx['actor_id']) as db:
        db.execute("UPDATE history_task SET state='running',attempts=1,lease_until=now()-interval '1 second' WHERE org_id=:o AND collection_id=:c", {'o': ctx['org_id'], 'c': cid})
    transport, calls = fixture_transport()
    result = run_tick(app.state.database, ctx['org_id'], ctx['actor_id'], [cid], execute=True, transport=transport, sleep=lambda _: None)
    assert result['collections'][0]['state'] == 'completed'
    assert len(calls) == len(set(calls))
    with app.state.database.transaction(ctx['org_id'], ctx['actor_id']) as db:
        assert db.one("SELECT max(attempts) AS n FROM history_task WHERE org_id=:o AND collection_id=:c", {'o': ctx['org_id'], 'c': cid})['n'] == 2


def test_explicit_slower_interval_is_preserved(app, login):
    c = login()
    ctx = c.get('/api/v1/auth/context').json()
    cid = collection(c)
    transport, calls = fixture_transport()
    delays = []
    result = run_tick(app.state.database, ctx['org_id'], ctx['actor_id'], [cid], execute=True,
                      max_attempts=2, interval_seconds=5, transport=transport, sleep=delays.append)
    assert result['pages'] == 2 and len(calls) == 2
    assert delays == [5, 5]
