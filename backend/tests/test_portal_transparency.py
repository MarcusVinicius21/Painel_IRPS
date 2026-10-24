import httpx
from app import portal_transparency as portal
from app.sources import job_context

def test_authenticated_empty_page_is_evidence_not_clearance(app,login,monkeypatch):
    monkeypatch.setattr(portal,'load_portal_key',lambda:'synthetic-test-key')
    c=login();identity=c.get('/api/v1/auth/context').json();calls=[]
    def response(r):
        assert r.url.host=='api.portaldatransparencia.gov.br'
        assert r.headers['chave-api-dados']=='synthetic-test-key'
        assert r.url.params['codigoSancionado']=='12579490000101';calls.append(r)
        return httpx.Response(200,json=[])
    with app.state.database.transaction(identity['org_id'],identity['actor_id']) as db:
        result=portal.sanctions(job_context(db,identity['org_id'],identity['actor_id']),'12579490000101',httpx.MockTransport(response))
        assert result['record_count']==0 and result['source_id']
        assert result['complete_sanctions_check'] is False and result['municipal_purchase_history'] is False
        assert 'synthetic-test-key' not in str(result)
    assert len(calls)==1

def test_redirect_and_auth_failure_never_follow_or_imply_no_sanctions(app,login,monkeypatch):
    monkeypatch.setattr(portal,'load_portal_key',lambda:'synthetic-test-key')
    c=login();identity=c.get('/api/v1/auth/context').json()
    for status in [302,401,403,429]:
        calls=[]
        def response(r):calls.append(r);return httpx.Response(status,headers={'Location':'https://untrusted.invalid/'})
        with app.state.database.transaction(identity['org_id'],identity['actor_id']) as db:
            result=portal.sanctions(job_context(db,identity['org_id'],identity['actor_id']),'12579490000101',httpx.MockTransport(response))
            assert result['state']!='available' and 'source_id' not in result
        assert len(calls)==1
