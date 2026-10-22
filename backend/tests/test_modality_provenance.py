"""I04_04: no live calls; generated observations in isolated PostgreSQL only."""
import hashlib,json
from copy import deepcopy
from uuid import uuid4
import httpx,pytest
from app import sources,history_sources,modality
from app.db import encoded,DB
from test_history_filters import filtered
from test_history_contract import fixture_history

def proof(code=6):
    record={'numeroControlePNCP':'00000000000001-1-42/2025','modalidadeId':code}
    return modality.publication(record,'PNCP',str(uuid4()),'a'*64,hashlib.sha256(encoded(record).encode()).hexdigest(),6)

def parent(provider='PNCP',value=None):
    return {'id':str(uuid4()),'provider':provider,'source_id':str(uuid4()),'revision_hash':'b'*64,
        'obligation_id':'00000000000001-1-42/2025','metadata':{'modality_provenance':value or proof()}}

@pytest.mark.parametrize('value',[None,False,0,-1,6.0,'6',{'id':6},9223372036854775808])
def test_only_documented_integer_int64_is_accepted(value):
    assert proof(value)['state']=='unknown'

def test_namespaced_proof_and_parent_chain_are_immutable():
    root=proof();before=deepcopy(root);p=parent(value=root)
    item=modality.inherit(p,'PNCP_ITENS');result=modality.inherit(parent('PNCP_ITENS',item),'PNCP_RESULTADOS')
    assert root==before and root['code']=='6' and root['namespace']==modality.NAMESPACE
    assert len(result['lineage'])==2 and modality.normalize('PNCP_RESULTADOS',{'modality_provenance':result})==result
    assert result['evidence']['field']=='modalidadeId' and result['evidence']['source_contract_version']=='1.0'

@pytest.mark.parametrize('provider',['PNCP_CONTRATOS','SICOM','COMPRAS_CATMAT','SYNTHETIC_OPPORTUNITIES'])
def test_namespace_cannot_be_assumed_for_other_providers(provider):
    assert modality.normalize(provider,{'modality':6,'modality_provenance':proof()})['code'] is None

def test_legacy_future_version_missing_proof_and_wrong_parent_remain_unknown():
    assert modality.normalize('PNCP',{'modality':6})['reason']=='legacy_without_proof'
    p=proof();p['version']=2;assert modality.normalize('PNCP',{'modality_provenance':p})['state']=='unknown'
    p=proof();p['evidence']['source_contract_version']='future';assert modality.normalize('PNCP',{'modality_provenance':p})['state']=='unknown'
    p=proof();p['evidence']['source_sha256']='not-a-hash';assert modality.normalize('PNCP',{'modality_provenance':p})['state']=='unknown'
    p=parent();p['obligation_id']='other';assert modality.inherit(p,'PNCP_ITENS')['state']=='unknown'
    assert modality.inherit(parent(),'PNCP_RESULTADOS')['state']=='unknown'
    assert modality.normalize('PNCP_RESULTADOS',{'modality_provenance':proof()})['state']=='unknown'

@pytest.fixture
def ingestion(app,login):
    c=login();identity=c.get('/api/v1/auth/context').json()
    with app.state.database.engine.connect() as connection:
        transaction=connection.begin();db=DB(connection)
        db.execute("SELECT set_config('irps.org_id',:o,true),set_config('irps.actor_id',:a,true)",{'o':identity['org_id'],'a':identity['actor_id']})
        try:yield sources.job_context(db,identity['org_id'],identity['actor_id'])
        finally:transaction.rollback()

def collect(ctx,code=6,include=True):
    seq=int(uuid4().hex[:10],16);identity=f'00000000000001-1-{seq}/2025'
    record={'numeroControlePNCP':identity,'orgaoEntidade':{'cnpj':'00000000000001','razaoSocial':'Generated test'},
        'unidadeOrgao':{'codigoUnidade':'TEST','codigoIbge':'3131307'},'anoCompra':2025,'sequencialCompra':seq,
        'objetoCompra':'Pregão 6 in free text is not proof','dataPublicacaoPncp':'2025-01-02T00:00:00'}
    if include:record['modalidadeId']=code
    args={'provider':'PNCP','start_date':'2025-01-01','end_date':'2025-01-07','page':1,'size':10,'modality':6}
    sources.sync(ctx,args,httpx.MockTransport(lambda r:httpx.Response(200,json={'data':[record],'totalPaginas':1})))
    p=ctx.db.one("SELECT * FROM procurement_fact WHERE provider='PNCP' AND obligation_id=:o AND is_current",{'o':identity})
    return record,args,p

def items(ctx,p):
    args={'provider':'PNCP_ITENS','procurement_id':str(p['id']),'page':1,'size':10}
    response=[{'numeroItem':1,'descricao':'Generated paper','unidadeMedida':'caixa','quantidade':3}]
    sources.sync(ctx,args,httpx.MockTransport(lambda r:httpx.Response(200,json=response)))
    return ctx.db.one("SELECT * FROM procurement_fact WHERE provider='PNCP_ITENS' AND obligation_id=:o AND is_current",{'o':p['obligation_id']})

