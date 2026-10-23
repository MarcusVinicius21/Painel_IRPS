import httpx
import pytest
from app import sources,history_sources,history
from app.municipal_contracts import create_contract_plan,create_linked_contract_plan
from app.municipal_plan import evidenced_windows
from app.opportunity_schemas import HistoricalScope
from test_municipal_items import parent
from test_municipal_plan import page


@pytest.fixture
def contract_parent(app,parent):
    ctx,pid=parent
    with app.state.database.transaction(ctx['org_id'],ctx['actor_id']) as db:
        publication=db.one('SELECT * FROM procurement_fact WHERE org_id=:o AND id=:i',{'o':ctx['org_id'],'i':pid})
    return ctx,publication


def record(contract_parent,number=1,**extra):
    _,p=contract_parent;cnpj=p['metadata']['purchase']['cnpj']
    return {'numeroControlePNCP':f'{cnpj}-2-{number:06}/2025','numeroControlePncpCompra':p['obligation_id'],
        'orgaoEntidade':{'cnpj':cnpj,'razaoSocial':'Órgão fictício do QA','esferaId':'M'},
        'unidadeOrgao':{'codigoIbge':'3131307','codigoUnidade':'1'},'objetoContrato':'Contrato global fictício de teste',
        'tipoContrato':{'id':1,'nome':'Contrato'},'valorInicial':100,'valorGlobal':120,
        'dataAssinatura':'2025-10-04','dataAtualizacaoGlobal':'2025-10-05T10:00:00',**extra}


def collect(app,parent,records,*,linked=False,updated=False):
    ctx,p=parent;cnpj=p['metadata']['purchase']['cnpj']
    args={'cnpj':cnpj,'start_date':'2025-10-01','end_date':'2025-10-07','size':10,'page':1}
    if linked:args={'procurement_id':str(p['id']),'size':10,'page':1}
    with app.state.database.transaction(ctx['org_id'],ctx['actor_id']) as db:
        return history_sources.contracts(sources.job_context(db,ctx['org_id'],ctx['actor_id']),args,
            httpx.MockTransport(lambda _:httpx.Response(200,json={'data':records,'totalPaginas':1})),updated,linked)


def observed(app,parent):
    ctx,p=parent;prefix=p['metadata']['purchase']['cnpj']+'-2-'
    with app.state.database.transaction(ctx['org_id'],ctx['actor_id']) as db:
        return db.all("SELECT * FROM procurement_fact WHERE org_id=:o AND provider='PNCP_CONTRATOS' AND event_identity LIKE :prefix ORDER BY event_identity,is_current",{'o':ctx['org_id'],'prefix':prefix+'%'})


def test_multiple_global_contracts_and_commitment_are_not_item_quantities(app,contract_parent):
    records=[record(contract_parent),record(contract_parent,2,tipoContrato={'id':7,'nome':'Empenho'})]
    response=collect(app,contract_parent,records)
    assert response['records']==2 and not response['quantities_collected']
    rows=observed(app,contract_parent)
    assert len(rows)==2 and rows[0]['phase']=='contratado' and rows[1]['phase']=='empenhado'
    assert len({r['event_identity'] for r in rows})==2 and len({r['obligation_id'] for r in rows})==1
    assert all(r['quantity'] is None and r['unit_price'] is None and r['item_id'] is None for r in rows)
    assert all(r['amount']==100 and r['metadata']['global_value']=='120' and not r['metadata']['financial_execution_proven'] for r in rows)
    assert rows[1]['metadata']['commitment_instrument_only']


def test_rectification_and_late_response_preserve_versions_not_added_amounts(app,contract_parent):
    collect(app,contract_parent,[record(contract_parent)])
    change=record(contract_parent,valorInicial=150,valorGlobal=300,numeroRetificacao=1,dataAtualizacaoGlobal='2025-11-01T10:00:00')
    collect(app,contract_parent,[change],updated=True)
    assert collect(app,contract_parent,[change],updated=True)['new_revisions']==0
    collect(app,contract_parent,[record(contract_parent,valorInicial=80,dataAtualizacaoGlobal='2025-09-01T10:00:00')])
    rows=observed(app,contract_parent);current=[r for r in rows if r['is_current']]
    assert len(rows)==3 and len(current)==1 and current[0]['amount']==150
    assert current[0]['metadata']['rectification_number']==1 and current[0]['metadata']['global_value']=='300'
    assert sum(r['metadata']['late_revision'] for r in rows)==1
    assert current[0]['metadata']['cancellation_state']=='not_exposed_by_contract_response'


def test_official_link_endpoint_can_supply_relationship_missing_from_index(app,contract_parent):
    value=record(contract_parent,numeroControlePncpCompra=None)
    collect(app,contract_parent,[value]);collect(app,contract_parent,[value],linked=True)
    rows=observed(app,contract_parent);assert len(rows)==2
    current=next(r for r in rows if r['is_current'])
    assert current['obligation_id']==contract_parent[1]['obligation_id']
    assert current['metadata']['purchase_link_basis']=='official_purchase_endpoint'
    assert current['metadata']['purchase_identity'] is None
    wrong=record(contract_parent,numeroControlePncpCompra='different-purchase')
    with pytest.raises(sources.SourceFault) as error:collect(app,contract_parent,[wrong],linked=True)
    assert error.value.code=='INVALID_CONTRACT_PURCHASE_LINK'


