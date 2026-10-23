"""Validate reuse of existing append-only/RLS storage in a disposable QA database."""
import pytest
from sqlalchemy.exc import DBAPIError
from app import history
from test_opportunities import collection, fixture_transport


def test_municipal_page_has_immutable_provenance_and_idempotent_restart(app, login, settings):
    assert settings.auth_mode == 'local_test'
    client = login()
    context = client.get('/api/v1/auth/context').json()
    cid = collection(client)
    transport, calls = fixture_transport()
    org, actor = context['org_id'], context['actor_id']
    for _ in range(8):
        history.advance(app.state.database, org, actor, cid, 1, transport)
    snapshot = client.get('/api/v1/history-collections/' + cid).json()
    assert snapshot['state'] == 'completed'
    before = len(calls)
    assert history.advance(app.state.database, org, actor, cid, 1, transport)['pages'] == 0
    assert len(calls) == before
    with app.state.database.transaction(org, actor) as db:
        rows = db.all("""SELECT t.arguments,t.state,t.attempts,p.record_count,p.created_at,
            s.id AS source_id,s.sha256,s.url,s.consulted_at,s.http_status
            FROM history_task t JOIN history_page p ON p.task_id=t.id AND p.org_id=t.org_id
            JOIN source_observation s ON s.id=p.source_id
            WHERE t.collection_id=:c AND t.org_id=:o""", {'c': cid, 'o': org})
        assert rows and all(r['state'] == 'done' and r['http_status'] == 200 and len(r['sha256']) == 64 for r in rows)
        assert all(r['created_at'] and r['consulted_at'] and r['arguments'] and r['attempts'] == 1 for r in rows)
        facts = db.all("""SELECT f.phase,f.quantity,f.unit_price,f.amount,f.event_identity,f.revision_hash,
            f.is_current,f.source_id,f.metadata FROM procurement_fact f
            WHERE f.org_id=:o AND f.provider='PNCP_RESULTADOS' AND f.classification='official'
            AND f.source_id IN (SELECT p.source_id FROM history_page p JOIN history_task t
                ON t.org_id=p.org_id AND t.id=p.task_id
                WHERE p.org_id=:o AND p.collection_id=:c AND t.provider='PNCP_RESULTADOS')""", {'o': org, 'c': cid})
        assert facts and all(f['phase'] == 'homologado' and f['source_id'] and f['event_identity'] and len(f['revision_hash']) == 64 for f in facts)
        assert all(f['metadata']['quantity_is_consumption'] is False for f in facts)
    with pytest.raises(DBAPIError) as error:
        with app.state.database.transaction(org, actor) as db:
            db.execute("UPDATE history_page SET record_count=999 WHERE org_id=:o AND collection_id=:c", {'o': org, 'c': cid})
    assert error.value.orig.sqlstate in ('42501', 'P0001')
    with app.state.database.transaction(org, actor) as db:
        assert db.one("SELECT max(record_count) AS n FROM history_page WHERE org_id=:o AND collection_id=:c", {'o': org, 'c': cid})['n'] < 999


def test_private_collection_evidence_is_not_shared_across_organizations(app, login):
    a, b = login(), login('compras-b')
    cid = collection(a)
    assert b.get('/api/v1/history-collections/' + cid).status_code == 404
    other = b.get('/api/v1/auth/context').json()
    with app.state.database.transaction(other['org_id'], other['actor_id']) as db:
        assert db.one('SELECT count(*) AS n FROM history_task WHERE collection_id=:c', {'c': cid})['n'] == 0
