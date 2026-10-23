"""Create a NEW loopback operational DB; never seed, reset, copy or drop data."""
import argparse,json,os,secrets,subprocess,sys,uuid
from pathlib import Path
import psycopg
from psycopg import sql
from sqlalchemy.engine import make_url

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.operational import PASSWORDS

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--credentials-from',required=True,help='Private local JSON; only connection credentials are reused.')
    parser.add_argument('--api-port',type=int,default=5295)
    parser.add_argument('--frontend-port',type=int,default=5296)
    args=parser.parse_args()
    runtime=ROOT/'.runtime/operacional-local';runtime.mkdir(parents=True,exist_ok=True)
    if os.name=='nt':
        user=subprocess.check_output(['whoami'],text=True).strip()
        subprocess.run(['icacls',str(runtime),'/inheritance:r','/grant:r',user+':(OI)(CI)F','SYSTEM:(OI)(CI)F'],check=True,stdout=subprocess.DEVNULL)
    config=runtime/'config.json'
    if config.exists():
        print('Configuração operacional existente preservada. Nenhum banco foi recriado.')
        return
    credentials=Path(args.credentials_from).resolve()
    if (ROOT/'.runtime').resolve() not in credentials.parents:raise SystemExit('Use configuração privada dentro de .runtime.')
    prior=json.loads(credentials.read_text(encoding='utf-8-sig'))
    owner=make_url(prior['owner_database_url']);app=make_url(prior['database_url'])
    if owner.host not in ('127.0.0.1','localhost','::1') or app.host!=owner.host:raise SystemExit('Somente PostgreSQL local.')
    dbname='irps_operacional_local_'+uuid.uuid4().hex[:10]
    with psycopg.connect(owner.set(database='postgres').render_as_string(hide_password=False).replace('+psycopg',''),autocommit=True) as conn:
        conn.execute(sql.SQL('CREATE DATABASE {} OWNER {}').format(sql.Identifier(dbname),sql.Identifier(owner.username)))
    password=secrets.token_urlsafe(32);org=str(uuid.uuid4());actor=str(uuid.uuid4())
    data={'database_url':app.set(database=dbname).render_as_string(hide_password=False),
          'owner_database_url':owner.set(database=dbname).render_as_string(hide_password=False),
          'auth_mode':'operational_local','issuer':'irps:consormulti:operacional:local','audience':'irps-operacional-local',
          'operator_org_id':org,'operator_actor_id':actor,'operator_password_hash':PASSWORDS.hash(password),
          'cookie_secure':False,'allowed_origins':[f'http://127.0.0.1:{args.frontend_port}'],
          'runtime':str(runtime),'ai_enabled':False,'testing':False,'rate_limit':600,'token_seconds':3600}
    config.write_text(json.dumps(data,indent=2),encoding='utf-8')
    (runtime/'acesso-privado.json').write_text(json.dumps({'password':password},indent=2),encoding='utf-8')
    env={**os.environ,'IRPS_LOCAL_CONFIG':str(config)}
    subprocess.run([sys.executable,'-m','alembic','upgrade','head'],cwd=ROOT/'backend',env=env,check=True)
    with psycopg.connect(data['owner_database_url'].replace('+psycopg','')) as conn:
        conn.execute("SELECT set_config('irps.org_id',%s,true)",(org,))
        conn.execute("INSERT INTO organization(id,name,kind) VALUES (%s,'CONSORMULTI','consortium')",(org,))
        conn.execute("INSERT INTO actor(id,issuer,subject,name) VALUES (%s,%s,'consormulti-operador','Operador CONSORMULTI')",(actor,data['issuer']))
        conn.execute("INSERT INTO membership(org_id,actor_id,role) VALUES (%s,%s,'planner')",(org,actor))
        conn.execute('REVOKE INSERT,UPDATE,DELETE ON membership FROM irps_app')
        assert conn.execute('SELECT count(*) FROM procurement_fact').fetchone()[0]==0
        assert conn.execute('SELECT count(*) FROM item_version').fetchone()[0]==0
    result={'database':dbname,'synthetic_seed_executed':False,'existing_data_modified':False,'configuration':str(config.relative_to(ROOT)),
            'application_url':f'http://127.0.0.1:{args.frontend_port}','api_port':args.api_port,'migration_head':'0014'}
    (runtime/'bootstrap-evidence.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result))

if __name__=='__main__':main()
