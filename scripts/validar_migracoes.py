from pathlib import Path
import os,sys,json,datetime
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'backend'))
os.environ['IRPS_LOCAL_CONFIG']=str(root/'.runtime/config-test.json');os.chdir(root/'backend')
from app.config import load_settings
from sqlalchemy import create_engine,text
from sqlalchemy.engine import make_url
from alembic.config import Config
from alembic import command
(root/'.runtime/evidencias').mkdir(parents=True,exist_ok=True)
s=load_settings();assert make_url(s.owner_database_url.get_secret_value()).database=='irps_migration_test'
engine=create_engine(s.owner_database_url.get_secret_value(),hide_parameters=True);cfg=Config('alembic.ini');steps=[]
for direction in ('upgrade','downgrade','upgrade'):
 if direction=='upgrade':command.upgrade(cfg,'head')
 else:command.downgrade(cfg,'base')
 with engine.begin() as c:
  tables=c.execute(text("SELECT count(*) FROM pg_tables WHERE schemaname='public' AND tablename<>'alembic_version'")).scalar()
  rls=c.execute(text("SELECT count(*) FROM pg_class WHERE relnamespace='public'::regnamespace AND relrowsecurity AND relforcerowsecurity")).scalar()
 steps.append({'operation':direction,'tables':tables,'rls_forced':rls})
assert steps[1]['tables']==0 and steps[0]['tables']==steps[2]['tables']
(root/'.runtime/evidencias/migracoes.json').write_text(json.dumps({'database':'irps_migration_test','steps':steps,'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'real_postgresql':True},indent=2),encoding='utf-8')
print(json.dumps(steps));engine.dispose()
