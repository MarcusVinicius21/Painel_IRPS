"""Reproducible LOCAL synthetic study using an imported national catalogue code.

Public catalogue identity is retained. Targets/technical review are explicitly fictional.
No government network request, private quotation or paid provider is used.
"""
import sys,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.config import load_settings
from app.main import create_app
from app.db import Database,normalize
from fastapi.testclient import TestClient

if __name__=='__main__':
    settings=load_settings()
    if settings.auth_mode!='local_test':raise SystemExit('Use somente o ambiente local de testes.')
    out=ROOT/'.runtime/evidencias/diretriz-v2';out.mkdir(parents=True,exist_ok=True)
    with TestClient(create_app(settings)) as c:
        r=c.post('/api/v1/auth/test-login',json={'user_key':'compras-a'});assert r.status_code==200
        c.headers['x-csrf-token']=c.cookies.get('irps_csrf')
        candidates=c.get('/api/v1/national-catalogue',params={'q':'café torrado','active':True,'limit':50}).json()['records']
        item=next((r for r in candidates if r['name'].lstrip('" ').upper().startswith(('CAFÉ','CAFE'))),None)
        if not item:raise SystemExit('Importe o CATMAT fornecido antes de executar esta demonstração.')
        cities=[r['ibge'] for r in c.get('/api/v1/municipalities').json()['records'][:3]]
        body={'classification':'synthetic','snapshot_id':item['snapshot_id'],'code':item['code'],'name':item['name'],
            'specification':item['name']+' Definição de demonstração: unidade kg. Não representa aprovação institucional.',
            'category':'material','unit':'kg','quantity_step':'1','municipalities':cities,'phase':'homologado','start':'2025-01-01','end':'2026-10-20',
            'preliminary_target':'200','target_justification':'Meta fictícia para demonstrar o fluxo local, sem rateio municipal.',
            'technical_evidence':'Conferência sintética exclusiva para demonstrar a geração documental.','technical_confirmed':True}
        r=c.post('/api/v1/director/studies',json=body);assert r.status_code==201,r.text;study=r.json()
        r=c.post('/api/v1/director/studies/'+study['id']+'/drafts',json={'scenario_revision':1,'object':'Estudo de aquisição de '+item['name'],
            'kind':'procedimento','coherence_confirmed':True,'coherence_evidence':'Conferência sintética para verificar a composição da minuta.'})
        assert r.status_code==201,r.text;draft=r.json()
        for fmt in ('docx','pdf'):
            r=c.post('/api/v1/irp-drafts/'+draft['id']+'/exports/'+fmt);assert r.status_code==201,r.text
            raw=c.get(r.json()['download_url']);assert raw.status_code==200;(out/('minuta-demonstrativa.'+fmt)).write_bytes(raw.content)
        r=c.post('/api/v1/director/studies/'+study['id']+'/dossier');assert r.status_code==201,r.text
        (out/'dossie-demonstrativo.zip').write_bytes(c.get(r.json()['download_url']).content)
        performance=[]
        for term in ('','café torrado','veículo'):
            t=time.perf_counter();response=c.get('/api/v1/national-catalogue',params={'q':term,'limit':25})
            assert response.status_code==200;performance.append({'query':term,'records':len(response.json()['records']),'seconds':round(time.perf_counter()-t,4)})
    demo={'study_id':study['id'],'draft_id':draft['id'],'scenario_id':study['scenario']['id'],'classification':'synthetic','catalogue_code':item['code'],
          'catalogue_name':item['name'],'meta_distributed':False,'v4_inputs_inferred':False,'network_requests':0,
          'url':'http://127.0.0.1:5248/#/inteligencia?estudo='+study['id'],'local_search_measurements':performance}
    (out/'demo.json').write_text(json.dumps(demo,ensure_ascii=False,indent=2),encoding='utf-8')
    with Database(settings).transaction() as db:
        inventory={'catalogue_snapshots':db.all('SELECT id,kind,sha256,row_count,active_count,inactive_count,origin,imported_at FROM national_catalogue_snapshot ORDER BY kind,imported_at'),
            'official_fact_counts':db.all("SELECT provider,phase,count(*) AS current_records,min(event_date) AS first_event,max(event_date) AS last_event FROM procurement_fact WHERE classification='official' AND is_current GROUP BY provider,phase ORDER BY provider,phase"),
            'municipalities_observed':db.all("SELECT m.ibge,m.name,m.uf,f.provider,f.phase,count(*) AS current_records,min(f.event_date) AS first_event,max(f.event_date) AS last_event FROM procurement_fact f JOIN municipality m ON m.ibge=f.municipality_ibge WHERE f.classification='official' AND f.is_current GROUP BY m.ibge,m.name,m.uf,f.provider,f.phase ORDER BY m.name,f.provider,f.phase"),
            'observations':db.all("SELECT provider,url,sha256,consulted_at,http_status FROM source_observation WHERE classification='official' ORDER BY consulted_at DESC LIMIT 250"),
            'notice':'Inventário de fatos existentes, não declaração de cobertura municipal completa. Nenhuma nova coleta nacional foi executada.'}
    (out/'inventario-dados.json').write_text(json.dumps(normalize(inventory),ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(demo,ensure_ascii=False))
