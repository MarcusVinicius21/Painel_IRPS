from pathlib import Path
import os
import httpx,time,json,uuid,datetime
root=Path(__file__).resolve().parents[1];evidence=root/'.runtime/evidencias'
results=[]
evidence.mkdir(parents=True,exist_ok=True)
with httpx.Client(base_url=os.environ.get('IRPS_API_URL','http://127.0.0.1:5211'),timeout=35) as client:
 r=client.post('/api/v1/auth/test-login',json={'user_key':'compras-a'});r.raise_for_status();client.headers['X-CSRF-Token']=client.cookies['irps_csrf']
 for args in [{'provider':'IBGE','municipality_ibge':'3131307'},{'provider':'PNCP','start_date':'2026-10-18','end_date':'2026-10-19','page':1,'size':10,'modality':6},{'provider':'PNCP','start_date':'2026-10-13','end_date':'2026-10-19','municipality_ibge':'3131307','page':1,'size':10,'modality':6}]:
  response=client.post('/api/v1/sources/sync',json=args,headers={'Idempotency-Key':'public-validation-'+str(uuid.uuid4())});response.raise_for_status();jid=response.json()['id']
  for _ in range(35):
   job=client.get('/api/v1/jobs/'+jid);job.raise_for_status();job=job.json()
   if job['state'] in ('completed','failed'):break
   time.sleep(1)
  results.append({'request':args,'job':job});print(json.dumps({'provider':args['provider'],'state':job['state'],'records':(job.get('result') or {}).get('records')},ensure_ascii=False),flush=True)
 records=client.get('/api/v1/purchases?dataset=official&limit=100').json();observations=client.get('/api/v1/sources').json()
 client.post('/api/v1/auth/logout')
(evidence/'fontes-publicas-execucao.json').write_text(json.dumps({'consulted_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'results':results,'persisted_official_records':records['total'],'sources':observations},ensure_ascii=False,indent=2),encoding='utf-8')
