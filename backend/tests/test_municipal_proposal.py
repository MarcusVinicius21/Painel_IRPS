"""I05_02: existing internal suggestions, never V4 inputs or municipal confirmations."""
from decimal import Decimal
import pytest
from test_director_workflow import make_study
from test_irp_register import operation


def suggestion(**kw):
    return operation(kind='suggestion',status='proposed',quantity='12',**kw)


@pytest.mark.parametrize('amount', ['-1','0.5','1.25',None])
def test_invalid_quantity_does_not_create_operation(login,amount):
    c=login();s=make_study(c);url='/api/v1/director/studies/'+s['id']
    body=suggestion();body['quantity']=amount
    assert c.post(url+'/operations',json=body).status_code==422
    data=c.get(url+'/register').json();assert not data['history'];assert data['suggested_known_total'] is None


@pytest.mark.parametrize('step,amount,valid',[('0.25','1.25',True),('0.25','1.10',False),('5','12',False),('5','15',True),('1','0',True)])
def test_step_is_definition_bound_without_rounding(login,step,amount,valid):
    c=login();s=make_study(c,quantity_step=step);url='/api/v1/director/studies/'+s['id']
    body=suggestion();body.update(quantity=amount,status='reviewed')
    r=c.post(url+'/operations',json=body);assert r.status_code==(201 if valid else 422),r.text
    data=c.get(url+'/register').json()
    if valid:
        assert Decimal(data['suggested_known_total'])==Decimal(amount)
        assert r.json()['payload']['quantity_step']==step
    else:assert r.json()['detail']['code']=='SUGGESTION_STEP_MISMATCH'
    assert data['confirmed_known_total'] is None and data['consolidated_total'] is None


def test_versions_reason_authorship_and_concurrency_preserve_v4(login):
    c=login();s=make_study(c);url='/api/v1/director/studies/'+s['id'];scenario='/api/v1/scenarios/'+s['scenario']['id']
    before=c.get(scenario).json();study_before=c.get(url).json()['payload']
    invalid=suggestion();invalid['note']=' '*12;assert c.post(url+'/operations',json=invalid).status_code==422
    body=suggestion();body.update(note='  Justificativa municipal fictícia.  ')
    first=c.post(url+'/operations',json=body);assert first.status_code==201,first.text
    data=c.get(url+'/register').json();assert data['suggested_known_total'] is None
    assert c.post(url+'/operations',json={**body,'created_by':'forged-author'}).status_code==422
    audit=c.get('/api/v1/audit').json()['records']
    assert any(r['action']=='irp.suggestion_recorded' and str(r['resource_id'])==first.json()['id'] and r['metadata']['revision']==1 for r in audit)
    assert data['operations'][0]['created_by'] and data['operations'][0]['created_by_name']=='Equipe de compras A'
    assert data['operations'][0]['created_at'];assert data['operations'][0]['payload']['note']=='Justificativa municipal fictícia.'
    assert c.post(url+'/operations',json=body).status_code==409
    second={**body,'status':'reviewed','quantity':'16','expected_revision':1,'note':'Nova conferência fictícia documentada.'}
    assert c.post(url+'/operations',json=second).status_code==201
    data=c.get(url+'/register').json();assert data['suggested_known_total']=='16';assert data['confirmed_known_total'] is None
    assert sorted((r['revision'],r['payload']['quantity']) for r in data['history'])==[(1,'12'),(2,'16')]
    third={**second,'status':'proposed','quantity':'18','expected_revision':2}
    assert c.post(url+'/operations',json=third).status_code==201
    assert c.get(url+'/register').json()['suggested_known_total'] is None
    assert c.get(scenario).json()==before;assert c.get(url).json()['payload']==study_before


def test_context_and_permissions_are_not_bypassed(login,monkeypatch):
    from app import security
    c=login();s=make_study(c);url='/api/v1/director/studies/'+s['id'];body=suggestion();body['status']='reviewed'
    assert login('consulta-a').post(url+'/operations',json=body).status_code==403
    assert login('compras-b').post(url+'/operations',json=body).status_code==404
    assert login('compras-b').get(url+'/register').status_code==404
    with monkeypatch.context() as m:
        m.setitem(security.PERMISSIONS,'planner',security.PERMISSIONS['planner']-{'scenario.review'})
        assert c.post(url+'/operations',json=body).status_code==403
        assert c.post(url+'/operations',json={**body,'status':'proposed'}).status_code==201
    assert c.post(url+'/operations',json={**body,'expected_revision':1}).status_code==201
    scenario=c.get('/api/v1/scenarios/'+s['scenario']['id']).json()
    response=c.put('/api/v1/scenarios/'+scenario['id'],headers={'If-Match':'1'},json={**scenario['snapshot'],'period':'Outro período fictício'})
    assert response.status_code==200
    data=c.get(url+'/register').json();assert data['suggested_known_total'] is None
    row=next(r for r in data['municipalities'] if r['ibge']==body['municipality_ibge'])
    assert not row['suggestion_context_current'];assert row['suggestion_state']=='requires_reconfirmation'
    assert row['suggestion']['payload']['quantity']=='12'
    assert c.post(url+'/operations',json={**body,'expected_revision':2,'scenario_revision':2}).status_code==409


def test_optional_document_change_invalidates_suggestion_without_mutating_history(login):
    from test_irp_register import doc,review
    c=login();s=make_study(c);url='/api/v1/director/studies/'+s['id'];d=doc(c)
    body=suggestion();body.update(status='reviewed',document_id=d['id'])
    first=c.post(url+'/operations',json=body);assert first.status_code==201
    assert c.get(url+'/register').json()['suggested_known_total']=='12'
    review(c,d['id'],d['revision'],'needs_changes')
    data=c.get(url+'/register').json();assert data['suggested_known_total'] is None
    row=next(r for r in data['municipalities'] if r['ibge']==body['municipality_ibge'])
    assert row['suggestion_state']=='requires_reconfirmation'
    assert row['suggestion']['payload']['document_revision']==d['revision']
    assert row['suggestion']['payload']['quantity']=='12'
    assert c.post(url+'/operations',json={**body,'expected_revision':1}).status_code==201
    assert c.get(url+'/register').json()['suggested_known_total']=='12'
