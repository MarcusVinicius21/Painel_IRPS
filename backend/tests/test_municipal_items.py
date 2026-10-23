from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
import httpx
import pytest
from app import sources, history
from app.db import encoded,identifier
from app.opportunity_schemas import HistoricalScope
from app.municipal_items import create_item_plan,proven_item_parents
from test_pncp_update_versions import payload,run


@pytest.fixture
def parent(app,login):
    c=login();ctx=c.get('/api/v1/auth/context').json();cnpj=str(uuid4().int)[:14]
    run(app,ctx,payload(cnpj))
    with app.state.database.transaction(ctx['org_id'],ctx['actor_id']) as db:
        row=db.one("SELECT id FROM procurement_fact WHERE org_id=:o AND provider='PNCP' AND obligation_id=:p AND is_current",
                   {'o':ctx['org_id'],'p':cnpj+'-1-000001/2025'})
        db.execute("UPDATE source_backoff SET resume_after=now()-interval '1 second' WHERE org_id=:o",{'o':ctx['org_id']})
    return ctx,str(row['id'])


def record(number=1,**extra):
    return {'numeroItem':number,'descricao':'Mesmo nome de teste, identidades diferentes',
        'unidadeMedida':'caixa com 10 unidades','quantidade':3,'valorUnitarioEstimado':10,
        'valorTotal':30,'materialOuServicoNome':'Material',**extra}


def item_sync(app,parent,records):
    ctx,pid=parent
    with app.state.database.transaction(ctx['org_id'],ctx['actor_id']) as db:
        return sources.sync(sources.job_context(db,ctx['org_id'],ctx['actor_id']),
            {'provider':'PNCP_ITENS','procurement_id':pid,'page':1,'size':10},
            httpx.MockTransport(lambda _:httpx.Response(200,json=records)))


def collection(app,parent):
    ctx,pid=parent;cid=identifier()
    scope=HistoricalScope(municipalities=['3131307'],start='2025-10-01',end='2025-10-07',
        size=10,results=False).model_dump(mode='json');scope['publications']=False
    with app.state.database.transaction(ctx['org_id'],ctx['actor_id']) as db:
        worker=sources.job_context(db,ctx['org_id'],ctx['actor_id'])
        db.execute('INSERT INTO history_collection(org_id,id,actor_id,scope) VALUES (:o,:i,:a,CAST(:s AS jsonb))',
            {'o':ctx['org_id'],'i':cid,'a':ctx['actor_id'],'s':encoded(scope)})
        history.queue(worker,cid,'PNCP_ITENS',{'provider':'PNCP_ITENS','procurement_id':pid,'page':1,'size':10})
    return cid


def test_full_page_schedules_next_and_missing_unit_is_preserved(app,parent):
    ctx,pid=parent;cid=collection(app,parent);calls=[]
    def handler(request):
        page=int(request.url.params['pagina']);calls.append(page)
        records=[record(n) for n in range(1,11)] if page==1 else [record(11),record(12,unidadeMedida=None)]
        return httpx.Response(200,json=records)
    transport=httpx.MockTransport(handler)
    for _ in range(3):history.advance(app.state.database,ctx['org_id'],ctx['actor_id'],cid,1,transport)
    with app.state.database.transaction(ctx['org_id'],ctx['actor_id']) as db:
        rows=db.all("SELECT * FROM procurement_fact WHERE org_id=:o AND provider='PNCP_ITENS' AND metadata->>'parent_id'=:p",{'o':ctx['org_id'],'p':pid})
        state=history.get(sources.job_context(db,ctx['org_id'],ctx['actor_id']),cid)
    assert calls==[1,2] and state['state']=='completed' and state['pages']==2
    assert len(rows)==12 and len({r['event_identity'] for r in rows})==12
    missing=next(r for r in rows if r['metadata']['purchase']['number']==12)
    assert missing['quantity']==3 and missing['unit'] is None
    assert missing['item_id'] is None and missing['item_version'] is None
    assert missing['metadata']['missing_unit'] and missing['metadata']['technical_identity_pending']
    assert all(r['phase']=='publicado_estimado' and not r['metadata']['quantity_is_consumption'] for r in rows)


def test_item_revision_idempotence_and_concurrency(app,parent):
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda _:item_sync(app,parent,[record()]),range(2)))
    assert sum(r['new_revisions'] for r in results)==1
    changed=item_sync(app,parent,[record(quantidade=5,unidadeMedida='pacote com 20 unidades')])
    assert changed['new_revisions']==1
    ctx,pid=parent
    with app.state.database.transaction(ctx['org_id'],ctx['actor_id']) as db:
        rows=db.all("SELECT * FROM procurement_fact WHERE org_id=:o AND provider='PNCP_ITENS' AND metadata->>'parent_id'=:p ORDER BY is_current",{'o':ctx['org_id'],'p':pid})
    assert len(rows)==2 and sum(r['is_current'] for r in rows)==1
    assert rows[1]['supersedes_id']==rows[0]['id'] and rows[1]['item_version']==2
    assert rows[1]['quantity']==5 and rows[0]['quantity']==3


