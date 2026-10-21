from datetime import date
from uuid import uuid4
from test_director_workflow import make_study


def doc(client,classification='synthetic'):
    r=client.post('/api/v1/documents',files={'file':('manifestacao.csv',('descricao;quantidade\nManifestação fictícia '+uuid4().hex+';30\n').encode(),'text/csv')},data={'classification':classification})
    assert r.status_code==201,r.text
    return r.json()


def review(client,did,revision,decision='reviewed'):
    r=client.post('/api/v1/documents/'+did+'/review',json={'revision':revision,'decision':decision,'note':'Conferência fictícia do documento em teste local.','corrections':{}})
    assert r.status_code==200,r.text
    return r.json()


def operation(**values):
    return {'kind':'manifestation','municipality_ibge':'3131307','expected_revision':0,'scenario_revision':1,
        'status':'confirmed','quantity':'30','event_date':date.today().isoformat(),'channel':'Canal formal fictício',
        'responsible_name':'Pessoa fictícia de teste','competence_evidence':'Documento fictício de competência conferido no teste.',
        'note':'Registro sintético para teste do fluxo documental.',**values}


def test_confirmation_requires_reviewed_evidence_and_never_uses_silence(login):
    c=login();s=make_study(c);base='/api/v1/director/studies/'+s['id']
    assert c.post(base+'/operations',json=operation()).status_code==422
    d=doc(c)
    assert c.post(base+'/operations',json=operation(document_id=d['id'])).status_code==422
    checked=review(c,d['id'],d['revision'])
    r=c.post(base+'/operations',json=operation(document_id=d['id']));assert r.status_code==201,r.text
    assert c.post(base+'/operations',json=operation(document_id=d['id'])).status_code==409
    summary=c.get(base+'/register').json();assert summary['confirmed_known_total']=='30' and summary['consolidated_total'] is None
    assert summary['pending_municipalities']==1
    other=c.post(base+'/operations',json=operation(kind='communication',municipality_ibge='3101607',status='no_response',quantity=None,document_id=None))
    assert other.status_code==201,other.text
    pending=next(r for r in c.get(base+'/register').json()['municipalities'] if r['ibge']=='3101607')
    assert pending['manifestation_state']=='not_received' and pending['confirmed_quantity'] is None
    # A later document revision invalidates the former confirmation even if it is reviewed again.
    changed=review(c,d['id'],checked['revision'],'needs_changes')
    assert c.get(base+'/register').json()['confirmed_known_total'] is None
    review(c,d['id'],changed['revision'])
    assert c.get(base+'/register').json()['confirmed_known_total'] is None
    r=c.post(base+'/operations',json=operation(document_id=d['id'],expected_revision=1));assert r.status_code==201
    assert c.get(base+'/register').json()['confirmed_known_total']=='30'
    assert login('compras-b').get(base+'/register').status_code==404


def test_suggestions_stay_independent_and_revision_invalidates_register(login):
    from test_director_workflow import draft_body
    c=login();s=make_study(c);base='/api/v1/director/studies/'+s['id']
    draft=c.post(base+'/drafts',json=draft_body()).json()
    r=c.post(base+'/operations',json=operation(kind='suggestion',status='reviewed',quantity='80'))
    assert r.status_code==201,r.text
    data=c.get(base+'/register').json();first=next(r for r in data['municipalities'] if r['ibge']=='3131307')
    assert first['suggested_quantity']=='80' and first['confirmed_quantity'] is None
    assert c.post('/api/v1/irp-drafts/'+draft['id']+'/exports/docx').status_code==409
    scenario=c.get('/api/v1/scenarios/'+s['scenario']['id']).json();assert scenario['snapshot']['inputs']=={}
    changed=c.put('/api/v1/scenarios/'+scenario['id'],headers={'If-Match':'1'},json={**scenario['snapshot'],'period':'2028 revisado'})
    assert changed.status_code==200
    data=c.get(base+'/register').json();assert not data['context_current']
    assert all(r['suggested_quantity'] is None for r in data['municipalities'])
    assert c.post(base+'/operations',json=operation(kind='suggestion',status='reviewed',quantity='81',expected_revision=1,scenario_revision=2)).status_code==409


def test_external_act_needs_proof_and_synthetic_documents_are_isolated(login):
    c=login();s=make_study(c);base='/api/v1/director/studies/'+s['id']
    r=c.post(base+'/operations',json=operation(kind='external_act',status='evidence_recorded',quantity=None,external_act='publicidade',protocol='Teste-001'))
    assert r.status_code==422
    d=doc(c);r=c.post(base+'/operations',json=operation(kind='external_act',status='evidence_recorded',quantity=None,external_act='publicidade',protocol='Teste-001',document_id=d['id']))
    assert r.status_code==201 and not r.json()['payload']['official_act_performed_by_irps']
    internal=make_study(c,classification='internal');r=c.post('/api/v1/director/studies/'+internal['id']+'/operations',json=operation(document_id=d['id']))
    assert r.status_code==422 and r.json()['detail']['code']=='DATASET_MISMATCH'
    assert login('consulta-a').post(base+'/operations',json=operation()).status_code==403


def test_dossier_is_tenant_scoped_and_excludes_private_quotations_and_originals(login):
    import io,json,zipfile
    from test_director_workflow import draft_body
    c=login();s=make_study(c);base='/api/v1/director/studies/'+s['id']
    assert c.post(base+'/drafts',json=draft_body()).status_code==201
    r=c.post(base+'/dossier');assert r.status_code==201,r.text
    raw=c.get(r.json()['download_url']).content
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        assert 'minutas/procedimento.docx' in z.namelist()
        assert 'consolidacao/quadro-municipal-e-item.xlsx' in z.namelist()
        assert 'consolidacao/quadro-municipal-e-item.pdf' in z.namelist()
        index=json.loads(z.read('indice.json'));assert not index['original_documents_embedded'] and not index['private_quotations_included']
        assert not any(name.startswith(('uploads/','negocio/')) for name in z.namelist())
    assert login('compras-b').post(base+'/dossier').status_code==404
