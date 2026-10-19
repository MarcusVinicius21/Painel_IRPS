"""Cluster descartável do projeto, loopback, sem serviço global e sem segredos no console."""
from pathlib import Path
import sys,subprocess,json,secrets,socket,os
from sqlalchemy import URL
APP=Path(__file__).resolve().parent.parent
RUNTIME=APP/'.runtime';RUNTIME.mkdir(exist_ok=True)
BIN=APP/'_tools/postgresql/bin';DATA=RUNTIME/'postgres-data';PORT=int(os.environ.get('IRPS_PG_PORT','55432'));API_PORT=int(os.environ.get('IRPS_API_PORT','5211'));WEB_PORT=int(os.environ.get('IRPS_FRONTEND_PORT','5210'))
if not all(1024<=p<=65535 for p in (PORT,API_PORT,WEB_PORT)):raise SystemExit('Porta local inválida.')
FLAGS=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
credentials=RUNTIME/'postgres-test-credentials.json'
if not credentials.exists():
 if DATA.exists():raise SystemExit('Dados existentes sem configuração do projeto. Não prosseguir.')
 credentials.write_text(json.dumps({'owner':secrets.token_urlsafe(32),'app':secrets.token_urlsafe(32)}),encoding='utf-8')
keys=json.loads(credentials.read_text(encoding='utf-8'))
if not (DATA/'PG_VERSION').exists():
 pw=RUNTIME/'initdb-password.txt';pw.write_text(keys['owner'],encoding='utf-8')
 r=subprocess.run([str(BIN/'initdb.exe'),'-D',str(DATA),'-U','irps_owner','--pwfile='+str(pw),'--auth=scram-sha-256','--encoding=UTF8','--locale=C'],capture_output=True,text=True,creationflags=FLAGS)
 (RUNTIME/'initdb.log').write_text(r.stdout+r.stderr,encoding='utf-8')
 pw.unlink()
 if r.returncode:raise SystemExit('Falha ao inicializar o cluster local. Consulte .runtime/initdb.log.')
running=subprocess.run([str(BIN/'pg_ctl.exe'),'-D',str(DATA),'status'],capture_output=True,text=True,creationflags=FLAGS)
if running.returncode:
 with socket.socket() as s:
  if s.connect_ex(('127.0.0.1',PORT))==0:raise SystemExit('Porta ocupada. Não alterar outro processo.')
 with (RUNTIME/'pgctl-start.log').open('w',encoding='utf-8') as log:
  r=subprocess.run([str(BIN/'pg_ctl.exe'),'-D',str(DATA),'-l',str(RUNTIME/'postgres.log'),'-o',f'-h 127.0.0.1 -p {PORT}','-w','start'],stdout=log,stderr=subprocess.STDOUT,text=True,creationflags=FLAGS,timeout=60)
 if r.returncode:raise SystemExit('Falha ao iniciar PostgreSQL local. Nenhum serviço global foi usado.')
import psycopg
from psycopg import sql
with psycopg.connect(user='irps_owner',password=keys['owner'],host='127.0.0.1',port=PORT,dbname='postgres',autocommit=True) as conn:
 if not conn.execute("SELECT 1 FROM pg_roles WHERE rolname='irps_app'").fetchone():conn.execute(sql.SQL('CREATE ROLE irps_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS PASSWORD {}').format(sql.Literal(keys['app'])))
 for name in ('irps_local','irps_migration_test'):
  if not conn.execute('SELECT 1 FROM pg_database WHERE datname=%s',(name,)).fetchone():conn.execute(sql.SQL('CREATE DATABASE {} OWNER irps_owner').format(sql.Identifier(name)))
def database_url(role,key):
 return URL.create('postgresql+psycopg',username=role,password=keys[key],host='127.0.0.1',port=PORT,database='irps_local').render_as_string(hide_password=False)
config={'database_url':database_url('irps_app','app'),'owner_database_url':database_url('irps_owner','owner'),'auth_mode':'local_test','issuer':f'http://127.0.0.1:{API_PORT}/local-issuer','allowed_origins':[f'http://127.0.0.1:{WEB_PORT}'],'audience':'irps-local','cookie_secure':False,'runtime':str(RUNTIME),'ai_enabled':False}
(RUNTIME/'config-local.json').write_text(json.dumps(config,indent=2),encoding='utf-8')
test={**config,'database_url':config['database_url'].replace('/irps_local','/irps_migration_test'),'owner_database_url':config['owner_database_url'].replace('/irps_local','/irps_migration_test'),'testing':True,'rate_limit':10000}
(RUNTIME/'config-test.json').write_text(json.dumps(test,indent=2),encoding='utf-8')
print(json.dumps({'postgres':'18.6','host':'127.0.0.1','port':PORT,'databases':['irps_local','irps_migration_test'],'global_service':False,'credentials':'Geradas somente para este ambiente de testes; mantidas em .runtime ignorada.'}))