def test_ingested_publication_items_results_and_revisions(ingestion):
    ctx=ingestion;record,args,p=collect(ctx);item=items(ctx,p)
    assert modality.normalize('PNCP',p['metadata'])['code']=='6'
    assert modality.normalize('PNCP_ITENS',item['metadata'])['code']=='6'
    result=[{'sequencialResultado':1,'dataResultado':'2025-01-03','situacaoCompraItemResultadoId':'1','quantidadeHomologada':2}]
    history_sources.results(ctx,{'procurement_id':str(item['id'])},httpx.MockTransport(lambda r:httpx.Response(200,json=result)))
    r=ctx.db.one("SELECT * FROM procurement_fact WHERE provider='PNCP_RESULTADOS' AND obligation_id=:o AND is_current",{'o':p['obligation_id']})
    assert r['phase']=='homologado' and len(modality.normalize(r['provider'],r['metadata'])['lineage'])==2
    assert items(ctx,p)['id']==item['id'] # Repeat consultation remains idempotent.
    record['modalidadeId']=7
    sources.sync(ctx,args,httpx.MockTransport(lambda r:httpx.Response(200,json={'data':[record],'totalPaginas':1})))
    new=ctx.db.one("SELECT * FROM procurement_fact WHERE provider='PNCP' AND obligation_id=:o AND is_current",{'o':p['obligation_id']});changed=items(ctx,new)
    assert changed['item_version']==item['item_version']+1 and changed['supersedes_id']==item['id']
    assert modality.normalize(changed['provider'],changed['metadata'])['code']=='7'
    assert modality.normalize(changed['provider'],changed['metadata'])['evidence']['request_matches'] is None
    assert modality.normalize(new['provider'],new['metadata'])['evidence']['request_matches'] is False
    assert modality.normalize(item['provider'],item['metadata'])['code']=='6' # Old evidence preserved.

def test_request_and_free_text_never_replace_missing_field(ingestion):
    ctx=ingestion;_,_,p=collect(ctx,include=False)
    assert p['metadata']['modality'] is None and modality.normalize(p['provider'],p['metadata'])['state']=='unknown'
    item=items(ctx,p);assert item['metadata']['modality'] is None
    assert modality.normalize(item['provider'],item['metadata'])['state']=='unknown'

def test_cache_preserves_missing_value_and_document_bytes(ingestion,monkeypatch):
    ctx=ingestion;_,_,p=collect(ctx,include=False)
    observation=ctx.db.one('SELECT * FROM source_observation WHERE id=:i',{'i':p['source_id']})
    def forbidden(*a,**k):raise AssertionError('Cache should not make a network call')
    monkeypatch.setattr(sources,'public_get',forbidden)
    _,_,raw,data=sources.cached_get(ctx,'PNCP',observation['url'])
    assert hashlib.sha256(raw).hexdigest()==observation['sha256']
    assert 'modalidadeId' not in data['data'][0]

def test_contract_does_not_inherit_or_accept_undocumented_field(ingestion):
    ctx=ingestion;seq=uuid4().hex;record={'numeroControlePNCP':'test-contract-'+seq,'orgaoEntidade':{'cnpj':'00000000000001'},'unidadeOrgao':{'codigoIbge':'3131307'},'objetoContrato':'Generated contract','dataAssinatura':'2025-01-04','tipoContrato':{'id':1},'modalidadeId':6}
    history_sources.contracts(ctx,{'cnpj':'00000000000001','start_date':'2025-01-01','end_date':'2025-01-07'},httpx.MockTransport(lambda r:httpx.Response(200,json={'data':[record],'totalPaginas':1})))
    row=ctx.db.one("SELECT * FROM procurement_fact WHERE provider='PNCP_CONTRATOS' AND event_identity=:e",{'e':record['numeroControlePNCP']+':contract'})
    assert row['quantity'] is None and row['metadata']['modality_provenance']['state']=='unknown'
    assert modality.normalize(row['provider'],row['metadata'])['code'] is None

def test_api_keeps_unknown_facts_and_explicitly_rejects_modality_filters(filtered):
    pid,add,get,client,_=filtered
    add(metadata={'modality':6});add(provider='OTHER_TEST_SOURCE',metadata={})
    result=get();assert result['summary']['observed_records']==2
    assert all(e['modality']['state']=='unknown' for r in result['municipalities'] for e in r['evidence'])
    args={'phase':'homologado','start':'2025-01-01','end':'2025-12-31','municipalities':'3131307'}
    options=client.get(f'/api/v1/director/history/{pid}/filters',params=args).json()
    assert options['modality_available'] is False and options['modality_unknown_handling']=='not_filtered'
    assert options['modality_normalization_version']==1
    for path in [f'/api/v1/director/history/{pid}',f'/api/v1/director/history/{pid}/filters',f'/api/v1/catalogue-intelligent/products/{pid}/history']:
        for key in ['modality','modalidade','modality_code']:
            response=client.get(path,params={**args,key:6});assert response.status_code==422,response.text
            assert response.json()['detail']['code']=='HISTORY_MODALITY_UNAVAILABLE'
    assert get('PNCP_RESULTADOS')['summary']['observed_records']==1

def test_known_proof_is_additive_in_history_without_changing_totals(filtered):
    _,add,get,_,_=filtered
    item=modality.inherit(parent(),'PNCP_ITENS')
    result=modality.inherit(parent('PNCP_ITENS',item),'PNCP_RESULTADOS')
    add(quantity='3',metadata={'modality':6,'modality_provenance':result})
    data=get();e=data['municipalities'][next(i for i,r in enumerate(data['municipalities']) if r['evidence'])]['evidence'][0]
    assert e['modality']['namespace']==modality.NAMESPACE and e['modality']['code']=='6'
    assert data['summary']['observed_quantity']=='3.00000000' or float(data['summary']['observed_quantity'])==3
