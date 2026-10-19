"""Explicit bounded recovery of PUBLIC source jobs only. Default is a read-only preview."""
from pathlib import Path
import sys,argparse,json
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'backend'))
from app.config import load_settings
from app.db import Database
from app import sources
parser=argparse.ArgumentParser();parser.add_argument('--execute',action='store_true');args=parser.parse_args()
dbase=Database(load_settings());queued=[]
with dbase.transaction() as db:orgs=db.all('SELECT id FROM organization')
for org in orgs:
 with dbase.transaction(org['id']) as db:
  jobs=db.all("SELECT id,actor_id,state FROM job WHERE org_id=:o AND kind='source.sync' AND state IN ('queued','running') ORDER BY created_at LIMIT 10",{'o':org['id']})
  for job in jobs:
   try:sources.job_context(db,str(org['id']),str(job['actor_id'])).require('sources.sync')
   except Exception:continue
   queued.append({'org':str(org['id']),'actor':str(job['actor_id']),'job':str(job['id'])})
   if args.execute:db.execute("UPDATE job SET state='queued' WHERE org_id=:o AND id=:i",{'o':org['id'],'i':job['id']})
 if len(queued)>=10:break
if args.execute:
 for job in queued[:10]:sources.run_job(dbase,job['org'],job['actor'],job['job'])
print(json.dumps({'public_jobs':len(queued),'executed':args.execute,'paid_services':False}));dbase.engine.dispose()
