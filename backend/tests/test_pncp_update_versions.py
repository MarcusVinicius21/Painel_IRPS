from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
import httpx
from app import sources
from app.municipal_plan import create_update_plan
from app.opportunity_schemas import HistoricalScope


def payload(cnpj, value=100, unit='1', name='Órgão fictício do QA', status='Divulgada no PNCP'):
    return {'numeroControlePNCP': cnpj+'-1-000001/2025','orgaoEntidade': {'cnpj':cnpj,'razaoSocial':name,'esferaId':'M'},
        'unidadeOrgao': {'codigoUnidade':unit,'codigoIbge':'3131307'},'anoCompra':2025,'sequencialCompra':1,
        'objetoCompra':'Registro controlado exclusivamente para QA','dataPublicacaoPncp':'2025-10-03T10:00:00',
        'valorTotalEstimado':value,'modalidadeId':6,'situacaoCompraNome':status}


def run(app, ctx, record, provider='PNCP'):
    transport=httpx.MockTransport(lambda _: httpx.Response(200,json={'data':[record],'totalPaginas':1}))
    with app.state.database.transaction(ctx['org_id'],ctx['actor_id']) as db:
        worker=sources.job_context(db,ctx['org_id'],ctx['actor_id'])
        return sources.sync(worker,{'provider':provider,'municipality_ibge':'3131307','modality':6,
            'start_date':'2025-10-01','end_date':'2025-10-07','page':1,'size':20},transport)


def test_update_revises_same_event_and_preserves_original_date_phase_and_source(app, login):
    c=login();ctx=c.get('/api/v1/auth/context').json();cnpj=str(uuid4().int)[:14]
    first=payload(cnpj)
    run(app,ctx,first)
    changed=payload(cnpj,value=200,unit='2',name='Nome corrigido no QA',status='Anulada')
    changed['dataAtualizacaoGlobal']='2026-01-02T12:00:00'
    run(app,ctx,changed,'PNCP_ATUALIZACAO')
    duplicate=run(app,ctx,changed,'PNCP_ATUALIZACAO')
    assert duplicate['new_revisions']==0
    with app.state.database.transaction(ctx['org_id'],ctx['actor_id']) as db:
        rows=db.all("""SELECT f.*,s.provider AS source_provider,s.body,b.unit_code FROM procurement_fact f
            JOIN source_observation s ON s.id=f.source_id JOIN buyer b ON b.id=f.buyer_id
            WHERE f.org_id=:o AND f.event_identity=:e ORDER BY f.is_current""", {'o':ctx['org_id'],'e':cnpj+'-1-000001/2025:publication'})
    assert len(rows)==2 and sum(r['is_current'] for r in rows)==1
    old,current=rows
    assert current['supersedes_id']==old['id'] and current['amount']==200 and old['amount']==100
    assert old['unit_code']=='1' and current['unit_code']=='2'
    assert current['source_provider']=='PNCP_ATUALIZACAO' and old['source_provider']=='PNCP'
    assert current['metadata']['source_phase']=='Anulada'
    assert all(str(r['event_date'])=='2025-10-03' and r['phase']=='publicado_estimado' and r['quantity'] is None for r in rows)
    assert '2026-01-02' in current['body'] and current['obligation_id']==old['obligation_id']


def test_competing_revisions_leave_one_current_event(app, login):
    c=login();ctx=c.get('/api/v1/auth/context').json();cnpj=str(uuid4().int)[:14]
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(run,app,ctx,payload(cnpj,value=v),'PNCP_ATUALIZACAO') for v in (101,202)]
        for future in futures:assert future.result(timeout=20)['records']==1
    with app.state.database.transaction(ctx['org_id'],ctx['actor_id']) as db:
        row=db.one("SELECT count(*) AS versions,count(*) FILTER(WHERE is_current) AS current FROM procurement_fact WHERE org_id=:o AND event_identity=:e",{'o':ctx['org_id'],'e':cnpj+'-1-000001/2025:publication'})
    assert row=={'versions':2,'current':1}


def test_update_plan_never_reuses_publication_coverage(app,login):
    c=login();ctx=c.get('/api/v1/auth/context').json()
    scope=HistoricalScope(municipalities=['3131307'],start='2025-10-01',end='2025-10-07',
                           modalities=[6],publications=False,updates=True,items=False,results=False)
    with app.state.database.transaction(ctx['org_id'],ctx['actor_id']) as db:
        worker=sources.job_context(db,ctx['org_id'],ctx['actor_id'])
        a=create_update_plan(worker,scope)
    with app.state.database.transaction(ctx['org_id'],ctx['actor_id']) as db:
        worker=sources.job_context(db,ctx['org_id'],ctx['actor_id']);b=create_update_plan(worker,scope)
        rows=db.all('SELECT provider FROM history_task WHERE org_id=:o AND collection_id=:c',{'o':ctx['org_id'],'c':a['id']})
    assert a['id']==b['id'] and b['reused_plan']
    assert rows and all(r['provider']=='PNCP_ATUALIZACAO' for r in rows)


def test_late_older_source_revision_is_preserved_without_replacing_current(app,login):
    c=login();ctx=c.get('/api/v1/auth/context').json();cnpj=str(uuid4().int)[:14]
    current=payload(cnpj,300);current['dataAtualizacaoGlobal']='2026-02-01T10:00:00'
    older=payload(cnpj,200);older['dataAtualizacaoGlobal']='2026-01-01T10:00:00'
    run(app,ctx,current,'PNCP_ATUALIZACAO');run(app,ctx,older)
    with app.state.database.transaction(ctx['org_id'],ctx['actor_id']) as db:
        rows=db.all("SELECT is_current,amount,metadata FROM procurement_fact WHERE org_id=:o AND event_identity=:e ORDER BY amount",{'o':ctx['org_id'],'e':cnpj+'-1-000001/2025:publication'})
    assert len(rows)==2
    assert rows[0]['amount']==200 and rows[0]['is_current'] is False and rows[0]['metadata']['late_revision'] is True
    assert rows[1]['amount']==300 and rows[1]['is_current'] is True


def test_missing_source_timestamp_does_not_become_verified_order(app,login):
    c=login();ctx=c.get('/api/v1/auth/context').json();cnpj=str(uuid4().int)[:14]
    run(app,ctx,payload(cnpj,100))
    run(app,ctx,payload(cnpj,200),'PNCP_ATUALIZACAO')
    with app.state.database.transaction(ctx['org_id'],ctx['actor_id']) as db:
        row=db.one("SELECT metadata FROM procurement_fact WHERE org_id=:o AND event_identity=:e AND is_current",{'o':ctx['org_id'],'e':cnpj+'-1-000001/2025:publication'})
    assert row['metadata']['source_order_verified'] is False
    assert row['metadata']['source_order_basis']=='observed_order'
