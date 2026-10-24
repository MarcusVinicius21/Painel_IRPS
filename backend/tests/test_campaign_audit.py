from copy import deepcopy
from datetime import date
from uuid import uuid4
from urllib.parse import urlencode
import httpx
import pytest
from app import sources
from app.db import identifier,encoded
from app.campaign_audit import reconcile,verified
from app.campaign_worker import tick,select_next


def row(page=1,expected=2,count=10,records=12):
    args={'provider':'PNCP','municipality_ibge':'3131307','modality':6,'start_date':'2025-10-01',
        'end_date':'2025-10-07','size':10,'page':page}
    query=urlencode({'dataInicial':'20251001','dataFinal':'20251007','codigoMunicipioIbge':'3131307',
        'codigoModalidadeContratacao':6,'pagina':page,'tamanhoPagina':10})
    return {'id':str(page),'collection_id':'a','provider':'PNCP','arguments':args,'state':'done','error_code':None,
        'http_status':200,'source_classification':'official','source_provider':'PNCP','sha256':'a'*64,
        'consulted_at':'2026-10-23','url':'https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao?'+query,
        'body_hash_matches':True,
        'source_metadata':{'scope':deepcopy(args)},'record_count':count,
        'result':{'expected_pages':expected,'expected_records':records}}


def test_reconciled_pages_and_counts_are_not_municipal_purchase_coverage():
    report=reconcile([row(),row(2,count=2)])
    group=report['groups'][0]
    assert group['pagination_reconciled'] and group['count_reconciliation']=='reconciled'
    assert group['observed_rows']==12 and report['materialized_request_percent']=='100'
    assert report['municipal_purchase_completeness'] is None


def test_missing_middle_page_is_detected_even_with_all_materialized_tasks_done():
    report=reconcile([row(expected=3,records=22),row(3,expected=3,count=2,records=22)])
    group=report['groups'][0]
    assert group['missing_pages']==[2] and not group['pagination_reconciled']
    assert report['materialized_request_percent']=='100' and report['municipal_purchase_completeness'] is None


@pytest.mark.parametrize('change',[
    {'http_status':429},{'source_provider':'PNCP_RESULTADOS'},{'body_hash_matches':False},
    {'source_metadata':{'scope':{'municipality_ibge':'3168705'}}},
    {'url':'https://example.invalid/api/consulta/v1/contratacoes/publicacao'},
    {'url':row()['url'].replace('codigoMunicipioIbge=3131307','codigoMunicipioIbge=3168705')},
    {'url':row()['url'].replace('/publicacao?','/atualizacao?')},
    {'state':'failed_retryable','error_code':'RATE_LIMIT'}])
def test_success_claim_requires_same_provider_scope_url_and_http(change):
    r={**row(),**change};assert not verified(r)
    report=reconcile([r]);assert report['verified_completed_tasks']==0
    assert not report['groups'][0]['pagination_reconciled']


def test_changed_source_total_and_duplicate_pages_are_not_reconciled():
    report=reconcile([row(expected=3),row(2,expected=2,count=2)])
    assert 'pagination_totals_changed' in report['groups'][0]['errors']
    assert not report['groups'][0]['pagination_reconciled']
    duplicate=reconcile([row(expected=1,count=12),row(expected=1,count=12)])['groups'][0]
    assert 'duplicate_page_identity' in duplicate['errors'] and not duplicate['pagination_reconciled']


def test_count_mismatch_and_missing_count_denominator_are_explicit():
    mismatch=reconcile([row(expected=1,count=5)])['groups'][0]
    assert mismatch['count_reconciliation']=='mismatch'
    unknown=reconcile([row(expected=1,count=5,records=None)])['groups'][0]
    assert unknown['expected_records'] is None and unknown['count_reconciliation']=='not_verifiable'
    assert reconcile([])['materialized_request_percent'] is None


def test_pages_from_different_collections_are_not_stitched_together():
    a=row();b=row(2,count=2);b['collection_id']='b'
    report=reconcile([a,b]);assert report['group_count']==2
    assert not any(g['pagination_reconciled'] for g in report['groups'])


def test_page_budget_exhaustion_is_visible_and_does_not_close_missing_prefix():
    r=row();r.update(collection_state='limited',collection_pages=1,max_pages='1',attempts=2)
    group=reconcile([r])['groups'][0]
    assert group['collection_limited'] and group['known_page_budget']=='1' and group['max_attempts_seen']==2
    assert group['missing_pages']==[2] and not group['pagination_reconciled']


def test_item_endpoint_requires_a_terminal_short_page():
    a=row(expected=None);b=row(2,expected=None,count=3)
    for r in (a,b):
        r['provider']=r['source_provider']='PNCP_ITENS'
        r['arguments']={'provider':'PNCP_ITENS','procurement_id':'fixture-parent','size':10,'page':r['arguments']['page']}
        r['source_metadata']={'scope':deepcopy(r['arguments'])}
        r['url']='https://pncp.gov.br/api/pncp/v1/orgaos/00000000000001/compras/2025/1/itens?'+urlencode({'pagina':r['arguments']['page'],'tamanhoPagina':10})
    assert not reconcile([a])['groups'][0]['pagination_reconciled']
    assert reconcile([a,b])['groups'][0]['pagination_reconciled']