@pytest.mark.parametrize('kind',['scope','duplicate','oversize'])
def test_contract_page_must_match_scope_and_is_never_truncated(app,contract_parent,kind):
    records=[record(contract_parent)]
    if kind=='scope':records[0]['orgaoEntidade']['cnpj']='00000000000000'
    if kind=='duplicate':records*=2
    if kind=='oversize':records=[record(contract_parent,n) for n in range(1,12)]
    with pytest.raises(sources.SourceFault):collect(app,contract_parent,records)
    assert observed(app,contract_parent)==[]


def test_contract_plan_is_idempotent_and_requires_municipal_buyers(app,contract_parent):
    ctx,p=contract_parent;cnpj=p['metadata']['purchase']['cnpj']
    body=HistoricalScope(municipalities=['3131307'],start='2025-10-01',end='2025-10-07',
        publications=False,items=False,results=False,contracts=True,organization_cnpjs=[cnpj])
    with app.state.database.transaction(ctx['org_id'],ctx['actor_id']) as db:
        worker=sources.job_context(db,ctx['org_id'],ctx['actor_id'])
        first=create_contract_plan(worker,body);again=create_contract_plan(worker,body)
    assert first['id']==again['id'] and again['reused_plan'] and first['initial_tasks']==1
    with pytest.raises(ValueError):
        with app.state.database.transaction(ctx['org_id'],ctx['actor_id']) as db:
            create_contract_plan(sources.job_context(db,ctx['org_id'],ctx['actor_id']),body.model_copy(update={'organization_cnpjs':['00000000000000']}))


def test_reconciliation_of_contract_windows_never_merges_different_cnpjs():
    a=page(provider='PNCP_CONTRATOS');a['arguments']['cnpj']='00000000000001'
    b=page(index=2,expected=2,provider='PNCP_CONTRATOS');b['arguments']['cnpj']='00000000000002'
    a['result']['expected_pages']=2
    assert evidenced_windows([a,b],'PNCP_CONTRATOS',('cnpj',))==[]


def test_linked_contract_plan_paginates_and_reopens_without_repeating_requests(app,contract_parent):
    ctx,p=contract_parent
    with app.state.database.transaction(ctx['org_id'],ctx['actor_id']) as db:
        worker=sources.job_context(db,ctx['org_id'],ctx['actor_id'])
        plan=create_linked_contract_plan(worker,[str(p['id'])])
        assert create_linked_contract_plan(worker,[str(p['id'])])['id']==plan['id']
    calls=[]
    def handler(request):
        assert '/contratos/contratacao/2025/1' in request.url.path
        number=int(request.url.params['pagina']);calls.append(number)
        records=[record(contract_parent,n) for n in range(1,21)] if number==1 else [record(contract_parent,21)]
        return httpx.Response(200,json={'data':records,'totalPaginas':2})
    for _ in range(3):history.advance(app.state.database,ctx['org_id'],ctx['actor_id'],plan['id'],1,httpx.MockTransport(handler))
    assert calls==[1,2] and len(observed(app,contract_parent))==21
    with app.state.database.transaction(ctx['org_id'],ctx['actor_id']) as db:
        saved=history.get(sources.job_context(db,ctx['org_id'],ctx['actor_id']),plan['id'])
    assert saved['state']=='completed' and saved['pages']==2
    assert saved['execution']['municipal_purchase_completeness'] is None


def test_contract_amendment_evidence_never_adds_to_original_global_value(app,contract_parent):
    ctx,p=contract_parent
    with app.state.database.transaction(ctx['org_id'],ctx['actor_id']) as db:
        plan=create_linked_contract_plan(sources.job_context(db,ctx['org_id'],ctx['actor_id']),[str(p['id'])])
    def handler(request):
        if request.url.path.endswith('/termos'):
            return httpx.Response(200,json=[{'sequencialTermoContrato':1,'tipoTermoContratoNome':'Aditivo fictício do QA',
                'valorGlobal':999,'prazoAditadoDias':90,'dataVigenciaFim':'2026-12-31'}])
        return httpx.Response(200,json={'data':[record(contract_parent,anoContrato=2025,sequencialContrato=1)],'totalPaginas':1})
    for _ in range(2):assert history.advance(app.state.database,ctx['org_id'],ctx['actor_id'],plan['id'],1,httpx.MockTransport(handler))['pages']==1
    with app.state.database.transaction(ctx['org_id'],ctx['actor_id']) as db:
        pages=db.all("SELECT p.result,s.body FROM history_page p JOIN source_observation s ON s.id=p.source_id WHERE p.org_id=:o AND p.collection_id=:c AND s.provider='PNCP_CONTRATO_TERMOS'",{'o':ctx['org_id'],'c':plan['id']})
    assert len(pages)==1 and pages[0]['result']['amounts_not_added_to_contract']
    assert pages[0]['result']['phase']=='termo_contratual' and '999' in pages[0]['body']
    contracts=observed(app,contract_parent)
    assert len(contracts)==1 and contracts[0]['amount']==100 and contracts[0]['quantity'] is None
