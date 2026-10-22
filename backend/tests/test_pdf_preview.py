import io
from pathlib import Path
from pypdf import PdfReader
from PIL import Image
from test_director_workflow import make_study,draft_body


def exported(c):
 s=make_study(c);draft=c.post('/api/v1/director/studies/'+s['id']+'/drafts',json=draft_body(note='Nota sintética para paginação. '*60)).json()
 response=c.post('/api/v1/irp-drafts/'+draft['id']+'/exports/pdf');assert response.status_code==201,response.text
 return s,draft,response.json()


def test_pdf_is_real_bound_paged_and_private(login,app,monkeypatch):
 c=login();s,d,a=exported(c);url='/api/v1/irp-drafts/'+d['id']+'/pdf/'+a['id']
 meta=c.get(url);assert meta.status_code==200,meta.text
 raw=c.get(a['download_url']).content;reader=PdfReader(io.BytesIO(raw));assert meta.json()['pages']==len(reader.pages)
 assert meta.json()['sha256']==a['sha256'] and meta.json()['internal_draft']
 page=c.get(url+'/pages/1');assert page.status_code==200 and page.content.startswith(b'\x89PNG')
 img=Image.open(io.BytesIO(page.content));assert max(img.size)==1400
 assert page.headers['cache-control']=='no-store'
 assert c.get(url+'/pages/0').status_code==404
 assert c.get(url+'/pages/'+str(len(reader.pages)+1)).status_code==404
 assert login('compras-b').get(url).status_code==404
 assert login('compras-b').get(url+'/pages/1').status_code==404
 other=c.post('/api/v1/director/studies/'+s['id']+'/drafts',json=draft_body(note='Outra versão sintética, mesmo cenário.')).json()
 assert c.get('/api/v1/irp-drafts/'+other['id']+'/pdf/'+a['id']).status_code==404
 from app import security
 with monkeypatch.context() as m:
  m.setitem(security.PERMISSIONS,'viewer',security.PERMISSIONS['viewer']-{'export'})
  assert login('consulta-a').get(url).status_code==403
 sc=c.get('/api/v1/scenarios/'+s['scenario']['id']).json()
 assert c.put('/api/v1/scenarios/'+sc['id'],headers={'If-Match':'1'},json={**sc['snapshot'],'period':'2028 sintético'}).status_code==200
 assert c.get(url).status_code==409 and c.get(url+'/pages/1').status_code==409


def test_renderer_unavailable_and_tamper_fail_without_binary(login,settings,monkeypatch):
 from app import pdf_preview
 c=login();_,d,a=exported(c);url='/api/v1/irp-drafts/'+d['id']+'/pdf/'+a['id']
 with monkeypatch.context() as m:
  m.setattr(pdf_preview.shutil,'which',lambda _:None)
  assert c.get(url).status_code==200
  assert c.get(url+'/pages/1').status_code==503
  assert c.get(a['download_url']).status_code==200
 # Only generated synthetic artifacts inside the disposable test runtime are modified and restored.
 from app.security import stable_id
 p=Path(settings.runtime)/'exports'/stable_id('org:compras-a')/(a['id']+'.pdf');before=p.read_bytes()
 try:
  p.write_bytes(before+b'changed');assert c.get(url).status_code==409
 finally:p.write_bytes(before)
