import copy,json
from datetime import date,timedelta
from decimal import Decimal
from uuid import uuid4
import httpx,pytest
from sqlalchemy import create_engine,text
from app import opportunities,history,opportunity_demo,history_sources,sources
from app.opportunity_schemas import OpportunityFilter,HistoricalScope
from app.security import stable_id

F={'dataset':'synthetic','phase':'homologado','start':'2024-01-01','end':'2025-12-31','q':'Papel A4'}

@pytest.fixture
def prepared(settings):
    opportunity_demo.seed_demo(settings)

def body_review(revision=0):
    return {'revision':revision,'criteria':{k:{'rating':4,'evidence':'Evidência fictícia para testar a revisão humana.'} for k in ('logistics','standardization','suppliers','requirements','deadline','availability')},
        'legal':'viable','operational':'viable','legal_evidence':'Análise fictícia, sem ato administrativo real.','operational_evidence':'Condição fictícia confirmada somente para teste.'}

def first(c):
    r=c.post('/api/v1/opportunities/query',json=F);assert r.status_code==200,r.text
    return r.json()['records'][0]

def test_history_metrics_and_missing_score(prepared,login):
    c=login();r=first(c);m=r['metrics']
    assert m['purchases']==72 and m['active_months']==24 and m['municipalities']==3
    assert Decimal(m['annual'][1]['variation_pct'])==100
    assert m['seasonality'] and len(m['seasonality'])==12
    assert Decimal(m['recurrence_pct'])==100 and Decimal(m['concentration_hhi']).quantize(Decimal('1'))==3333
    assert r['priority']['formula_version']=='opportunities-v1' and not m['future_purchase_promised']
    missing=opportunities.score(m,None,{'verified_ratio':Decimal(1),'complete_months':[x['month'] for x in m['monthly']]},{'recurrence':30,'spread':20,'price':20,'ease':30},3)
    assert missing['value'] is None and 'Confira os seis critérios de fornecimento e a viabilidade jurídica e operacional.' in missing['missing']
    assert len(m['monthly'])==24 and m['price']['count']>=3

def test_review_weighted_score_and_optimistic_conflict(prepared,login):
    c=login();r=first(c);url='/api/v1/opportunities/'+r['key']+'/review'
    current=c.post('/api/v1/opportunities/'+r['key']+'/detail',json=F).json().get('review')
    rev=current['revision'] if current else 0
    assert c.post(url,json=body_review(rev)).status_code==201
    assert c.post(url,json=body_review(rev)).status_code==409
    scored=first(c);assert scored['priority']['value'] is not None
    weighted={**F,'weights':{'recurrence':100,'spread':0,'price':0,'ease':0},'order':'priority'}
    assert Decimal(c.post('/api/v1/opportunities/query',json=weighted).json()['records'][0]['priority']['value'])==100

@pytest.mark.parametrize('extra',[{'weights':{'recurrence':100}}, {'months':[13]}, {'min_amount':'10','max_amount':'1'}, {'phase':'all'}, {'end':'2999-01-01'}, {'sql':'DROP TABLE scenario'}])
def test_filters_fail_closed(login,extra):
    assert login().post('/api/v1/opportunities/query',json={**F,**extra}).status_code==422

def test_combined_filters_and_group_intersection(prepared,login):
    c=login();gid=c.post('/api/v1/municipality-groups',json={'name':'Grupo fictício de teste','municipalities':['3131307']}).json()['id']
    f={**F,'groups':[gid],'municipalities':['3131307'],'months':[1,2],'years':[2025],'modalities':[6],'min_quantity':'1','max_price':'100000'}
    r=c.post('/api/v1/opportunities/query',json=f);assert r.status_code==200,r.text
    assert r.json()['records'][0]['metrics']['purchases']==2
    assert c.post('/api/v1/opportunities/query',json={**f,'municipalities':['3101607']}).json()['total']==0
    assert login('compras-b').post('/api/v1/opportunities/query',json={**F,'groups':[gid]}).status_code==404

