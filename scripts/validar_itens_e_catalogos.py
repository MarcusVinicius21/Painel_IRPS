from pathlib import Path
import os
import httpx,time,json,uuid,datetime
root=Path(__file__).resolve().parents[1];output=root/'.runtime/evidencias';results=[];output.mkdir(parents=True,exist_ok=True)
with httpx.Client(base_url=os.environ.get('IRPS_API_URL','http://127.0.0.1:5211'),timeout=35) as c:
 c.post('/api/v1/auth/test-login',json={'user_key':'compras-a'}).raise_for_status();c.headers['X-CSRF-Token']=c.cookies['irps_csrf']
 rows=c.get('/api/v1/purchases?dataset=official&limit=100').json()['records'];headers=[r for r in rows if r['provider']=='PNCP'];selected=[]
 for pred in (lambda r:r['municipality_ibge']=='3131307',lambda r:r.get('cnpj')=='08184434000109'):
  r=next((r for r in headers if pred(r)),None)
  if r and r['id'] not in selected:selected.append(r['id'])
 operations=[{'provider':'PNCP_ITENS','procurement_id':i,'page':1,'size':10} for i in selected]+[{'provider':p,'page':1,'size':10} for p in ('COMPRAS_CATMAT','COMPRAS_CATSER')]
 for args in operations:
  r=c.post('/api/v1/sources/sync',json=args,headers={'Idempotency-Key':'public-items-'+str(uuid.uuid4())});r.raise_for_status();jid=r.json()['id']
  for _ in range(35):
   job=c.get('/api/v1/jobs/'+jid).json()
   if job['state'] in ('completed','failed'):break
   time.sleep(1)
  results.append({'request':args,'job':job});print(json.dumps({'provider':args['provider'],'state':job['state'],'records':(job.get('result') or {}).get('records')}),flush=True)
 purchases=c.get('/api/v1/purchases?dataset=official&limit=100').json();catalogue=c.get('/api/v1/catalogue/official').json();items=[r for r in purchases['records'] if r['provider']=='PNCP_ITENS'];secret=[r for r in items if r['metadata'].get('budget_secret')]
 result={'consulted_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'operations':results,'persisted_official_records':purchases['total'],'official_items_in_first_page':len(items),'official_catalogue_entries':len(catalogue['records']),'secret_price_records':len(secret),'secret_values_remain_absent':all(r['unit_price'] is None and r['amount'] is None for r in secret),'sample_items':items[:3],'catalogue':catalogue['records'][:2]}
 (output/'fontes-itens-catalogos-execucao.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');c.post('/api/v1/auth/logout')
