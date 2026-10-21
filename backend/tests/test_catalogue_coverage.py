"""Catalogues and coverage cannot silently turn partial public evidence into facts."""
from datetime import date,timedelta
from uuid import uuid4

import pytest
import httpx

from app import catalogue, history, opportunity_demo
from app.db import encoded
from app.opportunity_schemas import HistoricalScope


@pytest.fixture
def prepared(settings):
    opportunity_demo.seed_demo(settings)


def test_normalization_preserves_original_and_package_conflicts():
    base={'description':'Papel A4, CAIXA com 10 resmas','unit':'cx de 10 resmas',
          'metadata':{},'provider':'PNCP_ITENS'}
    normalized=catalogue.normalized_fact(base)
    assert normalized['original_description']==base['description']
    assert normalized['package_signature']=='CAIXA:10:RESMA'
    assert normalized['confidence']=='text_unit'
    assert catalogue.normalized_fact({**base,'unit':'caixa com 20 resmas'})['confidence']=='incomplete'
    assert 'package_conflict' in catalogue.normalized_fact({**base,'unit':'caixa com 20 resmas'})['issues']
    assert catalogue.normalized_fact({**base,'unit':'unidade'})['confidence']=='incomplete'
    assert catalogue.pack('embalagem com 12 pares')=='EMBALAGEM:12:PAR'
    assert catalogue.fold('Álcool etílico 70%')=='ALCOOL ETILICO 70'
    assert catalogue.token_key('Papel A4 para escritório')==catalogue.token_key('Escritório: papel A4')
    assert catalogue.token_key('Papel A4 75 g')!=catalogue.token_key('Papel A4 90 g')
    assert catalogue.reliable_obligation({'classification':'official','provider':'PNCP_ITENS','obligation_id':'00000000000001-1-42/2025'})
    assert catalogue.reliable_obligation({'classification':'official','provider':'PNCP_ITENS','obligation_id':'local-42'}) is None


def test_reprocess_is_idempotent_and_private(prepared,login):
    a=login('compras-a');b=login('compras-b')
    url='/api/v1/catalogue-intelligent/reprocess?limit=500'
    first=a.post(url);assert first.status_code==200,first.text
    assert first.json()['scanned']>0
    second=a.post(url);assert second.status_code==200 and second.json()['inserted']==0
    other=b.post(url);assert other.status_code==200 and other.json()['scanned']>0
    assert a.get('/api/v1/catalogue-intelligent/candidates').status_code==200
    assert login('consulta-a').post(url).status_code==403


