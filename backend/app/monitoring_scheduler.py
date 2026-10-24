"""Application-owned bounded worker; PostgreSQL cursor survives Codex and restarts."""
from datetime import date
from threading import Event,Thread
from sqlalchemy import text
from .db import encoded,normalize
from .sources import job_context
from .monitoring_collection import windows,plan_city
from .campaign_worker import tick
from .security import fail

def select_window(cities,cursor,today):
    if not cities:raise ValueError('No validated targets')
    months=windows(today);priority=[months[-2],months[-1],*reversed(months[:-2])]
    return cities[cursor%len(cities)],*priority[(cursor//len(cities))%len(priority)]

def ensure(ctx):
    ctx.db.execute('INSERT INTO monitoring_schedule(org_id) VALUES (:o) ON CONFLICT(org_id) DO NOTHING',{'o':ctx.org_id})

def status(ctx):
    ctx.require('read')
    row=ctx.db.one('SELECT enabled,cursor,next_run,last_run,last_request,last_error,last_result FROM monitoring_schedule WHERE org_id=:o',{'o':ctx.org_id})
    return normalize(row or {'enabled':False,'last_run':None,'next_run':None,'last_error':None,'last_result':{},'notice':'A atualização automática ainda não foi iniciada.'})

def request_refresh(ctx):
    ctx.require('sources.sync');ensure(ctx)
    row=ctx.db.one("UPDATE monitoring_schedule SET next_run=now(),last_request=now(),updated_at=now() WHERE org_id=:o AND (last_request IS NULL OR last_request<now()-interval '1 minute') RETURNING next_run",{'o':ctx.org_id})
    if not row:fail(429,'A atualização já foi solicitada. Aguarde um minuto.','REFRESH_THROTTLED')
    ctx.audit('monitoring.refresh_requested',ctx.org_id,{'network_executed_in_request':False})
    return normalize({'accepted':True,**row})

def cycle(database,org,actor,today=None,transport=None,sleep=None):
    key='irps-monitoring-schedule:'+org
    with database.engine.connect() as lock:
        if not lock.execute(text('SELECT pg_try_advisory_lock(hashtextextended(:k,0))'),{'k':key}).scalar():
            lock.commit();return {'state':'busy'}
        lock.commit()
        try:
            with database.transaction(org,actor) as db:
                ctx=job_context(db,org,actor);ensure(ctx)
                state=db.one('SELECT *,next_run<=now() AS due FROM monitoring_schedule WHERE org_id=:o FOR UPDATE',{'o':org})
                if not state['enabled'] or not state['due']:return {'state':'not_due'}
                cities=[r['municipality_ibge'] for r in db.all('SELECT municipality_ibge FROM monitoring_target WHERE org_id=:o AND monitoring_enabled ORDER BY municipality_ibge',{'o':org})]
                if not cities:return {'state':'no_targets'}
                city,first,last=select_window(cities,state['cursor'],today or date.today());plan=plan_city(ctx,city,first,last)
                db.execute("UPDATE monitoring_schedule SET next_run=now()+interval '5 minutes',updated_at=now() WHERE org_id=:o",{'o':org})
            kwargs={'sleep':sleep} if sleep else {}
            result=tick(database,org,actor,first,last,execute=True,max_attempts=3,max_seconds=60,interval_seconds=4,
                        collection_ids=[plan['id']],transport=transport,**kwargs)
            # Child item/result discovery is bounded and uses the existing fact identities.
            from .municipal_items import create_item_plan
            from .municipal_results import create_result_plan
            with database.transaction(org,actor) as db:
                ctx=job_context(db,org,actor)
                children=[create_item_plan(ctx,[city],first,last),create_result_plan(ctx,[city],first,last)]
                child_ids=[r['id'] for r in children]
            child=tick(database,org,actor,first,last,execute=True,max_attempts=3,max_seconds=60,interval_seconds=4,
                       collection_ids=child_ids,transport=transport,**kwargs)
            summary={'municipality_ibge':city,'start':str(first),'end':str(last),'pages':result.get('pages',0)+child.get('pages',0),
                     'attempts':result.get('attempts',0)+child.get('attempts',0),'source_completeness':None}
            with database.transaction(org,actor) as db:
                db.execute("UPDATE monitoring_schedule SET cursor=cursor+1,last_run=now(),last_error=NULL,last_result=CAST(:r AS jsonb),updated_at=now() WHERE org_id=:o",{'o':org,'r':encoded(summary)})
                job_context(db,org,actor).audit('monitoring.cycle_finished',city,summary)
            return summary
        except Exception as e:
            # Only class/code persisted; no exception messages that might contain keys.
            code=type(e).__name__
            with database.transaction(org,actor) as db:
                db.execute("UPDATE monitoring_schedule SET last_error=:e,next_run=now()+interval '5 minutes',updated_at=now() WHERE org_id=:o",{'o':org,'e':code})
                job_context(db,org,actor).audit('monitoring.cycle_failed',org,{'error_type':code})
            return {'state':'failed','error_type':code}
        finally:
            lock.execute(text('SELECT pg_advisory_unlock(hashtextextended(:k,0))'),{'k':key});lock.commit()

def start(database,settings):
    stop=Event()
    def loop():
        while not stop.wait(5):
            try:cycle(database,settings.operator_org_id,settings.operator_actor_id)
            except Exception:pass  # Database unavailable: retry; never mark a cycle as successful.
    thread=Thread(target=loop,name='irps-monitoring',daemon=True);thread.start()
    return stop,thread
