import hashlib,json
import pytest

def test_capture_preserves_actual_url_and_rejects_other_purchase():
    from app.licinexus import Capture
    raw=b'[]';url='https://pncp.gov.br/api/pncp/v1/orgaos/19876424000142/compras/2025/164/itens'
    capture=Capture([{'url':url,'status':200,'body':'[]','sha256':hashlib.sha256(raw).hexdigest()}])
    actual=capture.read('PNCP_ITENS',url,{'pagina':1,'tamanhoPagina':20})
    assert actual[0]==url and actual[2]==raw
    with pytest.raises(ValueError):capture.read('PNCP_ITENS',url.replace('/164/','/165/'),{})
    with pytest.raises(ValueError):Capture([{'url':url,'status':200,'body':'[]','sha256':'0'*64}]).read('PNCP_ITENS',url,{})
    with pytest.raises(ValueError):capture.read('PNCP_ITENS',url,{'pagina':2})

def test_no_empty_success_from_404_or_secondary_capture():
    from app.licinexus import Capture
    for url,status in [('https://pncp.gov.br/test',404),('https://brasilapi.com.br/test',200)]:
        c=Capture([{'url':url,'status':status,'body':'[]','sha256':hashlib.sha256(b'[]').hexdigest()}])
        with pytest.raises(ValueError):c.read('PNCP_ITENS',url,{})

def test_queue_requires_official_tenant_fact_and_does_not_run_network(login):
    c=login()
    assert c.post('/api/v1/portfolio/licinexus',json={'fact_id':'00000000-0000-0000-0000-000000000001','group':'17','operation':'items'}).status_code==404
    assert login('consulta-a').post('/api/v1/portfolio/licinexus',json={'fact_id':'00000000-0000-0000-0000-000000000001','group':'17','operation':'items'}).status_code==403
    assert c.get('/api/v1/portfolio/licinexus').status_code==200
    assert login('compras-b').get('/api/v1/portfolio/licinexus').json()['jobs']==[]

def test_runtime_rejects_unknown_tools_before_launch():
    from app.licinexus_runtime import invoke
    with pytest.raises(ValueError):invoke('shell_exec',{'url':'https://example.com'})

def test_same_official_purchase_queued_via_parent_or_item_is_one_job(app,login):
    from app import history,licinexus,sources
    from app.monitoring import register,reconcile
    from test_monitoring import fixture
    from test_opportunities import collection,fixture_transport
    c=login();identity=c.get('/api/v1/auth/context').json();org,actor=identity['org_id'],identity['actor_id']
    assert app.state.settings.auth_mode=='local_test'
    cid=collection(c);transport,_=fixture_transport()
    for _ in range(5):history.advance(app.state.database,org,actor,cid,1,transport)
    with app.state.database.transaction(org,actor) as db:
        ctx=sources.job_context(db,org,actor)
        sid=sources.observe(ctx,'IBGE','https://servicodados.ibge.gov.br/api/v1/localidades/estados/QA/municipios',200,b'[]',{'fixture_only':True})
        register(ctx,reconcile(*fixture()),{'MG':sid,'RJ':sid},'a'*64)
        db.execute("UPDATE job SET state='failed' WHERE org_id=:o AND kind='licinexus.query' AND state IN ('queued','running')",{'o':org})
        parent=db.one("SELECT id FROM procurement_fact WHERE org_id=:o AND provider='PNCP' AND obligation_id='00000000000001-1-000001/2025' AND is_current",{'o':org})
        item=db.one("SELECT id FROM procurement_fact WHERE org_id=:o AND provider='PNCP_ITENS' AND obligation_id='00000000000001-1-000001/2025' AND is_current",{'o':org})
        first=licinexus.enqueue(ctx,str(parent['id']),'17','items');second=licinexus.enqueue(ctx,str(item['id']),'13','items')
        assert first['id']==second['id'] and second['duplicate']
        db.execute("UPDATE job SET state='queued' WHERE org_id=:o AND id=:i",{'o':org,'i':first['id']})
    sources.run_job(app.state.database,org,actor,str(first['id']))
    with app.state.database.transaction(org,actor) as db:
        row=db.one('SELECT state FROM job WHERE org_id=:o AND id=:i',{'o':org,'i':first['id']})
        assert row['state']=='queued'
        # Only this isolated fixture is retired after verifying dispatch protection.
        db.execute("UPDATE job SET state='failed' WHERE org_id=:o AND id=:i",{'o':org,'i':first['id']})