def make_campaign(app,login,cities):
    c=login();ctx=c.get('/api/v1/auth/context').json()
    response=c.post('/api/v1/history-collections',json={'municipalities':cities,'start':'2022-07-01','end':'2022-07-07',
        'items':False,'results':False,'max_pages':10})
    assert response.status_code==201,response.text
    cid=response.json()['id']
    with app.state.database.transaction(ctx['org_id'],ctx['actor_id']) as db:
        db.execute("UPDATE history_collection SET scope=jsonb_set(scope,'{_campaign}',CAST(:campaign AS jsonb)) WHERE org_id=:o AND id=:c",
            {'o':ctx['org_id'],'c':cid,'campaign':'{"key":"'+uuid4().hex+'"}'})
    return c,ctx,cid


def test_audit_api_filters_cities_before_grouping_and_preserves_isolation(app,login):
    c,ctx,cid=make_campaign(app,login,['3131307','3168705'])
    params={'start':'2022-07-01','end':'2022-07-07','municipalities':['3131307'],'limit':1000}
    response=c.get('/api/v1/history-campaign/audit',params=params);assert response.status_code==200,response.text
    groups=response.json()['groups'];assert any(g['collection_id']==cid for g in groups)
    assert all(g['scope'].get('municipality_ibge')!='3168705' for g in groups)
    assert response.json()['municipal_purchase_completeness'] is None
    other=login('compras-b').get('/api/v1/history-campaign/audit',params=params)
    assert other.status_code==200 and all(g['collection_id']!=cid for g in other.json()['groups'])
    assert login('consulta-a').get('/api/v1/history-campaign/audit',params=params).status_code==403
    assert c.get('/api/v1/history-campaign/audit',params={**params,'municipalities':['9999999']}).status_code==422
    assert c.get('/api/v1/history-campaign/audit',params={**params,'modality':6}).status_code==422


def test_dynamic_pool_preview_and_manual_pause_make_no_requests(app,login):
    c,ctx,cid=make_campaign(app,login,['3131307']);calls=[]
    transport=httpx.MockTransport(lambda request:(calls.append(str(request.url)) or httpx.Response(204)))
    preview=tick(app.state.database,ctx['org_id'],ctx['actor_id'],date(2022,7,1),date(2022,7,7),
        collection_ids=[cid],transport=transport,sleep=lambda _:None)
    assert not preview['executed'] and calls==[] and preview['selected_collections']==[cid]
    assert c.post('/api/v1/history-collections/'+cid+'/pause').status_code==200
    paused=tick(app.state.database,ctx['org_id'],ctx['actor_id'],date(2022,7,1),date(2022,7,7),execute=True,
        collection_ids=[cid],transport=transport,sleep=lambda _:None)
    assert paused['pages']==0 and calls==[] and paused['state']=='no_eligible_requests_now'
    with app.state.database.transaction(ctx['org_id'],ctx['actor_id']) as db:
        assert select_next(sources.job_context(db,ctx['org_id'],ctx['actor_id']),date(2022,7,1),date(2022,7,7),[cid])==[]


@pytest.mark.parametrize('valid_json',[True,False])
def test_saved_legacy_header_is_recovered_without_mutating_history_page(app,login,valid_json):
    assert app.state.settings.auth_mode=='local_test'
    c,ctx,cid=make_campaign(app,login,['3131307'])
    with app.state.database.transaction(ctx['org_id'],ctx['actor_id']) as db:
        task=db.one('SELECT * FROM history_task WHERE org_id=:o AND collection_id=:c',{'o':ctx['org_id'],'c':cid})
        args=task['arguments'];url='https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao?'+urlencode({
            'dataInicial':'20220701','dataFinal':'20220707','codigoMunicipioIbge':'3131307',
            'codigoModalidadeContratacao':6,'pagina':1,'tamanhoPagina':args['size']})
        body=b'{"data":[],"totalPaginas":1,"totalRegistros":0}' if valid_json else b'not-json-qa'
        sid=sources.observe(sources.job_context(db,ctx['org_id'],ctx['actor_id']),'PNCP',url,200,body,{'scope':args,'fixture_only':True})
        db.execute('INSERT INTO history_page(org_id,collection_id,task_id,source_id,record_count,result) VALUES (:o,:c,:t,:s,0,CAST(:r AS jsonb))',
            {'o':ctx['org_id'],'c':cid,'t':task['id'],'s':sid,'r':encoded({'expected_pages':1})})
        db.execute("UPDATE history_task SET state='done' WHERE org_id=:o AND id=:i",{'o':ctx['org_id'],'i':task['id']})
    response=c.get('/api/v1/history-campaign/audit',params={'start':'2022-07-01','end':'2022-07-07','limit':1000})
    assert response.status_code==200,response.text
    group=next(g for g in response.json()['groups'] if g['collection_id']==cid)
    if valid_json:assert group['fully_reconciled'] and group['expected_records']==0
    else:assert 'done_without_sufficient_evidence' in group['errors'] and not group['pagination_reconciled']
    with app.state.database.transaction(ctx['org_id'],ctx['actor_id']) as db:
        saved=db.one('SELECT result FROM history_page WHERE org_id=:o AND collection_id=:c',{'o':ctx['org_id'],'c':cid})
    assert saved['result']=={'expected_pages':1}