def test_scenario_carries_selection_without_need_and_is_idempotent(prepared,login):
    c=login();r=first(c);d=c.post('/api/v1/opportunities/'+r['key']+'/detail',json=F).json()
    data={'filters':F,'title':'Rascunho da oportunidade fictícia','period':'2027','participants':[x['ibge'] for x in d['buyers']],
        'expected_fingerprint':d['fingerprint'],'confirm_review_required':True}
    url='/api/v1/opportunities/'+r['key']+'/scenario';key='opportunity-test-'+__import__('uuid').uuid4().hex
    a=c.post(url,json=data,headers={'Idempotency-Key':key});assert a.status_code==201,a.text
    b=c.post(url,json=data,headers={'Idempotency-Key':key});assert b.json()['id']==a.json()['id']
    s=a.json();assert s['snapshot']['inputs']=={} and s['snapshot']['prices']=={} and len(s['snapshot']['participants'])==3
    calc=c.post('/api/v1/scenarios/'+s['id']+'/calculate').json();assert calc['summary']['total'] is None and calc['summary']['blocked_lines']==3
    assert login('compras-b').get('/api/v1/scenarios/'+s['id']).status_code==404
    assert c.post(url,json={**data,'expected_fingerprint':'0'*64},headers={'Idempotency-Key':key+'-changed'}).status_code==409

def test_private_review_does_not_cross_org(prepared,login):
    a=login('empresa-a');b=login('empresa-b');r=first(a)
    old=a.post('/api/v1/opportunities/'+r['key']+'/detail',json=F).json()['review']
    assert a.post('/api/v1/opportunities/'+r['key']+'/review',json=body_review(old['revision'] if old else 0)).status_code==201
    other=b.post('/api/v1/opportunities/'+r['key']+'/detail',json=F).json()
    assert not other['review'] and other['priority']['value'] is None
    assert login('consulta-a').post('/api/v1/opportunities/'+r['key']+'/review',json=body_review()).status_code==403

def test_missing_month_and_price_do_not_become_zero():
    f=OpportunityFilter(start='2024-01-01',end='2024-03-31')
    row={'event_date':date(2024,1,15),'obligation_id':'x','municipality_ibge':'3131307','amount':None,'quantity':None,'unit_price':None,'metadata':{}}
    m=opportunities.indicators([row],f,set())
    assert m['monthly'][1]['purchases'] is None and m['price']['median'] is None and m['known_amount'] is None
    assert m['recurrence_pct'] is None and m['seasonality'] is None and m['annual'][0]['variation_pct'] is None
    assert opportunities.pct_change(Decimal(0),Decimal(1)) is None

def test_human_not_viable_disables_score(prepared,login):
    c=login();r=first(c);d=c.post('/api/v1/opportunities/'+r['key']+'/detail',json=F).json();review=body_review(d['review']['revision'] if d['review'] else 0)
    review['legal']='not_viable';assert c.post('/api/v1/opportunities/'+r['key']+'/review',json=review).status_code==201
    assert first(c)['priority']['value'] is None

def fixture_transport(fail_first=False):
    calls=[]
    def handler(request):
        calls.append(str(request.url))
        if fail_first and len(calls)==1:return httpx.Response(429,headers={'Retry-After':'120'})
        if request.url.path.endswith('/contratacoes/publicacao'):
            page=int(request.url.params['pagina']);data=[] if page>1 else [{'numeroControlePNCP':'00000000000001-1-000001/2025','orgaoEntidade':{'cnpj':'00000000000001','razaoSocial':'Órgão fictício','esferaId':'M'},'unidadeOrgao':{'codigoUnidade':'1','codigoIbge':'3131307'},'anoCompra':2025,'sequencialCompra':1,'objetoCompra':'Papel A4 de teste','dataPublicacaoPncp':'2025-01-02T10:00:00','modalidadeId':6}]
            return httpx.Response(200,json={'data':data,'totalPaginas':2})
        if request.url.path.endswith('/itens'):
            return httpx.Response(200,json=[{'numeroItem':1,'descricao':'Papel A4 oficial controlado no teste','unidadeMedida':'caixa','quantidade':10,'valorUnitarioEstimado':2,'valorTotal':20,'materialOuServicoNome':'Material','temResultado':True}])
        if request.url.path.endswith('/resultados'):
            return httpx.Response(200,json=[{'sequencialResultado':1,'quantidadeHomologada':9,'valorUnitarioHomologado':2,'valorTotalHomologado':18,'dataResultado':'2025-01-03','situacaoCompraItemResultadoId':'1','situacaoCompraItemResultadoNome':'Informado','tipoPessoa':'PJ','niFornecedor':'00000000000002','nomeRazaoSocialFornecedor':'Fornecedor fictício'}])
        if request.url.path.endswith('/contratos'):
            return httpx.Response(200,json={'data':[{'numeroControlePNCP':'00000000000001-1-000071/2025','numeroControlePncpCompra':'00000000000001-1-000001/2025','orgaoEntidade':{'cnpj':'00000000000001','razaoSocial':'Órgão fictício','esferaId':'M'},'unidadeOrgao':{'codigoUnidade':'1','codigoIbge':'3131307'},'objetoContrato':'Contrato de teste sem itens documentados','valorInicial':500,'valorGlobal':500,'dataAssinatura':'2025-01-04','tipoContrato':{'id':1,'nome':'Contrato'},'tipoPessoa':'PJ','niFornecedor':'00000000000002','nomeRazaoSocialFornecedor':'Fornecedor fictício'}],'totalPaginas':1})
        return httpx.Response(404)
    return httpx.MockTransport(handler),calls