def test_reviewed_product_rejects_unit_mismatch_and_overlap(prepared,login,app):
    c=login();org=c.get('/api/v1/auth/context').json()['org_id']
    # Three new facts: two matching packages and one incompatible unit.
    from sqlalchemy import create_engine
    from app.config import load_settings
    from app.db import DB
    engine=create_engine(load_settings().owner_database_url.get_secret_value(),hide_parameters=True)
    items=['catalogue-test-'+uuid4().hex for _ in range(3)]
    with engine.begin() as conn:
        db=DB(conn);db.execute("SELECT set_config('irps.org_id',:o,true)",{'o':org})
        original=db.one("SELECT * FROM procurement_fact WHERE org_id=:o AND item_id='papel' AND provider='SYNTHETIC_OPPORTUNITIES' LIMIT 1",{'o':org})
        for index,item in enumerate(items):
            unit='unidade' if index==2 else 'caixa de 10 resmas'
            db.execute("INSERT INTO item_version(id,version,name,family,unit,step,classification) VALUES (:i,1,'Papel A4 de teste','Material',:u,1,'synthetic')",{'i':item,'u':unit})
            event='catalogue:'+item
            db.execute("""INSERT INTO procurement_fact(id,org_id,classification,provider,event_identity,revision_hash,source_id,buyer_id,
                municipality_ibge,item_id,item_version,description,unit,quantity,amount,phase,event_date,obligation_id,metadata)
                VALUES (:id,:o,'synthetic','SYNTHETIC_OPPORTUNITIES',:event,:event,:source,:buyer,:city,:item,1,
                'Papel A4 de teste · caixa com 10 resmas',:unit,5,50,'homologado',:day,:event,'{}')""",
                {'id':str(uuid4()),'o':org,'event':event,'source':original['source_id'],'buyer':original['buyer_id'],
                 'city':original['municipality_ibge'],'item':item,'unit':unit,'day':date(2025,1,20)})
    engine.dispose()
    offset=0
    while True:
        page=c.post(f'/api/v1/catalogue-intelligent/reprocess?limit=500&offset={offset}')
        assert page.status_code==200,page.text
        if page.json()['next_offset'] is None:break
        offset=page.json()['next_offset']
    base={'name':'Papel A4 revisado','category':'Materiais',
          'justification':'Teste de revisão humana da equivalência técnica.','evidence':'Registro sintético local de teste.',
          'confirmed':True}
    incompatible={**base,'members':[{'id':items[0],'version':1},{'id':items[2],'version':1}]}
    rejected=c.post('/api/v1/catalogue-intelligent/products',json=incompatible)
    assert rejected.status_code==422,rejected.text
    good={**base,'members':[{'id':items[0],'version':1},{'id':items[1],'version':1}]}
    created=c.post('/api/v1/catalogue-intelligent/products',json=good)
    assert created.status_code==201,created.text
    assert c.post('/api/v1/catalogue-intelligent/products',json=good).status_code==409
    view=c.get('/api/v1/catalogue-intelligent/products?phase=homologado&start=2025-01-01&end=2025-12-31')
    assert view.status_code==200,view.text
    record=next(x for x in view.json()['records'] if x['id']==created.json()['id'])
    assert record['observed_records']>0 and record['quantity_complete']
    assert record['known_amount'] is not None and record['sources']
    assert record['notice'].startswith('Quantidade observada')
    successor=c.post('/api/v1/catalogue-intelligent/products',json={**good,
        'name':'Papel A4 revisado novamente','supersedes_id':created.json()['id']})
    assert successor.status_code==201,successor.text
    active=c.get('/api/v1/catalogue-intelligent/products').json()['records']
    assert any(row['id']==successor.json()['id'] for row in active)
    assert all(row['id']!=created.json()['id'] for row in active)
    with app.state.database.transaction(org,c.get('/api/v1/auth/context').json()['actor_id']) as db:
        assert db.one('SELECT id FROM canonical_product WHERE id=:i',{'i':created.json()['id']})
    assert login('compras-b').get('/api/v1/catalogue-intelligent/products').json()['total']==0


def test_inventory_no_false_denominator_and_page_reconciliation(app,login):
    c=login();seed=int(uuid4().hex[:8],16)
    start=date(2021,1,1)+timedelta(days=seed%1500);end=start+timedelta(days=6)
    modality=9+(seed%6)
    url=f'/api/v1/coverage/inventory?start={start}&end={end}&municipalities=3131307'
    empty=c.get(url);assert empty.status_code==200,empty.text
    row=next(x for x in empty.json()['records'] if x['provider']=='PNCP')
    assert row['source_completeness_ratio'] is None
    assert row['request_completion_ratio'] is None or 0<=float(row['request_completion_ratio'])<=1
    from test_opportunities import fixture_transport
    scope={'municipalities':['3131307'],'start':str(start),'end':str(end),
           'modalities':[modality],'max_pages':12}
    created=c.post('/api/v1/history-collections',json=scope)
    assert created.status_code==201,created.text
    identity=c.get('/api/v1/auth/context').json();transport,_=fixture_transport()
    history.advance(app.state.database,identity['org_id'],identity['actor_id'],created.json()['id'],1,transport)
    partial=c.get(url).json();publication=next(x for x in partial['records'] if x['provider']=='PNCP' and x['modality']==modality)
    assert publication['planned_days']==7 and publication['reconciled_days']==0
    assert publication['request_completion_ratio']=='0' and publication['source_completeness_ratio'] is None
    for _ in range(5):history.advance(app.state.database,identity['org_id'],identity['actor_id'],created.json()['id'],1,transport)
    reconciled=c.get(url).json();publication=next(x for x in reconciled['records'] if x['provider']=='PNCP' and x['modality']==modality)
    assert publication['reconciled_days']==7 and publication['request_completion_ratio']=='1'
    assert publication['source_completeness_ratio'] is None and publication['proof'][0]['sha256']
    result=next(x for x in reconciled['records'] if x['provider']=='PNCP_RESULTADOS')
    assert result['phase']=='homologado' and result['request_completion_ratio'] is None
    assert not reconciled['official_phase_completeness_claimed']


