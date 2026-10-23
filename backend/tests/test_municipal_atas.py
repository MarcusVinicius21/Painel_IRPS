import httpx
import pytest
from app import sources,history_sources,history
from app.db import identifier,encoded
from app.opportunity_schemas import HistoricalScope
from app.municipal_contracts import create_ata_plan,create_linked_ata_plan
from test_municipal_items import parent


def record(parent,number=1,**extra):
    _,pid=parent
    return {'numeroControlePNCP':pid+'-'+str(number),'sequencialAta':number,'numeroAtaRegistroPreco':str(number)+'/2025',
        'dataVigenciaInicio':'2025-10-01','dataVigenciaFim':'2026-06-30','cancelado':False,**extra}


def collect(app,parent,data):
    ctx,pid=parent
    with app.state.database.transaction(ctx['org_id'],ctx['actor_id']) as db:
        result=history_sources.atas(sources.job_context(db,ctx['org_id'],ctx['actor_id']),
            {'procurement_id':pid,'page':1,'size':10},httpx.MockTransport(lambda _:httpx.Response(200,json=data)))
        source=db.one('SELECT metadata FROM source_observation WHERE id=:i',{'i':result['source_id']})
    return result,source['metadata']


def test_ata_revision_preserves_validity_and_never_creates_purchase_quantity(app,parent):
    old=record(parent,quantidade=999)
    _,first=collect(app,parent,{'data':[old],'totalPaginas':1})
    response,second=collect(app,parent,{'data':[{**old,'dataVigenciaFim':'2026-12-31','cancelado':True}],'totalPaginas':1})
    before,after=first['ata_summaries'][0],second['ata_summaries'][0]
    assert before['validity_end']=='2026-06-30' and after['validity_end']=='2026-12-31'
    assert before['revision_hash']!=after['revision_hash'] and not before['cancelled'] and after['cancelled']
    assert before['registered_quantity'] is None and after['registered_quantity'] is None
    assert response['phase']=='ata_registro' and not response['purchase_inferred'] and not response['quantities_collected']
    ctx,pid=parent
    with app.state.database.transaction(ctx['org_id'],ctx['actor_id']) as db:
        assert db.one("SELECT count(*) AS n FROM procurement_fact WHERE org_id=:o AND provider LIKE 'PNCP_ATAS%'",{'o':ctx['org_id']})['n']==0


def ata_collection(app,parent):
    ctx,pid=parent;cid=identifier()
    scope=HistoricalScope(municipalities=['3131307'],start='2025-10-01',end='2025-10-07',publications=False,
        atas=True,items=False,results=False,size=10).model_dump(mode='json')
    with app.state.database.transaction(ctx['org_id'],ctx['actor_id']) as db:
        worker=sources.job_context(db,ctx['org_id'],ctx['actor_id'])
        db.execute('INSERT INTO history_collection(org_id,id,actor_id,scope) VALUES (:o,:c,:a,CAST(:s AS jsonb))',
            {'o':ctx['org_id'],'c':cid,'a':ctx['actor_id'],'s':encoded(scope)})
        history.queue(worker,cid,'PNCP_ATAS',{'procurement_id':pid,'page':1,'size':10})
    return cid


def test_detailed_ata_pagination_reaches_all_pages(app,parent):
    ctx,_=parent;cid=ata_collection(app,parent);calls=[]
    def handler(request):
        page=int(request.url.params['pagina']);calls.append(page)
        assert request.url.params['tamanhoPagina']=='10'
        values=[record(parent,n) for n in range(1,11)] if page==1 else [record(parent,11)]
        return httpx.Response(200,json={'data':values,'totalPaginas':2})
    for _ in range(3):history.advance(app.state.database,ctx['org_id'],ctx['actor_id'],cid,1,httpx.MockTransport(handler))
    with app.state.database.transaction(ctx['org_id'],ctx['actor_id']) as db:
        state=history.get(sources.job_context(db,ctx['org_id'],ctx['actor_id']),cid)
    assert calls==[1,2] and state['pages']==2 and state['records']==11 and state['state']=='completed'
    assert state['execution']['municipal_purchase_completeness'] is None


