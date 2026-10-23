from uuid import uuid4
import httpx
import pytest
from app import sources,history_sources,opportunities
from app.municipal_results import create_result_plan
from app.opportunity_schemas import OpportunityFilter
from test_municipal_items import parent,item_sync,record


@pytest.fixture
def result_item(app,parent):
    item_sync(app,parent,[record(temResultado=True)])
    ctx,pid=parent
    with app.state.database.transaction(ctx['org_id'],ctx['actor_id']) as db:
        item=db.one("SELECT * FROM procurement_fact WHERE org_id=:o AND provider='PNCP_ITENS' AND metadata->>'parent_id'=:p AND is_current",{'o':ctx['org_id'],'p':pid})
    return ctx,item


def result(sequence=1,**extra):
    return {'sequencialResultado':sequence,'situacaoCompraItemResultadoId':'1','dataResultado':'2025-10-05',
        'quantidadeHomologada':2,'valorUnitarioHomologado':8,'valorTotalHomologado':16,
        'tipoPessoa':'PJ','niFornecedor':str(sequence).zfill(14),'nomeRazaoSocialFornecedor':'Fornecedor fictício do QA',**extra}


def consult(app,result_item,data,status=200):
    ctx,item=result_item
    with app.state.database.transaction(ctx['org_id'],ctx['actor_id']) as db:
        return history_sources.results(sources.job_context(db,ctx['org_id'],ctx['actor_id']),
            {'procurement_id':str(item['id'])},httpx.MockTransport(lambda _:httpx.Response(status,json=data) if status!=204 else httpx.Response(204)))


def rows(app,result_item):
    ctx,item=result_item
    with app.state.database.transaction(ctx['org_id'],ctx['actor_id']) as db:
        return db.all("SELECT f.*,s.body,s.metadata AS source_metadata FROM procurement_fact f JOIN source_observation s ON s.id=f.source_id WHERE f.org_id=:o AND f.provider='PNCP_RESULTADOS' AND f.metadata->>'parent_id'=:p ORDER BY f.event_identity,f.is_current",{'o':ctx['org_id'],'p':str(item['id'])})


def test_results_preserve_status_suppliers_unknown_numbers_and_parent_version(app,result_item):
    values=[result(),result(2,situacaoCompraItemResultadoId='2',dataCancelamento='2025-10-06'),
        result(3,quantidadeHomologada=None,valorTotalHomologado=None,valorUnitarioHomologado=None),
        result(4,situacaoCompraItemResultadoId=None)]
    assert consult(app,result_item,values)['records']==4
    observed=rows(app,result_item);assert len(observed)==4
    active,cancelled,unknown,status_missing=observed
    assert active['quantity']==2 and active['unit_price']==8 and active['amount']==16
    assert cancelled['metadata']['cancelled'] and not cancelled['metadata']['eligible_result']
    assert cancelled['quantity'] is None and cancelled['amount'] is None
    assert unknown['quantity'] is None and unknown['amount'] is None and unknown['unit_price'] is None
    assert not status_missing['metadata']['eligible_result'] and status_missing['quantity'] is None
    ctx,item=result_item
    assert all(r['item_id']==item['item_id'] and r['item_version']==item['item_version']
               and r['phase']=='homologado' and r['source_metadata']['natural_person_identifiers_redacted'] for r in observed)
    with app.state.database.transaction(ctx['org_id'],ctx['actor_id']) as db:
        filtered,_=opportunities.facts(sources.job_context(db,ctx['org_id'],ctx['actor_id']),
            OpportunityFilter(phase='homologado',start='2025-10-01',end='2025-10-31',item_ids=[item['item_id']]))
    assert {r['event_identity'] for r in filtered}=={active['event_identity'],unknown['event_identity']}


def test_cancelled_revision_and_replay_preserve_old_result(app,result_item):
    consult(app,result_item,[result()]);changed=[result(dataCancelamento='2025-10-06')]
    assert consult(app,result_item,changed)['new_revisions']==1
    assert consult(app,result_item,changed)['new_revisions']==0
    old,current=rows(app,result_item)
    assert not old['is_current'] and current['is_current'] and current['supersedes_id']==old['id']
    assert old['quantity']==2 and current['quantity'] is None


def test_natural_person_identity_is_redacted_from_stored_results(app,result_item):
    consult(app,result_item,[result(tipoPessoa='PF',niFornecedor='11111111111',nomeRazaoSocialFornecedor='Pessoa fictícia do QA')])
    observed=rows(app,result_item)[0]
    assert '11111111111' not in observed['body'] and 'Pessoa fictícia do QA' not in observed['body']
    assert observed['metadata']['supplier']['cnpj'] is None
    assert observed['source_metadata']['original_response_sha256']


@pytest.mark.parametrize('data',[[result(),result()],[result(True)],[{}],[None],None])
def test_invalid_results_are_not_silently_skipped_or_called_empty(app,result_item,data):
    with pytest.raises(sources.SourceFault):consult(app,result_item,data)
    assert rows(app,result_item)==[]


@pytest.mark.parametrize('status,data',[(200,[]),(204,None)])
def test_empty_success_is_endpoint_evidence_only(app,result_item,status,data):
    response=consult(app,result_item,data,status)
    assert response['records']==0 and response['phase']=='homologado'
    assert response['state']=='partial' and response['expected_pages']==1
    assert rows(app,result_item)==[]


def test_stale_item_cannot_attach_live_results_to_an_old_specification(app,parent,result_item):
    item_sync(app,parent,[record(temResultado=True,unidadeMedida='pacote de 20 unidades')])
    with pytest.raises(sources.SourceFault) as error:consult(app,result_item,[result()])
    assert error.value.code=='INVALID_PARENT_REVISION' and rows(app,result_item)==[]


def test_result_plan_uses_current_items_is_idempotent_and_does_not_claim_months(app,result_item):
    ctx,item=result_item
    with app.state.database.transaction(ctx['org_id'],ctx['actor_id']) as db:
        worker=sources.job_context(db,ctx['org_id'],ctx['actor_id'])
        first=create_result_plan(worker,['3131307'],'2025-10-01','2025-10-07')
        again=create_result_plan(worker,['3131307'],'2025-10-01','2025-10-07')
        task=db.one("SELECT * FROM history_task WHERE org_id=:o AND collection_id=:c AND arguments->>'procurement_id'=:p",{'o':ctx['org_id'],'c':first['id'],'p':str(item['id'])})
        saved=db.one('SELECT scope FROM history_collection WHERE org_id=:o AND id=:c',{'o':ctx['org_id'],'c':first['id']})['scope']
    assert task['provider']=='PNCP_RESULTADOS' and first['id']==again['id'] and again['new_tasks']==0
    assert again['result_date_coverage'] is None and again['municipal_purchase_completeness'] is None
    assert saved['_campaign']['discovery_period_basis']=='publication_date_of_parent_item'
    assert not saved['publications'] and saved['results']