def test_scope_requires_documented_constraints():
    with pytest.raises(ValueError):HistoricalScope(municipalities=['3131307'],start=date(2025,1,1),end=date(2025,1,7),contracts=True)
    with pytest.raises(ValueError):HistoricalScope(municipalities=['3131307'],start=date(2025,1,1),end=date(2025,1,7),
        publications=False,updates=False,contracts=False,contract_updates=False,atas=False,pca=False)


def test_compras_reference_price_preserves_scope_without_personal_data(app,login):
    c=login();identity=c.get('/api/v1/auth/context').json()
    transport=httpx.MockTransport(lambda request:httpx.Response(200,json={'resultado':[
        {'idCompra':'compra-1','numeroItemCompra':2,'codigoItemCatalogo':206504,
         'descricaoItem':'Cadeira de escritório','quantidade':2,'precoUnitario':100,
         'nomeUnidadeFornecimento':'Unidade','dataCompra':'2025-09-01','dataResultado':'2025-09-02',
         'codigoUasg':'123','nomeOrgao':'Órgão público','codigoMunicipio':3131307,'estado':'MG',
         'niFornecedor':'12345678901','nomeFornecedor':'Pessoa natural'}],
         'totalRegistros':1,'totalPaginas':1}))
    from app import sources
    with app.state.database.transaction(identity['org_id'],identity['actor_id']) as db:
        ctx=sources.job_context(db,identity['org_id'],identity['actor_id'])
        result=catalogue.reference_prices(ctx,'material','206504','codigoItemCatalogo',
            date(2025,9,1),date(2025,9,30),1,transport)
        assert result['records'][0]['unit_price']=='100'
        assert result['records'][0]['supplier_cnpj'] is None
        assert result['municipal_coverage_claimed'] is False
        stored=db.one('SELECT body FROM source_observation WHERE provider=:p AND url=:url',
            {'p':'COMPRAS_PRECOS_MATERIAL','url':result['url']})
        assert 'Pessoa natural' not in stored['body'] and '12345678901' not in stored['body']
        assert result['original_response_sha256']!=result['stored_sha256']
        no_content=catalogue.reference_prices(ctx,'material','206504','codigoItemCatalogo',
            date(2025,9,1),date(2025,9,30),1,
            httpx.MockTransport(lambda request:httpx.Response(204)))
        assert no_content['records']==[] and no_content['municipal_coverage_claimed'] is False
        cache_url='https://example.invalid/cache-204/'+uuid4().hex
        sources.observe(ctx,'TEST_EMPTY',cache_url,204,b'',{'test_only':True})
        assert sources.cached_get(ctx,'TEST_EMPTY',cache_url)[3] is None
    assert c.get('/api/v1/catalogue-intelligent/reference-prices?kind=material&code=abc').status_code==422