@pytest.mark.parametrize('records',[[record(n) for n in range(1,12)],[record(),record()],[record(True)]])
def test_invalid_item_page_is_not_silently_truncated(app,parent,records):
    with pytest.raises(sources.SourceFault):item_sync(app,parent,records)
    ctx,pid=parent
    with app.state.database.transaction(ctx['org_id'],ctx['actor_id']) as db:
        assert db.one("SELECT count(*) AS n FROM procurement_fact WHERE org_id=:o AND provider='PNCP_ITENS' AND metadata->>'parent_id'=:p",{'o':ctx['org_id'],'p':pid})['n']==0


@pytest.mark.parametrize('status',[404,409,410])
def test_missing_or_conflicting_endpoint_never_proves_empty_items(app,parent,status):
    ctx,_=parent;cid=collection(app,parent)
    result=history.advance(app.state.database,ctx['org_id'],ctx['actor_id'],cid,1,
        httpx.MockTransport(lambda _:httpx.Response(status)))
    assert result['pages']==0
    with app.state.database.transaction(ctx['org_id'],ctx['actor_id']) as db:
        state=history.get(sources.job_context(db,ctx['org_id'],ctx['actor_id']),cid)
    assert not state['execution']['complete_known_plan'] and state['error_code']=='HTTP_'+str(status)
    assert state['tasks']==[{'state':'blocked','count':1}]
    assert state['recent_errors'][0]['metadata']['http_status']==status


def test_item_plan_is_idempotent_and_preserves_pending_other_queues(app,parent):
    ctx,pid=parent
    with app.state.database.transaction(ctx['org_id'],ctx['actor_id']) as db:
        worker=sources.job_context(db,ctx['org_id'],ctx['actor_id'])
        first=create_item_plan(worker,['3131307'],'2025-10-01','2025-10-07')
        again=create_item_plan(worker,['3131307'],'2025-10-01','2025-10-07')
        assert db.one("SELECT count(*) AS n FROM history_task WHERE org_id=:o AND collection_id=:c AND arguments->>'procurement_id'=:p",{'o':ctx['org_id'],'c':first['id'],'p':pid})['n']==1
    assert first['id']==again['id'] and again['new_tasks']==0 and again['network_requests']==0
    assert again['municipal_purchase_completeness'] is None
    with app.state.database.transaction(ctx['org_id'],ctx['actor_id']) as db:
        other=create_item_plan(sources.job_context(db,ctx['org_id'],ctx['actor_id']),['3131307'],'2025-10-01','2025-10-08')
    assert other['parents_in_other_queues']>=1


def test_explicit_204_completes_only_the_item_endpoint_scope(app,parent):
    ctx,_=parent;cid=collection(app,parent)
    result=history.advance(app.state.database,ctx['org_id'],ctx['actor_id'],cid,1,
        httpx.MockTransport(lambda _:httpx.Response(204)))
    assert result['pages']==1
    with app.state.database.transaction(ctx['org_id'],ctx['actor_id']) as db:
        state=history.get(sources.job_context(db,ctx['org_id'],ctx['actor_id']),cid)
    assert state['state']=='completed' and state['records']==0
    assert state['execution']['municipal_purchase_completeness'] is None


def test_connection_failure_recovers_from_same_item_checkpoint(app,parent):
    ctx,_=parent;cid=collection(app,parent)
    def fail(request):raise httpx.ReadTimeout('QA timeout',request=request)
    assert history.advance(app.state.database,ctx['org_id'],ctx['actor_id'],cid,1,httpx.MockTransport(fail))['pages']==0
    # Only this isolated test clock is advanced; production retry policy remains intact.
    assert app.state.settings.auth_mode=='local_test'
    with app.state.database.transaction(ctx['org_id'],ctx['actor_id']) as db:
        db.execute("UPDATE source_backoff SET resume_after=now()-interval '1 second' WHERE org_id=:o",{'o':ctx['org_id']})
        db.execute("UPDATE history_collection SET resume_after=now()-interval '1 second' WHERE org_id=:o AND id=:c",{'o':ctx['org_id'],'c':cid})
    assert history.advance(app.state.database,ctx['org_id'],ctx['actor_id'],cid,1,
        httpx.MockTransport(lambda _:httpx.Response(200,json=[record()])))['pages']==1
    with app.state.database.transaction(ctx['org_id'],ctx['actor_id']) as db:
        tasks=db.all('SELECT attempts,state FROM history_task WHERE org_id=:o AND collection_id=:c',{'o':ctx['org_id'],'c':cid})
    assert tasks==[{'attempts':2,'state':'done'}]


def test_reuse_requires_terminal_short_page_and_contiguous_evidenced_pages():
    def page(n,count=10,status=200):
        return {'collection_id':'a','arguments':{'procurement_id':'p','page':n,'size':10},'state':'done',
            'record_count':count,'http_status':status,'classification':'official','sha256':'a'*64,'consulted_at':'2026-10-23'}
    assert proven_item_parents([page(1)])==set()
    assert proven_item_parents([page(2,2)])==set()
    assert proven_item_parents([page(1),page(2,0)])=={'p'}
    assert proven_item_parents([page(1,0,status=404)])==set()
    assert proven_item_parents([page(1,0,status=204)])=={'p'}
