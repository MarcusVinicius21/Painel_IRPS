"""Consistent dump and actual restore into a NEW disposable DB, never overwrite one."""
import argparse,hashlib,json,os,subprocess,sys,uuid
from datetime import datetime,timezone
from pathlib import Path
import psycopg
from psycopg import sql
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.config import load_settings
from monthly_import_support import target,private_path,digest

def counts(conn,org):
    conn.execute("SELECT set_config('irps.org_id',%s,true)",(str(org),))
    return {t:conn.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in ['national_catalogue_entry','procurement_fact','price_monthly_snapshot','price_monthly_record']}

def backup(name,output):
    s=load_settings();u=target(s,name);out=private_path(output);out.parent.mkdir(parents=True,exist_ok=True)
    dump=out.with_suffix('.dump')
    if dump.exists() or out.exists():raise ValueError('Use a new backup path; preserve prior evidence')
    env={**os.environ,'PGPASSWORD':u.password or ''};opts=['-h',u.host,'-p',str(u.port),'-U',u.username];bin=ROOT/'_tools/postgresql/bin'
    with psycopg.connect(u.render_as_string(hide_password=False).replace('+psycopg','')) as c:
        c.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY');before=counts(c,s.operator_org_id)
    subprocess.run([str(bin/'pg_dump.exe'),*opts,'-d',name,'-Fc','--no-owner','--no-acl','-f',str(dump)],env=env,check=True,capture_output=True)
    restored='irps_annual_restore_'+uuid.uuid4().hex[:10]
    with psycopg.connect(u.set(database='postgres').render_as_string(hide_password=False).replace('+psycopg',''),autocommit=True) as c:c.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(restored)))
    subprocess.run([str(bin/'pg_restore.exe'),*opts,'-d',restored,'--no-owner','--no-acl',str(dump)],env=env,check=True,capture_output=True)
    with psycopg.connect(u.set(database=restored).render_as_string(hide_password=False).replace('+psycopg','')) as c:after=counts(c,s.operator_org_id)
    with psycopg.connect(u.render_as_string(hide_password=False).replace('+psycopg','')) as c:current=counts(c,s.operator_org_id)
    if before!=after or current!=before:raise ValueError('Concurrent change or restore count mismatch')
    result={'created_at':datetime.now(timezone.utc).isoformat(),'backup_path':str(dump.relative_to(ROOT)),'sha256':digest(dump),'counts':after,'restored_to_disposable_database':True,'target_fingerprint':hashlib.sha256((name+':'+str(s.operator_org_id)).encode()).hexdigest()}
    out.write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({'backup_restored':True,'bytes':dump.stat().st_size,'counts':after}))
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--target-database',required=True);p.add_argument('--output',required=True);a=p.parse_args();backup(a.target_database,a.output)