def test_official_update_ata_and_pca_are_observed_not_purchases(app,login):
    c=login();identity=c.get('/api/v1/auth/context').json();sequence=int(uuid4().hex[:6],16)
    scope={'municipalities':['3131307'],'start':'2025-03-01','end':'2025-03-07',
        'modalities':[6],'publications':False,'updates':True,'items':False,'results':False,
        'atas':True,'pca':True,'max_pages':12}
    created=c.post('/api/v1/history-collections',json=scope)
    assert created.status_code==201,created.text
    def response(request):
        path=request.url.path
        if path.endswith('/contratacoes/atualizacao'):
            return httpx.Response(200,json={'data':[{'numeroControlePNCP':f'00000000000001-1-{sequence}/2025',
                'orgaoEntidade':{'cnpj':'00000000000001','razaoSocial':'Órgão fictício','esferaId':'M'},
                'unidadeOrgao':{'codigoUnidade':'1','codigoIbge':'3131307'},'anoCompra':2025,
                'sequencialCompra':sequence,'objetoCompra':'Teste de atualização pública',
                'dataPublicacaoPncp':'2025-03-02T12:00:00','modalidadeId':6}],'totalPaginas':1})
        if path.endswith('/atas'):return httpx.Response(200,json={'data':[{'numeroAtaRegistroPreco':'ata-sintetica'}],
            'totalPaginas':1,'totalRegistros':1})
        if path.endswith('/consolidado'):return httpx.Response(200,json={'anoPca':2025,'itens':[]})
        if path.endswith('/atas/atualizacao') or path.endswith('/pca/atualizacao'):
            return httpx.Response(200,json={'data':[],'totalPaginas':0})
        return httpx.Response(404)
    transport=httpx.MockTransport(response)
    cid=created.json()['id']
    for _ in range(8):
        if not history.advance(app.state.database,identity['org_id'],identity['actor_id'],cid,1,transport)['pages']:break
    state=c.get('/api/v1/history-collections/'+cid).json()
    assert state['state']=='completed',state
    with app.state.database.transaction(identity['org_id'],identity['actor_id']) as db:
        pages=db.all("""SELECT t.provider,p.record_count,p.result FROM history_task t
            JOIN history_page p ON p.task_id=t.id WHERE t.collection_id=:c""",{'c':cid})
        assert {'PNCP_ATUALIZACAO','PNCP_ATAS','PNCP_PCA','PNCP_ATAS_ATUALIZACAO','PNCP_PCA_ATUALIZACAO'}<={x['provider'] for x in pages}
        assert all(x['result'].get('purchase_inferred') is False for x in pages if x['provider'] in ('PNCP_ATAS','PNCP_PCA'))


def test_missing_optional_plan_does_not_claim_absence_or_block_other_pages(app,login):
    c=login();identity=c.get('/api/v1/auth/context').json()
    from app import history_sources,sources
    with app.state.database.transaction(identity['org_id'],identity['actor_id']) as db:
        ctx=sources.job_context(db,identity['org_id'],identity['actor_id'])
        result=history_sources.pca(ctx,{'cnpj':'00000000000001','year':2024},
            httpx.MockTransport(lambda request:httpx.Response(404,json={'message':'not found'})))
        assert result['state']=='not_found_unclassified' and result['absence_proven'] is False
        observed=db.one('SELECT http_status,metadata FROM source_observation WHERE id=:i',{'i':result['source_id']})
        assert observed['http_status']==404 and observed['metadata']['absence_of_plan_or_ata_not_proven']


def test_empty_publication_response_keeps_checkpoint_without_inventing_records(app,login):
    c=login();identity=c.get('/api/v1/auth/context').json()
    created=c.post('/api/v1/history-collections',json={'municipalities':['3131307'],
        'start':'2021-03-01','end':'2021-03-07','modalities':[14],'max_pages':2})
    assert created.status_code==201,created.text
    cid=created.json()['id']
    transport=httpx.MockTransport(lambda request:httpx.Response(204))
    result=history.advance(app.state.database,identity['org_id'],identity['actor_id'],cid,1,transport)
    assert result['pages']==1
    state=c.get('/api/v1/history-collections/'+cid).json()
    assert state['state']=='completed' and state['records']==0


