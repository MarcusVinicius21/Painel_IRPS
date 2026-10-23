"""Read-only repeatable-read operational snapshot. Never prints credentials or row bodies."""
import json,sys,argparse
from pathlib import Path
import psycopg
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.config import load_settings

def snapshot():
 s=load_settings()
 if s.auth_mode!='operational_local':raise ValueError('Select the local operational configuration explicitly')
 with psycopg.connect(s.owner_database_url.get_secret_value().replace('+psycopg','')) as c:
  c.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
  c.execute("SELECT set_config('irps.org_id',%s,true)",(s.operator_org_id,))
  def rows(query):
   cur=c.execute(query);return [dict(zip([x.name for x in cur.description],row)) for row in cur]
  result={'transaction':rows("SELECT now() utc,txid_current_snapshot()::text snapshot,current_setting('transaction_read_only') read_only,current_setting('transaction_isolation') isolation"),
   'migration':rows('SELECT version_num FROM alembic_version'),
   'identity':{t:c.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in ['actor','organization','membership']},
   'catalogue':rows('SELECT s.kind,count(*) codes FROM national_catalogue_entry e JOIN national_catalogue_snapshot s ON s.id=e.snapshot_id GROUP BY s.kind ORDER BY s.kind'),
   'facts':rows('SELECT provider,phase,classification,is_current,count(*) records FROM procurement_fact GROUP BY provider,phase,classification,is_current ORDER BY provider,phase,is_current'),
   'months':rows('SELECT kind,month,archive_sha256,source_rows,accepted_rows,rejected_rows,duplicate_rows,imported_at FROM price_monthly_snapshot ORDER BY month,kind,imported_at'),
   'prices':rows('SELECT s.kind,count(*) rows,count(DISTINCT r.code) codes,count(*) FILTER(WHERE coalesce(r.body->>\'unit\',\'\')=\'\') missing_unit FROM price_monthly_record r JOIN price_monthly_snapshot s ON s.org_id=r.org_id AND s.id=r.snapshot_id GROUP BY s.kind ORDER BY s.kind'),
   'known_codes':rows("SELECT count(DISTINCT (s.kind,r.code)) codes FROM price_monthly_record r JOIN price_monthly_snapshot s ON s.org_id=r.org_id AND s.id=r.snapshot_id WHERE EXISTS(SELECT 1 FROM national_catalogue_entry e JOIN national_catalogue_snapshot n ON n.id=e.snapshot_id WHERE n.kind=CASE WHEN s.kind='material' THEN 'CATMAT' ELSE 'CATSER' END AND e.code=r.code)"),
   'rls':rows("SELECT relname,relrowsecurity,relforcerowsecurity FROM pg_class WHERE relname IN ('price_monthly_snapshot','price_monthly_record')")}
  assert result['transaction'][0]['read_only']=='on'
  assert all(x['relforcerowsecurity'] for x in result['rls'])
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();result=snapshot();Path(a.output).write_text(json.dumps(result,default=str,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,default=str,ensure_ascii=False))
