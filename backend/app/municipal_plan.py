"""Publication-only campaign plans reuse evidenced windows, never other phases."""
from collections import defaultdict
from datetime import date, timedelta
import hashlib
import json
from . import history
from .db import encoded, identifier
from .modality import COLLECTABLE_CODES


def evidenced_windows(rows):
    groups = defaultdict(list)
    for row in rows:
        args = row['arguments']
        if row['provider'] != 'PNCP':
            continue
        key = (str(row['collection_id']), args.get('municipality_ibge'), args.get('modality'),
               args.get('start_date'), args.get('end_date'), args.get('size'))
        groups[key].append(row)
    proven = []
    for key, pages in groups.items():
        expected = {p['result'].get('expected_pages') for p in pages if p['result']}
        if len(expected) != 1:
            continue
        total = next(iter(expected))
        if type(total) is not int or not 0 <= total <= 10000:
            continue
        valid = [p for p in pages if p['state'] == 'done' and p['http_status'] in (200, 204)
                 and p['source_classification'] == 'official' and p['sha256'] and p['consulted_at']]
        indexes = {p['arguments'].get('page') for p in valid}
        if indexes != set(range(1, max(total, 1) + 1)):
            continue
        if total == 0 and any(p['record_count'] != 0 for p in valid):
            continue
        proven.append({'municipality_ibge': key[1], 'modality': key[2], 'start': key[3], 'end': key[4],
                       'evidence': [{'task_id': str(p['id']), 'source_id': str(p['source_id']),
                                     'sha256': p['sha256'], 'consulted_at': str(p['consulted_at'])} for p in valid]})
    return proven


def missing_windows(start, end, verified):
    covered = set()
    for first, last in verified:
        current = max(start, first)
        while current <= min(end, last):
            covered.add(current)
            current += timedelta(days=1)
    result = []
    current = start
    while current <= end:
        if current in covered:
            current += timedelta(days=1)
            continue
        first = current
        while current < end and current - first < timedelta(days=6) and current + timedelta(days=1) not in covered:
            current += timedelta(days=1)
        result.append((first, current))
        current += timedelta(days=1)
    return result


def create_publication_plan(ctx, body):
    ctx.require('sources.sync')
    if not body.publications or any((body.updates, body.items, body.results, body.contracts, body.contract_updates, body.atas, body.pca)):
        raise ValueError('Este plano é exclusivo para publicações, sem inferir cobertura das demais fases.')
    if set(body.modalities) - COLLECTABLE_CODES:
        raise ValueError('Confira o domínio oficial de modalidades.')
    known = {r['ibge'] for r in ctx.db.all('SELECT ibge FROM municipality')}
    if set(body.municipalities) - known:
        raise ValueError('Município fora do cadastro verificado.')
    scope = json.loads(body.model_dump_json())
    scope['municipalities'].sort()
    scope['modalities'].sort()
    key = hashlib.sha256(encoded(scope).encode()).hexdigest()
    ctx.db.execute('SELECT pg_advisory_xact_lock(hashtextextended(:key,0))', {'key': ctx.org_id + ':municipal-plan:' + key})
    old = ctx.db.one("SELECT id FROM history_collection WHERE org_id=:o AND scope->'_campaign'->>'key'=:k", {'o': ctx.org_id, 'k': key})
    if old:
        return {'id': str(old['id']), 'reused_plan': True}
    rows = ctx.db.all("""SELECT t.id,t.collection_id,t.provider,t.arguments,t.state,p.result,p.record_count,
        s.id AS source_id,s.sha256,s.consulted_at,s.http_status,s.classification AS source_classification
        FROM history_task t JOIN history_collection c ON c.id=t.collection_id AND c.org_id=t.org_id
        LEFT JOIN history_page p ON p.task_id=t.id AND p.org_id=t.org_id
        LEFT JOIN source_observation s ON s.id=p.source_id
        WHERE t.org_id=:o AND c.dataset='official' AND t.provider='PNCP'
          AND t.arguments->>'municipality_ibge'=ANY(:cities)
          AND t.arguments->>'start_date'<=:end AND t.arguments->>'end_date'>=:start
        ORDER BY t.collection_id,t.task_key LIMIT 50001""",
        {'o': ctx.org_id, 'cities': body.municipalities, 'start': body.start.isoformat(), 'end': body.end.isoformat()})
    if len(rows) > 50000:
        raise ValueError('Divida o período antes de conciliar as tarefas existentes.')
    reused = evidenced_windows(rows)
    scope['_campaign'] = {'key': key, 'reused_publication_windows': reused,
                          'note': 'Reaproveitamento da resposta na data documentada; não comprova todas as compras.'}
    cid = identifier()
    ctx.db.execute('INSERT INTO history_collection(org_id,id,actor_id,scope) VALUES (:o,:i,:a,CAST(:s AS jsonb))',
                   {'o': ctx.org_id, 'i': cid, 'a': ctx.actor_id, 's': encoded(scope)})
    count = 0
    for city in body.municipalities:
        for modality in body.modalities:
            ranges = [(date.fromisoformat(p['start']), date.fromisoformat(p['end'])) for p in reused
                      if p['municipality_ibge'] == city and p['modality'] == modality]
            for first, last in missing_windows(body.start, body.end, ranges):
                history.queue(ctx, cid, 'PNCP', {'provider': 'PNCP', 'municipality_ibge': city, 'modality': modality,
                    'start_date': first.isoformat(), 'end_date': last.isoformat(), 'page': 1, 'size': body.size})
                count += 1
    ctx.audit('history.campaign_planned', cid, {'initial_tasks': count, 'reused_windows': len(reused), 'network_requests': 0})
    return {'id': cid, 'reused_plan': False, 'initial_tasks': count, 'reused_windows': len(reused)}
