"""Source identity contract. Synthetic network responses exist only in isolated QA."""
from uuid import uuid4
import httpx
from app import sources,catalogue

def test_unit_prefix_is_not_package_conversion():
    assert catalogue.unit_key('1,00 UNIDADE')=='UNIDADE'
    assert catalogue.unit_key('1.00 UNIDADE')=='UNIDADE'
    assert catalogue.unit_key('10 UNIDADES')=='10'
    assert catalogue.pack('caixa com 10 resmas')=='CAIXA:10:RESMA'

def test_identity_exact_singleton_and_authorization(app,login):
    client=login();identity=client.get('/api/v1/auth/context').json()
    cnpj=str(int(uuid4().hex[:12],16) % (10**14)).zfill(14)
    obligation=f'{cnpj}-1-1/2026'
    header={'orgaoEntidade':{'cnpj':cnpj,'razaoSocial':'Órgão apenas para QA'},
        'unidadeOrgao':{'codigoIbge':'3131307','codigoUnidade':'QA'},'anoCompra':2026,'sequencialCompra':1,
        'numeroControlePNCP':obligation,'dataPublicacaoPncp':'2026-10-20','objetoCompra':'Pia de louça para QA','modalidadeId':6}
    def transport(request):
        if request.url.path.endswith('/itens'):
            return httpx.Response(200,json=[{'numeroItem':1,'descricao':'Pia de louça branca para teste isolado','unidadeMedida':'1,00 UNIDADE','quantidade':3,'valorUnitarioEstimado':10,'valorTotal':30}])
        return httpx.Response(200,json={'data':[header],'totalPaginas':1})
    with app.state.database.transaction(identity['org_id'],identity['actor_id']) as db:
        ctx=sources.job_context(db,identity['org_id'],identity['actor_id'])
        sources.sync(ctx,{'provider':'PNCP','municipality_ibge':'3131307','modality':6,'start_date':'2026-10-20','end_date':'2026-10-20','page':1,'size':10},httpx.MockTransport(transport))
        parent=db.one('SELECT id FROM procurement_fact WHERE event_identity=:e',{'e':obligation+':publication'})
        sources.sync(ctx,{'provider':'PNCP_ITENS','procurement_id':str(parent['id']),'page':1,'size':10},httpx.MockTransport(transport))
        fact=db.one("SELECT id,item_id,item_version FROM procurement_fact WHERE provider='PNCP_ITENS' AND obligation_id=:ob",{'ob':obligation})
    url='/api/v1/director/observed-items/'+str(fact['id'])+'/identity'
    created=client.post(url);assert created.status_code==200,created.text
    assert created.json()['identity_only'] and not created.json()['cross_item_equivalence_reviewed']
    again=client.post(url);assert again.json()['id']==created.json()['id'] and not again.json()['created']
    assert login('consulta-a').post(url).status_code==403
    assert client.post('/api/v1/director/observed-items/'+str(uuid4())+'/identity').status_code==404
    history=client.get('/api/v1/director/history/'+created.json()['id'],params={'phase':'publicado_estimado','start':'2026-10-20','end':'2026-10-20','municipalities':['3131307','3101607']})
    assert history.status_code==200,history.text
    assert history.json()['summary']['observed_quantity']=='3.00000000'
    assert history.json()['summary']['unit']=='UNIDADE'
    missing=next(r for r in history.json()['municipalities'] if r['municipality']['ibge']=='3101607')
    assert missing['observed_quantity'] is None
    with app.state.database.transaction(identity['org_id']) as db:
        p=db.one('SELECT members FROM canonical_product WHERE id=:i',{'i':created.json()['id']})
        assert p['members']==[{'id':fact['item_id'],'version':fact['item_version']}]