def test_official_capture_import_is_idempotent_and_keeps_original_source(app,login):
    from app import history,licinexus,sources
    from test_opportunities import collection,fixture_transport
    c=login();identity=c.get('/api/v1/auth/context').json();org,actor=identity['org_id'],identity['actor_id']
    cid=collection(c);transport,_=fixture_transport()
    for _ in range(5):history.advance(app.state.database,org,actor,cid,1,transport)
    with app.state.database.transaction(org,actor) as db:
        ctx=sources.job_context(db,org,actor)
        parent=db.one("SELECT id FROM procurement_fact WHERE org_id=:o AND provider='PNCP' AND obligation_id='00000000000001-1-000001/2025' AND is_current",{'o':org})
        item={'numeroItem':1,'descricao':'Papel A4 oficial controlado no teste','unidadeMedida':'caixa','quantidade':10,'valorUnitarioEstimado':2,'valorTotal':20,'materialOuServicoNome':'Material','temResultado':True}
        raw=json.dumps([item]);url='https://pncp.gov.br/api/pncp/v1/orgaos/00000000000001/compras/2025/1/itens'
        def invoke(tool,args):
            assert tool=='list_licitacao_itens'
            return {'result':{'content':[]}},[{'url':url,'status':200,'body':raw,'sha256':hashlib.sha256(raw.encode()).hexdigest()}]
        args={'fact_id':str(parent['id']),'operation':'items'}
        first=licinexus.perform(ctx,args,invoke);second=licinexus.perform(ctx,args,invoke)
        assert second['new_revisions']==0 and first['records']==second['records']==1
        row=db.one("SELECT count(*) n FROM procurement_fact WHERE org_id=:o AND provider='PNCP_ITENS' AND event_identity='00000000000001-1-000001/2025:item:1' AND is_current",{'o':org})
        assert row['n']==1
        assert second['documents'][0]['url']==url and second['expected_pages'] is None

def test_retry_backoff_and_expired_lease_resume_are_bounded(app,login):
    from app import licinexus,sources
    from app.db import encoded,identifier
    c=login();identity=c.get('/api/v1/auth/context').json();org,actor=identity['org_id'],identity['actor_id'];jid=identifier()
    assert app.state.settings.auth_mode=='local_test'
    with app.state.database.transaction(org,actor) as db:
        parent=db.one("SELECT id FROM procurement_fact WHERE org_id=:o AND provider='PNCP' AND is_current LIMIT 1",{'o':org})
        assert parent
        db.execute("UPDATE job SET state='failed' WHERE org_id=:o AND kind='licinexus.query'",{'o':org})
        db.execute("UPDATE source_backoff SET resume_after=now()-interval '1 minute' WHERE org_id=:o",{'o':org})
        db.execute("INSERT INTO job(org_id,id,actor_id,kind,idempotency_key,input_hash,arguments,state,result) VALUES (:o,:i,:a,'licinexus.query',:k,:k,CAST(:p AS jsonb),'running',jsonb_build_object('lease_until',now()-interval '1 minute','attempts',1))",{'o':org,'i':jid,'k':str(jid),'a':actor,'p':encoded({'fact_id':str(parent['id']),'operation':'items'})})
    def unavailable(*args):raise sources.SourceFault('RATE_LIMIT',429,300)
    assert licinexus.tick(app.state.database,org,actor,unavailable)['state']=='failed'
    with app.state.database.transaction(org,actor) as db:
        row=db.one('SELECT state,result,error_code FROM job WHERE org_id=:o AND id=:i',{'o':org,'i':jid})
        assert row['state']=='retry_wait' and row['result']['attempts']==2
        assert row['error_code']=='RATE_LIMIT'
        assert db.one("SELECT 1 FROM source_backoff WHERE org_id=:o AND provider='PNCP_HOST' AND resume_after>now()",{'o':org})
        db.execute("UPDATE source_backoff SET resume_after=now()-interval '1 minute' WHERE org_id=:o",{'o':org})
        db.execute("UPDATE job SET result=jsonb_set(result,'{retry_at}',to_jsonb(now()-interval '1 minute')) WHERE org_id=:o AND id=:i",{'o':org,'i':jid})
    licinexus.tick(app.state.database,org,actor,unavailable)
    with app.state.database.transaction(org,actor) as db:
        row=db.one('SELECT state,result FROM job WHERE org_id=:o AND id=:i',{'o':org,'i':jid})
        assert row['state']=='failed' and row['result']['attempts']==3
        db.execute("UPDATE source_backoff SET resume_after=now()-interval '1 minute' WHERE org_id=:o",{'o':org})
