from datetime import date
import pytest
from app import sources
from app.municipal_plan import evidenced_windows, missing_windows, create_publication_plan
from app.opportunity_schemas import HistoricalScope, OpportunityFilter
from app.schemas import SourceSync
from app import history
from test_opportunities import collection, fixture_transport
import httpx


def page(index=1, expected=1, state='done', count=3, provider='PNCP'):
    return {'collection_id': 'old', 'provider': provider, 'state': state,
        'arguments': {'municipality_ibge': '3131307', 'modality': 6, 'start_date': '2025-10-16',
                      'end_date': '2025-10-22', 'size': 20, 'page': index},
        'result': {'expected_pages': expected}, 'record_count': count, 'http_status': 200,
        'source_classification': 'official', 'sha256': 'a' * 64, 'consulted_at': '2026-10-22', 'id': str(index), 'source_id': 'source'}


def test_reuse_requires_full_pagination_for_the_same_phase_and_window():
    assert evidenced_windows([page(expected=2)]) == []
    assert len(evidenced_windows([page(expected=2), page(index=2, expected=2)])) == 1
    assert evidenced_windows([page(state='failed')]) == []
    assert evidenced_windows([page(provider='PNCP_RESULTADOS')]) == []
    assert evidenced_windows([page(expected=0, count=3)]) == []
    assert len(evidenced_windows([page(expected=0, count=0)])) == 1


def test_gaps_do_not_repeat_verified_days_and_never_exceed_seven_days():
    windows = missing_windows(date(2025, 10, 1), date(2025, 10, 31), [(date(2025, 10, 16), date(2025, 10, 22))])
    assert windows == [(date(2025, 10, 1), date(2025, 10, 7)), (date(2025, 10, 8), date(2025, 10, 14)),
        (date(2025, 10, 15), date(2025, 10, 15)), (date(2025, 10, 23), date(2025, 10, 29)), (date(2025, 10, 30), date(2025, 10, 31))]
    assert missing_windows(date(2025, 10, 1), date(2025, 10, 7), [(date(2025, 9, 1), date(2025, 11, 1))]) == []


def test_official_new_modalities_accepted_but_unknown_codes_rejected():
    scope = HistoricalScope(municipalities=['3131307'], start='2025-10-01', end='2025-10-31', modalities=list(range(1, 20)), items=False, results=False)
    assert len(scope.modalities) == 19
    assert SourceSync(provider='PNCP', municipality_ibge='3131307', start_date='2025-10-01', end_date='2025-10-07', modality=19).modality == 19
    assert OpportunityFilter(modalities=[15, 19]).modalities == [15, 19]
    with pytest.raises(ValueError):
        HistoricalScope(municipalities=['3131307'], start='2025-10-01', end='2025-10-31', modalities=[20])


def test_plan_creation_is_idempotent_and_municipalities_do_not_bleed(app, login):
    c = login()
    ctx = c.get('/api/v1/auth/context').json()
    body = HistoricalScope(municipalities=['3131307'], start='2025-11-01', end='2025-11-30', modalities=[15, 19], items=False, results=False)
    with app.state.database.transaction(ctx['org_id'], ctx['actor_id']) as db:
        worker = sources.job_context(db, ctx['org_id'], ctx['actor_id'])
        first = create_publication_plan(worker, body)
    with app.state.database.transaction(ctx['org_id'], ctx['actor_id']) as db:
        worker = sources.job_context(db, ctx['org_id'], ctx['actor_id'])
        second = create_publication_plan(worker, body)
        tasks = db.all('SELECT arguments FROM history_task WHERE org_id=:o AND collection_id=:c', {'o': ctx['org_id'], 'c': first['id']})
    assert second['id'] == first['id'] and second['reused_plan']
    assert len(tasks) == 10 and all(t['arguments']['municipality_ibge'] == '3131307' for t in tasks)


def test_wrong_municipal_scope_is_quarantined_without_import(app, login):
    c = login()
    ctx = c.get('/api/v1/auth/context').json()
    cid = collection(c)
    payload = {'data': [{'numeroControlePNCP': '19875020000134-1-000010/2025',
        'orgaoEntidade': {'cnpj': '19875020000134'},
        'unidadeOrgao': {'codigoIbge': '3168705', 'codigoUnidade': '1'}}], 'totalPaginas': 1}
    history.advance(app.state.database, ctx['org_id'], ctx['actor_id'], cid, 1,
                    httpx.MockTransport(lambda _: httpx.Response(200, json=payload)))
    result = c.get('/api/v1/history-collections/' + cid).json()
    assert result['pages'] == 0 and result['tasks'] == [{'state': 'quarantined', 'count': 1}]
    assert result['recent_errors'][0]['metadata']['code'] == 'INVALID_MUNICIPAL_SCOPE'
    assert len(result['recent_errors'][0]['metadata']['response_evidence']['sha256']) == 64


def test_common_modalities_are_prioritized_without_omitting_others(app, login):
    c = login()
    ctx = c.get('/api/v1/auth/context').json()
    body = HistoricalScope(municipalities=['3131307'], start='2025-12-01', end='2025-12-07',
                           modalities=[1, 6], items=False, results=False)
    with app.state.database.transaction(ctx['org_id'], ctx['actor_id']) as db:
        worker = sources.job_context(db, ctx['org_id'], ctx['actor_id'])
        plan = create_publication_plan(worker, body)
    calls = []
    transport = httpx.MockTransport(lambda request: (calls.append(request.url.params['codigoModalidadeContratacao']) or httpx.Response(204)))
    for _ in range(2):
        assert history.advance(app.state.database, ctx['org_id'], ctx['actor_id'], plan['id'], 1, transport)['pages'] == 1
    assert calls == ['6', '1']
    assert c.get('/api/v1/history-collections/' + plan['id']).json()['state'] == 'completed'
