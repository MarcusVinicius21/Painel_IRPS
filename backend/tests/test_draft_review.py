import io,zipfile,json
import pytest
from sqlalchemy import create_engine,text
from sqlalchemy.exc import DBAPIError
from app.security import stable_id
from test_director_workflow import make_study,draft_body


def draft(c,s=None,**kw):
 s=s or make_study(c);r=c.post('/api/v1/director/studies/'+s['id']+'/drafts',json=draft_body(**kw));assert r.status_code==201
 return s,r.json()


def event(meta,status='requested',**kw):
 return {'expected_revision':meta['revision'],'context_sha256':meta['context_sha256'],'status':status,'note':'Parecer interno sintético, sem aprovação oficial.',**kw}


def test_request_review_versions_and_comparison_preserve_documents(login):
 c=login();s,d=draft(c);url='/api/v1/irp-drafts/'+d['id'];before=c.get(url).json()['payload'];meta=c.get(url+'/review').json()
 assert meta['status']=='not_requested' and not meta['officially_approved']
 first=c.post(url+'/review',json=event(meta));assert first.status_code==201,first.text
 assert c.post(url+'/review',json=event(meta)).status_code==409
 reviewed=c.post(url+'/review',json=event(first.json(),'reviewed_internal'));assert reviewed.status_code==201,reviewed.text
 assert reviewed.json()['revision']==2 and len(reviewed.json()['events'])==2
 assert reviewed.json()['events'][0]['created_by_name']=='Equipe de compras A'
 assert c.get(url).json()['payload']==before
 assert c.post(url+'/exports/pdf').status_code==201
 _,new=draft(c,s,note='Observações da nova versão para comparar.')
 diff=c.get('/api/v1/irp-drafts/'+new['id']+'/compare/'+d['id']);assert diff.status_code==200
 assert any(r['field']=='note' and r['after']=='Observações da nova versão para comparar.' for r in diff.json()['differences'])
 old=c.get(url+'/review').json();assert not old['latest_for_kind'] and old['export_blocked']
 assert c.post(url+'/exports/pdf').status_code==409
 assert c.post(url+'/review',json=event(old)).status_code==409
 assert c.get('/api/v1/irp-drafts/'+new['id']+'/review').json()['status']=='not_requested'


def test_changes_require_new_draft_and_do_not_grant_approval(login):
 c=login();s,d=draft(c);url='/api/v1/irp-drafts/'+d['id'];meta=c.get(url+'/review').json()
 assert c.post(url+'/review',json=event(meta,'reviewed_internal')).status_code==422
 requested=c.post(url+'/review',json=event(meta)).json();changes=c.post(url+'/review',json=event(requested,'changes_requested'))
 assert changes.status_code==201 and changes.json()['export_blocked']
 assert c.post(url+'/exports/docx').status_code==409
 dossier=c.post('/api/v1/director/studies/'+s['id']+'/dossier');assert dossier.status_code==201
 with zipfile.ZipFile(io.BytesIO(c.get(dossier.json()['download_url']).content)) as archive:
  index=json.loads(archive.read('indice.json'))
  assert any(f.get('id')==d['id'] and f.get('included') is False for f in index['files'])
  assert not any(n.startswith('minutas/') for n in archive.namelist())
 assert c.post(url+'/review',json=event(changes.json(),'reviewed_internal')).status_code==422
 assert c.get(url+'/review').json()['officially_approved'] is False
 assert c.get(url).json()['payload']['signature_invented'] is False
 _,new=draft(c,s,note='Minuta corrigida sintética para revisão nova.')
 fresh=c.get('/api/v1/irp-drafts/'+new['id']+'/review').json();assert fresh['can_submit'] and not fresh['export_blocked']


@pytest.mark.parametrize('change',[{'context_sha256':'0'*64},{'expected_revision':99}])
def test_wrong_version_or_context_is_rejected(login,change):
 c=login();_,d=draft(c);url='/api/v1/irp-drafts/'+d['id']+'/review';meta=c.get(url).json()
 assert c.post(url,json={**event(meta),**change}).status_code==409
 assert c.get(url).json()['revision']==0


def test_roles_rls_invalid_state_and_scenario_change(login,app,settings,monkeypatch):
 from app import security
 c=login();s,d=draft(c);url='/api/v1/irp-drafts/'+d['id'];meta=c.get(url+'/review').json()
 assert c.post(url+'/review',json={**event(meta),'status':'approved'}).status_code==422
 assert login('consulta-a').post(url+'/review',json=event(meta)).status_code==403
 assert login('compras-b').get(url+'/review').status_code==404
 assert login('compras-b').post(url+'/review',json=event(meta)).status_code==404
 with monkeypatch.context() as m:
  m.setitem(security.PERMISSIONS,'planner',security.PERMISSIONS['planner']-{'document.review','scenario.review'})
  req=c.post(url+'/review',json=event(meta));assert req.status_code==201
  assert c.post(url+'/review',json=event(req.json(),'reviewed_internal')).status_code==403
 current=c.get(url+'/review').json()
 with app.state.database.transaction(stable_id('org:compras-b')) as db:assert not db.all('SELECT * FROM irp_draft_review WHERE draft_id=:d',{'d':d['id']})
 owner=create_engine(settings.owner_database_url.get_secret_value(),hide_parameters=True)
 with pytest.raises(DBAPIError):
  with owner.begin() as conn:conn.execute(text('DELETE FROM irp_draft_review WHERE draft_id=:d'),{'d':d['id']})
 owner.dispose()
 sc=c.get('/api/v1/scenarios/'+s['scenario']['id']).json()
 assert c.put('/api/v1/scenarios/'+sc['id'],headers={'If-Match':'1'},json={**sc['snapshot'],'period':'2028 revisado'}).status_code==200
 assert c.post(url+'/review',json=event(current,'reviewed_internal')).status_code==409
 assert c.get(url+'/review').json()['export_blocked']
