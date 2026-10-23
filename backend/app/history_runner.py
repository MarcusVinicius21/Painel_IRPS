"""Bounded, explicit worker tick reusing durable history tasks and page leases."""
import time
from sqlalchemy import text
from . import history, sources


def snapshot(database, org, actor, collection_ids):
    with database.transaction(org, actor) as db:
        ctx = sources.job_context(db, org, actor)
        result = []
        for cid in collection_ids:
            row = history.get(ctx, cid)
            if row['dataset'] != 'official':
                raise ValueError('Only existing official collections are eligible.')
            result.append({'id': cid, 'state': row['state'], 'pages': row['pages'],
                           'tasks': row['tasks'], 'execution': row['execution'], 'error_code': row['error_code']})
        return result


def run_tick(database, org, actor, collection_ids, *, execute=False, max_attempts=20,
             max_seconds=60, interval_seconds=1, transport=None, sleep=time.sleep):
    if not collection_ids or len(collection_ids) > 20 or len(set(collection_ids)) != len(collection_ids):
        raise ValueError('Escolha entre 1 e 20 coletas diferentes já cadastradas.')
    if not 1 <= max_attempts <= 300 or not 1 <= max_seconds <= 900:
        raise ValueError('Limite de até 300 tentativas e 900 segundos por execução.')
    if not 1 <= interval_seconds <= 60:
        raise ValueError('O intervalo entre avanços deve ficar entre 1 e 60 segundos.')
    initial = snapshot(database, org, actor, collection_ids)
    if not execute:
        return {'executed': False, 'attempts': 0, 'pages': 0, 'collections': initial}
    key = 'irps-public-history-runner:' + org
    with database.engine.connect() as lease:
        acquired = lease.execute(text('SELECT pg_try_advisory_lock(hashtextextended(:key,0))'), {'key': key}).scalar()
        lease.commit()
        if not acquired:
            return {'executed': False, 'busy': True, 'attempts': 0, 'pages': 0}
        try:
            started = time.monotonic()
            attempts = pages = 0
            stopped = set()
            while attempts < max_attempts and time.monotonic() - started < max_seconds:
                progress = False
                for cid in collection_ids:
                    if cid in stopped:
                        continue
                    if attempts >= max_attempts or time.monotonic() - started >= max_seconds:
                        break
                    before = snapshot(database, org, actor, [cid])[0]
                    if before['state'] in ('completed', 'limited'):
                        stopped.add(cid)
                        continue
                    result = history.advance(database, org, actor, cid, budget=1, transport=transport)
                    attempts += 1
                    pages += result.get('pages', 0)
                    progress |= bool(result.get('pages'))
                    if not result.get('pages') or result.get('paused'):
                        stopped.add(cid)
                    # Source failures stop only this collection in this tick.
                    sleep(interval_seconds)
                if not progress:
                    break
            return {'executed': True, 'attempts': attempts, 'pages': pages,
                    'collections': snapshot(database, org, actor, collection_ids),
                    'municipal_completeness': None}
        finally:
            lease.execute(text('SELECT pg_advisory_unlock(hashtextextended(:key,0))'), {'key': key})
            lease.commit()