def test_missing_ata_endpoint_is_inconclusive_and_does_not_complete_the_scope(app,parent):
    ctx,_=parent;cid=ata_collection(app,parent)
    assert history.advance(app.state.database,ctx['org_id'],ctx['actor_id'],cid,1,
        httpx.MockTransport(lambda _:httpx.Response(404)))['pages']==0
    with app.state.database.transaction(ctx['org_id'],ctx['actor_id']) as db:
        state=history.get(sources.job_context(db,ctx['org_id'],ctx['actor_id']),cid)
    assert state['error_code']=='HTTP_404' and not state['execution']['complete_known_plan']


def test_unknown_identity_and_status_remain_pending_without_assumed_quantity():
    summary=history_sources.ata_summary({'numeroAtaRegistroPreco':'Número local sem identidade nacional'})
    assert summary['identity_pending'] and summary['cancelled'] is None and summary['registered_quantity'] is None


def test_ata_index_plan_separates_publication_updates_and_municipal_identity(app,parent):
    ctx,pid=parent
    with app.state.database.transaction(ctx['org_id'],ctx['actor_id']) as db:
        cnpj=db.one('SELECT metadata FROM procurement_fact WHERE id=:i',{'i':pid})['metadata']['purchase']['cnpj']
        body=HistoricalScope(municipalities=['3131307'],start='2025-10-01',end='2025-10-07',
            publications=False,items=False,results=False,atas=True,organization_cnpjs=[cnpj])
        worker=sources.job_context(db,ctx['org_id'],ctx['actor_id'])
        publication=create_ata_plan(worker,body);updates=create_ata_plan(worker,body,updated=True)
        again=create_ata_plan(worker,body)
        saved=db.one('SELECT scope FROM history_collection WHERE org_id=:o AND id=:i',{'o':ctx['org_id'],'i':publication['id']})
    assert publication['id']!=updates['id'] and publication['id']==again['id'] and again['reused_plan']
    assert saved['scope']['_campaign']['period_basis']=='validity_overlap'


def test_ata_index_rejects_other_cnpj_and_keeps_registered_amounts_unknown(app,parent):
    ctx,pid=parent
    with app.state.database.transaction(ctx['org_id'],ctx['actor_id']) as db:
        cnpj=db.one('SELECT metadata FROM procurement_fact WHERE id=:i',{'i':pid})['metadata']['purchase']['cnpj']
        worker=sources.job_context(db,ctx['org_id'],ctx['actor_id'])
        args={'cnpj':cnpj,'start_date':'2025-10-01','end_date':'2025-10-07','page':1,'size':10}
        with pytest.raises(sources.SourceFault):
            history_sources.updated_index(worker,'PNCP_ATAS_PUBLICACAO',args,httpx.MockTransport(lambda _:httpx.Response(200,
                json={'data':[{'cnpjOrgao':'00000000000000'}],'totalPaginas':1})))
        response=history_sources.updated_index(worker,'PNCP_ATAS_PUBLICACAO',args,httpx.MockTransport(lambda _:httpx.Response(200,
            json={'data':[{'cnpjOrgao':cnpj,'numeroControlePNCPAta':'Ata fictícia do QA','vigenciaFim':'2026-12-31'}],'totalPaginas':1})))
        source=db.one('SELECT metadata FROM source_observation WHERE id=:i',{'i':response['source_id']})
    assert response['phase']=='ata_registro' and not response['quantities_collected']
    assert response['period_basis']=='validity_overlap'
    assert source['metadata']['ata_summaries'][0]['registered_quantity'] is None


def test_linked_ata_plan_queues_only_the_existing_publication_identity(app,parent):
    ctx,pid=parent
    with app.state.database.transaction(ctx['org_id'],ctx['actor_id']) as db:
        worker=sources.job_context(db,ctx['org_id'],ctx['actor_id'])
        first=create_linked_ata_plan(worker,[pid]);again=create_linked_ata_plan(worker,[pid])
        task=db.one('SELECT provider,arguments FROM history_task WHERE org_id=:o AND collection_id=:c',{'o':ctx['org_id'],'c':first['id']})
    assert first['id']==again['id'] and again['reused_plan']
    assert task['provider']=='PNCP_ATAS' and task['arguments']['procurement_id']==pid
    assert task['arguments']['page']==1 and first['municipal_purchase_completeness'] is None