def collection(c,max_pages=20):
    r=c.post('/api/v1/history-collections',json={'municipalities':['3131307'],'start':'2025-01-01','end':'2025-01-07','modalities':[6],'max_pages':max_pages});assert r.status_code==201,r.text;return r.json()['id']

def test_pagination_children_checkpoint_and_restart(app,login):
    c=login();cid=collection(c);transport,calls=fixture_transport();org=c.get('/api/v1/auth/context').json()
    for _ in range(5):history.advance(app.state.database,org['org_id'],org['actor_id'],cid,1,transport)
    r=c.get('/api/v1/history-collections/'+cid).json();assert r['state']=='completed' and r['pages']==4 and len(calls)==4
    history.advance(app.state.database,org['org_id'],org['actor_id'],cid,3,transport);assert len(calls)==4
    assert c.post('/api/v1/opportunities/query',json={'start':'2025-01-01','end':'2025-01-31','phase':'homologado'}).json()['total']>=1
    assert login('compras-b').get('/api/v1/history-collections/'+cid).status_code==404

def test_page_limit_stays_partial_and_can_extend(app,login):
    c=login();cid=collection(c,1);transport,calls=fixture_transport();org=c.get('/api/v1/auth/context').json()
    history.advance(app.state.database,org['org_id'],org['actor_id'],cid,3,transport)
    assert c.get('/api/v1/history-collections/'+cid).json()['state']=='limited' and len(calls)==1
    assert c.post('/api/v1/history-collections/'+cid+'/extend?max_pages=20').status_code==200
    for _ in range(2):history.advance(app.state.database,org['org_id'],org['actor_id'],cid,3,transport)
    assert c.get('/api/v1/history-collections/'+cid).json()['state']=='completed'

def test_contracts_stay_separate_from_item_quantity_and_price(app,login):
    c=login();payload={'municipalities':['3131307'],'start':'2025-01-01','end':'2025-01-07','publications':False,'contracts':True,'organization_cnpjs':['00000000000001'],'max_pages':5}
    made=c.post('/api/v1/history-collections',json=payload);assert made.status_code==201,made.text;cid=made.json()['id'];transport,_=fixture_transport();identity=c.get('/api/v1/auth/context').json()
    history.advance(app.state.database,identity['org_id'],identity['actor_id'],cid,1,transport)
    records=c.get('/api/v1/purchases?dataset=official&phase=contratado&limit=100').json()['records'];contract=next(r for r in records if r['provider']=='PNCP_CONTRATOS')
    assert contract['quantity'] is None and contract['unit_price'] is None and Decimal(contract['amount'])==500
    assert c.post('/api/v1/opportunities/query',json={'phase':'contratado','start':'2025-01-01','end':'2025-01-31'}).json()['total']==0

def test_reviewed_equivalence_requires_same_documented_unit(prepared,login):
    body={'name':'Veículos equivalentes para análise','category':'Mobilidade','unit':'veículo','members':[{'id':'cat-13','version':1},{'id':'cat-18','version':1}],
        'justification':'Os dois registros foram avaliados na mesma unidade documental.','evidence':'Referências internas de teste, sem dado oficial.','confirmed':True}
    assert login().post('/api/v1/opportunity-equivalences',json=body).status_code==201

