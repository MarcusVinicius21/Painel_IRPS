"""Verify forward migrations twice in a newly created disposable local database."""
import os,sys,json,uuid,subprocess,argparse
from pathlib import Path
from sqlalchemy.engine import make_url
import psycopg
from psycopg import sql
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.config import load_settings

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--evidence-dir',default='.runtime/evidencias/diretriz-v2');args=parser.parse_args()
    evidence=(ROOT/args.evidence_dir).resolve()
    if (ROOT/'.runtime').resolve() not in evidence.parents:raise SystemExit('Use uma pasta de evidências dentro de .runtime.')
    from alembic.config import Config
    from alembic.script import ScriptDirectory
    config_path=Config(str(ROOT/'backend/alembic.ini'));config_path.set_main_option('script_location',str(ROOT/'backend/migrations'))
    expected_head=ScriptDirectory.from_config(config_path).get_current_head()
    settings=load_settings();url=make_url(settings.owner_database_url.get_secret_value())
    if settings.auth_mode!='local_test' or url.host not in ('127.0.0.1','localhost','::1'):
        raise SystemExit('Use somente o PostgreSQL local descartável.')
    name='irps_director_migration_'+uuid.uuid4().hex[:10]
    with psycopg.connect(url.set(database='postgres').render_as_string(hide_password=False).replace('+psycopg',''),autocommit=True) as conn:
        conn.execute(sql.SQL('CREATE DATABASE {} OWNER irps_owner').format(sql.Identifier(name)))
    config=settings.model_dump(mode='json');config.update(database_url=make_url(settings.database_url.get_secret_value()).set(database=name).render_as_string(hide_password=False),owner_database_url=url.set(database=name).render_as_string(hide_password=False))
    path=ROOT/'.runtime/config-director-migration.json';path.write_text(json.dumps(config),encoding='utf-8')
    env={**os.environ,'IRPS_LOCAL_CONFIG':str(path)}
    for _ in range(2):subprocess.run([sys.executable,'-m','alembic','upgrade','head'],cwd=ROOT/'backend',env=env,check=True)
    with psycopg.connect(config['owner_database_url'].replace('+psycopg','')) as conn:
        head=conn.execute('SELECT version_num FROM alembic_version').fetchone()[0]
        tables=conn.execute("SELECT relname,relrowsecurity,relforcerowsecurity FROM pg_class WHERE relname IN ('director_study','irp_draft','irp_operation','national_product_link','item_version','director_progress') ORDER BY relname").fetchall()
        assert head==expected_head and len(tables)==6 and all(r[1] and r[2] for r in tables)
    result={'database':name,'head':head,'fresh_upgrade':True,'second_upgrade_idempotent':True,'rls_forced_tables':[r[0] for r in tables],
        'production_database_used':False,'downgrade_executed':False,'note':'Banco descartável preservado. Migrações append-only não apagam evidências por downgrade.'}
    out=evidence/'migracoes.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
