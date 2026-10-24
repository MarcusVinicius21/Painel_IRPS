import hashlib,json
from uuid import uuid4
from test_portfolio_api import prepared
from app.db import encoded
from app.portfolio_history import source_groups


def test_text_triage_is_only_a_candidate_and_keeps_negatives_out():
    assert source_groups({'description':'CAFÉ TORRADO E MOÍDO 500 G'},{'materialOuServico':'M'})==['15']
    assert '07' not in source_groups({'description':'CHAVE CATRACA 1/2'},{'materialOuServico':'M'})
    assert source_groups({'description':'CAFÉ TORRADO E MOÍDO'},None)==[]
    assert source_groups({'description':'CONECTOR RJ45 BRONZE FÓSFORO'},{'materialOuServico':'M'})==['17']
    assert '13' not in source_groups({'description':'SERINGA USO VETERINÁRIO'},{'materialOuServico':'M'})


def test_local_parent_lineage_supplier_and_candidate_filters(prepared,app,login):
    c,_=prepared;identity=c.get('/api/v1/auth/context').json();org=identity['org_id'];actor=identity['actor_id']
    prefix='qa-fcp-'+uuid4().hex;sid=str(uuid4());rid=str(uuid4());bid=str(uuid4());item=prefix;parent=str(uuid4());result=str(uuid4())
    name='CAFÉ TORRADO E MOÍDO 500 G';unit='PACOTE';body=encoded([{'numeroItem':1,'descricao':name,'unidadeMedida':unit,'materialOuServico':'M'}])
    with app.state.database.transaction(org,actor) as db:
        for source,text in [(sid,body),(rid,encoded([{'fixture_only':True,'tipoPessoa':'PJ','niFornecedor':'00000000000001'}]))]:
            db.execute('''INSERT INTO source_observation(id,org_id,provider,url,http_status,sha256,body,metadata,classification)
                VALUES (:i,:o,'QA_FCP',:url,200,:h,:b,CAST(:m AS jsonb),'official')''',
                {'i':source,'o':org,'url':'https://example.invalid/isolated-qa-fcp/'+prefix,'h':hashlib.sha256(text.encode()).hexdigest(),'b':text,'m':encoded({'fixture_only':True})})
        db.execute('''INSERT INTO buyer(id,org_id,cnpj,name,municipality_ibge,government_level,classification,external_identity)
            VALUES (:i,:o,'00000000000001','Isolated QA buyer','3131307','M','official',:e)''',{'i':bid,'o':org,'e':prefix})
        db.execute("INSERT INTO item_version(id,version,name,family,unit,step,classification) VALUES (:i,1,:n,'QA',:u,1,'synthetic')",{'i':item,'n':name,'u':unit})
        for fid,provider,phase,source,meta in [(parent,'PNCP_ITENS','publicado_estimado',sid,{'purchase':{'number':1}}),
                (result,'PNCP_RESULTADOS','homologado',rid,{'parent_id':parent,'supplier':{'cnpj':'00000000000001','name':'QA supplier'}})]:
            db.execute('''INSERT INTO procurement_fact(id,org_id,classification,provider,event_identity,revision_hash,source_id,buyer_id,
                municipality_ibge,item_id,item_version,description,unit,quantity,unit_price,amount,phase,event_date,obligation_id,metadata)
                VALUES (:i,:o,'official',:p,:e,:h,:s,:b,'3131307',:item,1,:n,:u,10,5,50,:phase,'2026-09-01',:ob,CAST(:m AS jsonb))''',
                {'i':fid,'o':org,'p':provider,'e':prefix+provider,'h':prefix,'s':source,'b':bid,'item':item,'n':name,'u':unit,
                    'phase':phase,'ob':'00000000000001-1-1/2026','m':encoded(meta)})
    p={'group':'15','start':'2026-09-01','end':'2026-09-30','phase':'homologado','municipalities':['3131307']}
    response=c.get('/api/v1/portfolio/history',params=p);assert response.status_code==200,response.text
    row=next(r for r in response.json()['records'] if r['id']==result)
    assert row['group_match_state']=='description_candidate_requires_review'
    assert row['group_evidence_source_id']==sid and row['source_id']==rid
    assert row['supplier']['cnpj']=='00000000000001' and row['supplier_role']=='adjudicatário'
    assert not row['included_in_group_totals'] and not row['quantity_is_consumption']
    assert response.json()['comparative_quantity'] is None
    assert c.get('/api/v1/portfolio/history',params={**p,'candidates':False}).json()['total']==0
    assert login('compras-b').get('/api/v1/portfolio/history',params=p).json()['records']==[]
    assert c.get('/api/v1/portfolio/history',params={**p,'municipalities':['9999999']}).status_code==422
