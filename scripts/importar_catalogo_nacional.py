"""Import only into the explicitly configured local PostgreSQL database."""
import argparse,sys,json,os,subprocess,hashlib,uuid
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlparse
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from app.config import load_settings
from app.national_catalogue import import_csv
from app.db import encoded

def operational_import(settings,path,kind,manifest_path,target_database):
    from sqlalchemy.engine import make_url
    from sqlalchemy import create_engine,text
    from app.operational import validate_local
    root=Path(__file__).resolve().parents[1];validate_local(settings)
    owner=make_url(settings.owner_database_url.get_secret_value());app=make_url(settings.database_url.get_secret_value())
    if not target_database or owner.database!=target_database or app.database!=target_database:
        raise SystemExit('Confirme explicitamente o nome exato do banco operacional.')
    if owner.host not in ('127.0.0.1','localhost','::1') or owner.host!=app.host or owner.port!=app.port:
        raise SystemExit('O banco proprietário e o aplicativo devem usar o mesmo PostgreSQL local.')
    manifest=json.loads(Path(manifest_path).read_text(encoding='utf-8'))[kind]
    expected_url='https://repositorio.dados.gov.br/seges/comprasgov/catalogo_cnbs/'+('catmat.csv' if kind=='CATMAT' else 'catser.csv')
    if manifest.get('source_url')!=expected_url or not manifest.get('complete') or manifest.get('rejected') or manifest.get('duplicates'):
        raise SystemExit('Manifesto oficial não reconciliado. Não importar como completo.')
    with Path(path).open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
    if digest!=manifest['sha256']:raise SystemExit('O arquivo não corresponde ao manifesto.')
    engine=create_engine(owner,hide_parameters=True)
    with engine.connect() as conn:
        count=conn.execute(text('SELECT count(*) FROM actor')).scalar_one()
        identity=conn.execute(text("SELECT a.id,m.org_id FROM actor a JOIN membership m ON m.actor_id=a.id WHERE a.subject='consormulti-operador' AND a.active AND m.active")).mappings().all()
        if count!=1 or len(identity)!=1 or str(identity[0]['id'])!=settings.operator_actor_id or str(identity[0]['org_id'])!=settings.operator_org_id:
            raise SystemExit('O banco não corresponde à identidade operacional única configurada.')
    engine.dispose()
    private=root/'.runtime/catalogo-historico-real/backups';private.mkdir(parents=True,exist_ok=True)
    if os.name=='nt':
        user=subprocess.check_output(['whoami'],text=True).strip()
        subprocess.run(['icacls',str(private),'/inheritance:r','/grant:r',user+':(OI)(CI)F','SYSTEM:(OI)(CI)F'],check=True,stdout=subprocess.DEVNULL)
    backup=private/('antes-'+kind.lower()+'-'+uuid.uuid4().hex[:10]+'.dump')
    bin_dir=root/'_tools/postgresql/bin'
    env={**os.environ,'PGPASSWORD':owner.password or ''}
    subprocess.run([str(bin_dir/'pg_dump.exe'),'-h',owner.host,'-p',str(owner.port),'-U',owner.username,'-d',target_database,'-Fc','--no-owner','--no-acl','-f',str(backup)],env=env,check=True,capture_output=True)
    toc=subprocess.run([str(bin_dir/'pg_restore.exe'),'--list',str(backup)],check=True,capture_output=True)
    if not toc.stdout:raise SystemExit('Backup não pôde ser verificado.')
    with backup.open('rb') as f:backup_sha=hashlib.file_digest(f,'sha256').hexdigest()
    origin=json.dumps({'official_snapshot':True,**{k:v for k,v in manifest.items() if k not in ('path','headers')},'snapshot_version':manifest['http_metadata'].get('last-modified'),'reconciled':True},ensure_ascii=False)
    result=import_csv(owner.render_as_string(hide_password=False),path,kind,origin,
        expected_sha256=manifest['sha256'],expected_records=manifest['unique_valid_records'])
    result.update(kind=kind,source_url=manifest['source_url'],source_records=manifest['source_records'],complete=result['rows']==manifest['unique_valid_records'],backup={'file':str(backup.relative_to(root)),'sha256':backup_sha,'toc_verified':True,'bytes':backup.stat().st_size},imported_at=datetime.now(timezone.utc).isoformat())
    report=root/'docs/IRPS_CATALOGO_HISTORICO_REAL';report.mkdir(parents=True,exist_ok=True)
    (report/('IMPORTACAO_'+kind+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('kind',choices=['CATMAT','CATSER']);p.add_argument('path');p.add_argument('--manifest');p.add_argument('--target-database');args=p.parse_args()
    s=load_settings();url=s.owner_database_url.get_secret_value()
    if s.auth_mode=='operational_local':
        if not args.manifest:raise SystemExit('O modo operacional exige manifesto oficial e banco-alvo explícito.')
        print(encoded(operational_import(s,args.path,args.kind,args.manifest,args.target_database)));sys.exit(0)
    if s.auth_mode!='local_test' or urlparse(url.replace('+psycopg','')).hostname not in ('127.0.0.1','localhost','::1'):
        raise SystemExit('A importação desta rodada exige banco PostgreSQL local de testes.')
    print(encoded(import_csv(url,args.path,args.kind)))
