"""Bounded, read-only public PNCP pilot stored in the configured local test database.

Run after migrations. Never claims municipal source completeness.
"""
import argparse
import json
import os
import sys
from datetime import datetime,timezone
from pathlib import Path

from fastapi.testclient import TestClient

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.config import load_settings
from app.main import create_app
from app import history


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--pages',type=int,default=24)
    parser.add_argument('--collection-id',type=str)
    parser.add_argument('--max-pages',type=int,default=100)
    parser.add_argument('--output',type=Path,default=ROOT/'.runtime/evidencias/piloto-cobertura.json')
    options=parser.parse_args()
    if not 1<=options.pages<=40 or not 1<=options.max_pages<=2000:parser.error('Use de 1 a 40 páginas por execução, até 2.000 no total.')
    os.environ.setdefault('IRPS_LOCAL_CONFIG',str(ROOT/'.runtime/config-local.json'))
    settings=load_settings()
    if settings.auth_mode!='local_test' or settings.ai_enabled:parser.error('Piloto exige ambiente local de testes e IA paga desligada.')
    settings.testing=True
    app=create_app(settings)
    with TestClient(app) as client:
        response=client.post('/api/v1/auth/test-login',json={'user_key':'compras-a'})
        response.raise_for_status()
        client.headers['x-csrf-token']=client.cookies.get('irps_csrf')
        scope={'municipalities':['3131307','3101607','3169703'],
               'start':'2025-09-01','end':'2025-09-07','modalities':[6],
               'publications':True,'updates':False,'items':True,'results':True,
               'contracts':False,'atas':False,'pca':False,'max_pages':options.pages}
        if options.collection_id:
            cid=options.collection_id
            previous=client.get('/api/v1/history-collections/'+cid)
            previous.raise_for_status()
            scope=previous.json()['scope']
            if previous.json()['state']=='limited':
                extended=client.post('/api/v1/history-collections/'+cid+'/extend',params={'max_pages':options.max_pages})
                extended.raise_for_status()
        else:
            created=client.post('/api/v1/history-collections',json=scope)
            created.raise_for_status();cid=created.json()['id']
        identity=client.get('/api/v1/auth/context').json()
        for _ in range(options.pages):
            result=history.advance(app.state.database,identity['org_id'],identity['actor_id'],cid,1)
            if not result.get('pages'):break
        collection=client.get('/api/v1/history-collections/'+cid).json()
        params={'start':scope['start'],'end':scope['end']}
        for city in scope['municipalities']:params.setdefault('municipalities',[]).append(city)
        coverage=client.get('/api/v1/coverage/inventory',params=params)
        coverage.raise_for_status()
        public_rows=[row for row in coverage.json()['records'] if row['municipality_ibge'] in scope['municipalities']]
        summary={'consulted_at_utc':datetime.now(timezone.utc).isoformat(),'collection_id':cid,
                 'scope':scope,'state':collection['state'],'pages_completed':collection['pages'],
                 'source_requests':collection['source_requests'],'error_code':collection['error_code'],
                 'coverage_basis':coverage.json()['basis'],
                 'records':[{key:row[key] for key in ('municipality_ibge','municipality_name','provider','phase',
                     'modality','tasks','completed_tasks','records_returned','planned_days','reconciled_days',
                     'request_completion_ratio','source_completeness_ratio','status','proof')}
                    for row in public_rows if row['tasks']]}
        options.output.parent.mkdir(parents=True,exist_ok=True)
        options.output.write_text(json.dumps(summary,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
        print(json.dumps({'collection_id':cid,'state':collection['state'],'pages_completed':collection['pages'],
                          'error_code':collection['error_code'],'sources_with_tasks':len(summary['records']),
                          'output':str(options.output)},ensure_ascii=False))


if __name__=='__main__':main()