def test_product_history_filters_cities_revisions_units_and_tenants(app,login,prepared):
    from sqlalchemy import create_engine
    from app.config import load_settings
    from app.db import DB
    client=login('compras-a');identity=client.get('/api/v1/auth/context').json()
    engine=create_engine(load_settings().owner_database_url.get_secret_value(),hide_parameters=True)
    item='history-'+uuid4().hex;item2='history-'+uuid4().hex;prefix=uuid4().hex
    with engine.begin() as conn:
        db=DB(conn);db.execute("SELECT set_config('irps.org_id',:o,true)",{'o':identity['org_id']})
        cities=db.all('SELECT ibge FROM municipality ORDER BY ibge LIMIT 4')
        assert len(cities)==4
        codes=[r['ibge'] for r in cities]
        original=db.one("SELECT * FROM procurement_fact WHERE org_id=:o AND item_id='papel' AND provider='SYNTHETIC_OPPORTUNITIES' LIMIT 1",{'o':identity['org_id']})
        db.execute("INSERT INTO item_version(id,version,name,family,unit,step,classification) VALUES (:i,1,'Material histórico de teste','Material','caixa de 10 resmas',1,'synthetic')",{'i':item})
        db.execute("INSERT INTO item_version(id,version,name,family,unit,step,classification) VALUES (:i,1,'Material histórico de teste','Material','caixa de 10 resmas',1,'synthetic')",{'i':item2})
        def fact(city,event,quantity,unit='caixa de 10 resmas',current=True,phase='homologado',day='2025-02-01'):
            db.execute("""INSERT INTO procurement_fact(id,org_id,classification,provider,event_identity,revision_hash,
                source_id,buyer_id,municipality_ibge,item_id,item_version,description,unit,quantity,amount,unit_price,
                phase,event_date,obligation_id,metadata,is_current)
                VALUES (:id,:o,'synthetic','SYNTHETIC_OPPORTUNITIES',:event,:revision,:source,:buyer,:city,
                :item,1,'Papel A4 caixa com 10 resmas',:unit,:qty,:amount,10,:phase,:day,:obligation,'{}',:current)""",
                {'id':str(uuid4()),'o':identity['org_id'],'event':event,'revision':uuid4().hex,
                 'source':original['source_id'],'buyer':original['buyer_id'],'city':city,'item':item,
                 'unit':unit,'qty':quantity,'amount':quantity*10,'phase':phase,'day':day,
                 'obligation':'process-'+event.split(':')[0],'current':current})
        fact(codes[0],prefix+'a:1',2)
        db.execute("UPDATE procurement_fact SET is_current=false WHERE provider='SYNTHETIC_OPPORTUNITIES' AND event_identity=:event AND item_id=:item",{'event':prefix+'a:1','item':item})
        fact(codes[0],prefix+'a:1',3)
        fact(codes[0],prefix+'a:2',4)
        fact(codes[3],prefix+'d:1',100)
        db.execute("""INSERT INTO procurement_fact(id,org_id,classification,provider,event_identity,revision_hash,
            source_id,buyer_id,municipality_ibge,item_id,item_version,description,unit,quantity,amount,unit_price,
            phase,event_date,obligation_id,metadata)
            VALUES (:id,:o,'synthetic','SYNTHETIC_OPPORTUNITIES',:event,:revision,:source,:buyer,:city,
            :item,1,'Papel A4 caixa com 10 resmas','caixa de 10 resmas',6,60,10,'homologado','2025-02-01',:event,'{}')""",
            {'id':str(uuid4()),'o':identity['org_id'],'event':'second-'+item2,'revision':uuid4().hex,
             'source':original['source_id'],'buyer':original['buyer_id'],'city':codes[3],'item':item2})
        fact(codes[0],prefix+'a:publication',500,phase='publicado_estimado')
    engine.dispose()
    assert client.post('/api/v1/catalogue-intelligent/reprocess?limit=500').status_code==200
    reviewed=client.post('/api/v1/catalogue-intelligent/products',json={
        'name':'Papel A4 caixa de 10 resmas','category':'Materiais',
        'justification':'Unidade e embalagem conferidas no teste de histórico.',
        'evidence':'Fonte sintética local para regressão.',
        'members':[{'id':item,'version':1},{'id':item2,'version':1}],'confirmed':True})
    assert reviewed.status_code==201,reviewed.text
    pid=reviewed.json()['id']
    engine=create_engine(load_settings().owner_database_url.get_secret_value(),hide_parameters=True)
    with engine.begin() as conn:
        db=DB(conn);db.execute("SELECT set_config('irps.org_id',:o,true)",{'o':identity['org_id']})
        db.execute("""INSERT INTO procurement_fact(id,org_id,classification,provider,event_identity,revision_hash,
            source_id,buyer_id,municipality_ibge,item_id,item_version,description,unit,quantity,amount,unit_price,
            phase,event_date,obligation_id,metadata)
            VALUES (:id,:o,'synthetic','SYNTHETIC_OPPORTUNITIES',:event,:revision,:source,:buyer,:city,
            :item,1,'Papel A4 caixa com 10 resmas','caixa de 20 resmas',5,50,10,'homologado','2025-02-01',:event,'{}')""",
            {'id':str(uuid4()),'o':identity['org_id'],'event':prefix+'b:1','revision':uuid4().hex,
             'source':original['source_id'],'buyer':original['buyer_id'],'city':codes[1],'item':item})
    engine.dispose()
    query='phase=homologado&start=2025-01-01&end=2025-12-31'
    for code in codes[:3]:query+='&municipalities='+code
    result=client.get(f'/api/v1/catalogue-intelligent/products/{pid}/history?{query}')
    assert result.status_code==200,result.text
    by_code={r['municipality']['ibge']:r for r in result.json()['municipalities']}
    assert set(by_code)==set(codes[:3])
    assert by_code[codes[0]]['observed_records']==2
    assert by_code[codes[0]]['distinct_processes']==1
    assert float(by_code[codes[0]]['observed_quantity'])==7
    assert by_code[codes[0]]['recurrence_percentage'] is None
    assert by_code[codes[1]]['observed_records']==1
    assert by_code[codes[1]]['observed_quantity'] is None
    assert by_code[codes[1]]['excluded_from_totals']
    assert by_code[codes[2]]['observed_records']==0
    assert by_code[codes[2]]['observed_quantity'] is None
    assert by_code[codes[2]]['coverage_state']=='demonstration'
    duplicate=client.get(f'/api/v1/catalogue-intelligent/products/{pid}/history?{query}&municipalities={codes[0]}')
    assert duplicate.status_code==200 and len(duplicate.json()['municipalities'])==3
    assert duplicate.json()['scope']['municipalities']==codes[:3]
    assert all(x['evidence'][0]['url'] for x in by_code.values() if x['evidence'])
    summary=client.get('/api/v1/catalogue-intelligent/products?'+query)
    assert summary.status_code==200,summary.text
    row=next(r for r in summary.json()['records'] if r['id']==pid)
    assert row['observed_records']==3 and float(row['observed_quantity'])==7
    assert row['quantity_complete'] is False
    only=client.get('/api/v1/catalogue-intelligent/products?'+query.replace('&municipalities='+codes[1],'').replace('&municipalities='+codes[2],''))
    row=next(r for r in only.json()['records'] if r['id']==pid)
    assert row['observed_records']==2 and float(row['observed_quantity'])==7
    assert login('compras-b').get(f'/api/v1/catalogue-intelligent/products/{pid}/history?{query}').status_code==404
    publication=client.get(f'/api/v1/catalogue-intelligent/products/{pid}/history?'+query.replace('homologado','publicado_estimado')).json()['municipalities']
    assert next(r for r in publication if r['municipality']['ibge']==codes[0])['observed_records']==1
    older=client.get(f'/api/v1/catalogue-intelligent/products/{pid}/history?'+query.replace('2025-01-01','2024-01-01').replace('2025-12-31','2024-12-31')).json()['municipalities']
    assert all(r['observed_records']==0 for r in older)