def test_watch_registers_new_record_without_future_promise(prepared,settings,login):
    c=login();candidate=first(c);watch=c.post('/api/v1/opportunity-watches',json={'name':'Acompanhamento de teste '+uuid4().hex,'filters':F,'opportunity_key':candidate['key']});assert watch.status_code==201,watch.text
    identity=c.get('/api/v1/auth/context').json();engine=create_engine(settings.owner_database_url.get_secret_value())
    with engine.begin() as db:
        source=db.execute(text("SELECT id FROM source_observation WHERE org_id=:o AND provider='SYNTHETIC_OPPORTUNITIES' LIMIT 1"),{'o':identity['org_id']}).scalar_one()
        buyer=db.execute(text("SELECT id FROM buyer WHERE org_id=:o AND classification='synthetic' LIMIT 1"),{'o':identity['org_id']}).scalar_one()
        event='demo-alert-'+uuid4().hex;metadata=json.dumps({'synthetic':True,'record_level':'item','category':'Materiais de consumo','modality':6,'currency':'BRL','eligible_result':True})
        db.execute(text("""INSERT INTO procurement_fact(id,org_id,classification,provider,event_identity,revision_hash,source_id,buyer_id,municipality_ibge,item_id,item_version,description,unit,quantity,unit_price,amount,phase,event_date,obligation_id,metadata)
          VALUES (:id,:org,'synthetic','SYNTHETIC_OPPORTUNITIES',:event,:hash,:source,:buyer,'3131307','papel',1,'Papel A4 · registro fictício novo','resma',10,5,50,'homologado','2025-12-20',:event,CAST(:metadata AS jsonb))"""),{'id':str(uuid4()),'org':identity['org_id'],'event':event,'hash':event,'source':source,'buyer':buyer,'metadata':metadata})
    engine.dispose();refreshed=c.post('/api/v1/opportunity-alerts/refresh');assert refreshed.status_code==200 and refreshed.json()['future_purchase_promised'] is False
    alerts=c.get('/api/v1/opportunity-alerts').json()['alerts'];assert any(a['event_identity']==event and a['kind']=='new_record' for a in alerts)

def test_429_checkpoint_and_pause(app,settings,login):
    c=login();cid=collection(c);transport,calls=fixture_transport(True);org=c.get('/api/v1/auth/context').json()
    result=history.advance(app.state.database,org['org_id'],org['actor_id'],cid,1,transport)
    assert result['paused'];r=c.get('/api/v1/history-collections/'+cid).json();assert r['pages']==0 and r['error_code']=='RATE_LIMIT'
    assert c.post('/api/v1/history-collections/'+cid+'/resume').status_code==429
    engine=create_engine(settings.owner_database_url.get_secret_value())
    with engine.begin() as db:
        db.execute(text("UPDATE history_collection SET resume_after=now()-interval '1 second' WHERE id=:i"),{'i':cid})
        db.execute(text("UPDATE source_backoff SET resume_after=now()-interval '1 second' WHERE org_id=:o"),{'o':org['org_id']})
    engine.dispose();assert c.post('/api/v1/history-collections/'+cid+'/resume').status_code==200
    history.advance(app.state.database,org['org_id'],org['actor_id'],cid,1,transport)
    assert c.get('/api/v1/history-collections/'+cid).json()['pages']==1

def test_redaction_preserves_no_natural_person_identity():
    r={'tipoPessoa':'PF','niFornecedor':'12345678901','nomeRazaoSocialFornecedor':'Pessoa de teste'}
    safe=history_sources.redacted_source(r);assert safe['niFornecedor'] is None and safe['nomeRazaoSocialFornecedor'] is None
    assert history_sources.public_supplier(r)['cnpj'] is None

def test_source_scope_validation(login):
    c=login()
    assert c.post('/api/v1/history-collections',json={'municipalities':['3131307'],'start':'2025-01-01','end':'2025-01-10','contracts':True}).status_code==422
    assert c.post('/api/v1/history-collections',json={'municipalities':['3131307'],'start':'2025-01-01','end':'2025-01-10','contracts':True,'organization_cnpjs':['0000000000000X']}).status_code==422
    assert c.post('/api/v1/history-collections',json={'municipalities':['3131307'],'start':'2025-02-01','end':'2025-01-01'}).status_code==422
