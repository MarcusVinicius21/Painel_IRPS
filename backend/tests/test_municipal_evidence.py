from test_director_workflow import make_study,draft_body
from test_irp_register import doc,review,operation


def test_upload_is_not_association_or_confirmation_and_provenance_is_explicit(login):
 c=login();s=make_study(c);base='/api/v1/director/studies/'+s['id'];d=doc(c)
 assert all(not m['records'] for m in c.get(base+'/register/evidence').json()['municipalities'])
 assert c.get(base+'/register').json()['confirmed_known_total'] is None
 received=c.post(base+'/operations',json=operation(status='received',document_id=d['id']));assert received.status_code==201
 row=next(m for m in c.get(base+'/register/evidence').json()['municipalities'] if m['ibge']=='3131307')['records'][0]
 assert row['qualification']=='review_pending' and row['document']['reviewer_name'] is None
 assert row['document']['uploaded_by_name']=='Equipe de compras A'
 assert row['declared_responsible']=='Pessoa fictícia de teste' and row['recorded_by_name']=='Equipe de compras A'
 assert c.get(base+'/register').json()['confirmed_known_total'] is None
 checked=review(c,d['id'],d['revision'])
 assert c.get(base+'/register').json()['confirmed_known_total'] is None
 confirmed=c.post(base+'/operations',json=operation(document_id=d['id'],expected_revision=1));assert confirmed.status_code==201
 row=next(m for m in c.get(base+'/register/evidence').json()['municipalities'] if m['ibge']=='3131307')['records'][0]
 assert row['qualification']=='reviewed_document' and row['document']['reviewed_at']
 assert row['document']['reviewer_name']=='Equipe de compras A'
 assert row['document']['current_revision']==checked['revision']==row['document']['recorded_revision']
 review(c,d['id'],checked['revision'],'needs_changes')
 row=next(m for m in c.get(base+'/register/evidence').json()['municipalities'] if m['ibge']=='3131307')['records'][0]
 assert not row['document']['revision_matches'] and row['qualification']=='review_pending'
 assert c.get(base+'/register').json()['confirmed_known_total'] is None
 assert len(c.get(base+'/register').json()['history'])==2


def test_read_permissions_and_existing_draft_snapshot_unchanged(login):
 c=login();s=make_study(c);base='/api/v1/director/studies/'+s['id'];d=c.post(base+'/drafts',json=draft_body()).json();before=c.get('/api/v1/irp-drafts/'+d['id']).json()
 assert c.get(base+'/register/evidence').status_code==200
 after=c.get('/api/v1/irp-drafts/'+d['id']).json();assert before['payload']==after['payload'] and before['stale']==after['stale']
 assert login('consulta-a').get(base+'/register/evidence').status_code==200
 assert login('compras-b').get(base+'/register/evidence').status_code==404
 assert login('consulta-a').post(base+'/operations',json=operation()).status_code==403


def test_reviewed_file_without_competence_or_channel_is_not_confirmation(login):
 c=login();s=make_study(c);base='/api/v1/director/studies/'+s['id'];d=doc(c);review(c,d['id'],d['revision'])
 for values in [{'channel':''},{'competence_evidence':''},{'responsible_name':''}]:
  assert c.post(base+'/operations',json=operation(document_id=d['id'],**values)).status_code==422
 assert c.get(base+'/register').json()['confirmed_known_total'] is None
