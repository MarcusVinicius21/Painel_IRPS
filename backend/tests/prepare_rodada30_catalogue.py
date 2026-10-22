"""Dados de catálogo inteiramente fictícios; importação somente em banco descartável."""
from pathlib import Path
import os,sys,json,csv
from uuid import uuid4
root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/'backend'))
os.environ['IRPS_LOCAL_CONFIG']=str(root/'.runtime/sequence-05-06/config-browser.json')
from app.config import load_settings
from app.national_catalogue import import_csv
from sqlalchemy.engine import make_url
s=load_settings();u=make_url(s.owner_database_url.get_secret_value())
assert s.testing and s.auth_mode=='local_test' and u.host=='127.0.0.1' and u.database.startswith('irps_multi_i0503_')
target=root/'.runtime/rodada30/testing';tag='CAT30'+uuid4().hex[:8];result={'tag':tag,'synthetic':True}
for kind in ['CATMAT','CATSER']:
 p=target/(tag+'-'+kind+'.csv');base=int(uuid4().hex[:10],16)
 with p.open('w',encoding='utf-8',newline='') as f:
  w=csv.writer(f,delimiter=';');w.writerow((['codigoItem','descricaoItem','statusItem'] if kind=='CATMAT' else ['codigoServico','nomeServico','statusServico'])+['codigoGrupo','nomeGrupo','codigoClasse','nomeClasse'])
  for i in range(31):w.writerow([str(base+i),f'{tag} — {kind} fictício de teste {i:02d}',i%2==0,'990030','Grupo fictício de teste','990031','Classe fictícia de teste'])
 imported=import_csv(s.owner_database_url.get_secret_value(),p,kind,origin='Dados fictícios gerados para QA local. Não representam códigos oficiais.')
 result[kind]={**imported,'active':str(base),'inactive':str(base+1)}
(target/'catalogue.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('62 códigos fictícios de teste importados em dois snapshots isolados, sem remover versões anteriores.')
