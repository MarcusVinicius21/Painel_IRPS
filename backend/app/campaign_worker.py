"""One bounded worker over every saved campaign, including older linked-plan snapshots."""
from . import sources
from .history_runner import run_tick


def select_next(ctx,start,end,collection_ids=None):
    ctx.require('sources.sync')
    args={'o':ctx.org_id,'start':str(start),'end':str(end),'filter_ids':collection_ids is not None,'ids':collection_ids or []}
    rows=ctx.db.all("""SELECT c.id FROM history_collection c
        WHERE c.org_id=:o AND c.dataset='official' AND c.scope ? '_campaign'
        AND c.scope->>'start'>=:start AND c.scope->>'end'<=:end
        AND (:filter_ids=false OR c.id=ANY(CAST(:ids AS uuid[])))
        AND c.state NOT IN ('completed','limited') AND c.error_code IS DISTINCT FROM 'USER_PAUSED'
        AND (c.resume_after IS NULL OR c.resume_after<=now())
        AND EXISTS(SELECT 1 FROM history_task t WHERE t.org_id=c.org_id AND t.collection_id=c.id AND t.attempts<3
            AND (t.state IN ('ready','failed','failed_retryable') OR (t.state='running' AND t.lease_until<now())))
        ORDER BY c.updated_at,c.id LIMIT 20""",args)
    return [str(r['id']) for r in rows]


def tick(database,org,actor,start,end,*,execute=False,max_attempts=24,max_seconds=160,interval_seconds=4,
         collection_ids=None,transport=None,sleep=None):
    if end<start or (end-start).days>366:raise ValueError('Use até doze meses por campanha.')
    with database.transaction(org,actor) as db:
        ids=select_next(sources.job_context(db,org,actor),start,end,collection_ids)
        pending=db.one("""SELECT count(*) AS n FROM history_task t JOIN history_collection c ON c.org_id=t.org_id AND c.id=t.collection_id
            WHERE t.org_id=:o AND c.dataset='official' AND c.scope ? '_campaign' AND c.scope->>'start'>=:start AND c.scope->>'end'<=:end
            AND c.state NOT IN ('completed','limited') AND c.error_code IS DISTINCT FROM 'USER_PAUSED'
            AND t.state IN ('ready','failed','failed_retryable','running') AND t.attempts<3
            AND (:filter_ids=false OR c.id=ANY(CAST(:ids AS uuid[])))""",{'o':org,'start':str(start),'end':str(end),
                'filter_ids':collection_ids is not None,'ids':collection_ids or []})['n'] if not ids else None
    if not ids:return {'executed':execute,'pages':0,'attempts':0,'selected_collections':[],
        'state':'no_eligible_requests_now','resumable_tasks':pending,'municipal_purchase_completeness':None}
    kwargs={'sleep':sleep} if sleep is not None else {}
    result=run_tick(database,org,actor,ids,execute=execute,max_attempts=max_attempts,max_seconds=max_seconds,
                    interval_seconds=interval_seconds,transport=transport,**kwargs)
    return {**result,'selected_collections':ids}
