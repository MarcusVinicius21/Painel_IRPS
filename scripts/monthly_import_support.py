"""Fail-closed local campaign gates; raw files and backup proofs remain private."""
import hashlib,json,re,shutil,zipfile
from datetime import datetime,timezone
from pathlib import Path
from sqlalchemy.engine import make_url

ROOT=Path(__file__).resolve().parents[1]
OFFICIAL='https://repositorio.dados.gov.br/seges/comprasgov/pesquisa_precos/'

def private_path(value):
    path=(ROOT/value).resolve()
    if (ROOT/'.runtime').resolve() not in path.parents:raise ValueError('Use a private .runtime path')
    return path

def digest(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def target(settings,name):
    owner=make_url(settings.owner_database_url.get_secret_value());app=make_url(settings.database_url.get_secret_value())
    if settings.auth_mode!='operational_local' or owner.host not in ('127.0.0.1','localhost') or owner.database!=name or app.database!=name or app.host!=owner.host:
        raise ValueError('Select the exact existing loopback operational database')
    return owner

def validate_manifest(items,month,first='2025-10',last='2026-09'):
    if not re.fullmatch(r'\d{4}-(0[1-9]|1[0-2])',month) or not first<=month<=last:raise ValueError('Month outside approved campaign')
    if len(items)!=2 or {x['kind'] for x in items}!={'material','servico'}:raise ValueError('Both official kinds required exactly once')
    for item in items:
        expected=OFFICIAL+month.replace('-','/')+'/'+item['kind']+'_'+month.replace('-','_')+'.csv.zip'
        if item['url']!=expected or item.get('blocked'):raise ValueError('Official source scope mismatch')
        path=private_path(item['path'])
        if path.stat().st_size!=item['bytes'] or digest(path)!=item['sha256']:raise ValueError('Downloaded file integrity mismatch')
        with zipfile.ZipFile(path) as archive:
            entries=archive.infolist()
            if len(entries)!=1 or not entries[0].filename.endswith('.csv') or archive.testzip():raise ValueError('Invalid archive or CRC')
            if entries[0].file_size!=item['uncompressed_bytes']:raise ValueError('Uncompressed size mismatch')
    return items

def backup_gate(proof,settings,counts,uncompressed_bytes):
    backup=private_path(proof['backup_path'])
    if not proof.get('restored_to_disposable_database') or digest(backup)!=proof['sha256']:raise ValueError('Restored matching backup required')
    fingerprint=hashlib.sha256((make_url(settings.owner_database_url.get_secret_value()).database+':'+str(settings.operator_org_id)).encode()).hexdigest()
    if proof.get('target_fingerprint')!=fingerprint or proof['counts']!=counts:raise ValueError('Backup does not represent the current target')
    age=(datetime.now(timezone.utc)-datetime.fromisoformat(proof['created_at'])).total_seconds()
    if age<0 or age>21600:raise ValueError('Refresh and restore the backup before this import')
    # Conservative allowance for staging, JSON storage, indexes, WAL and another backup.
    required=uncompressed_bytes*15+backup.stat().st_size*2+1024**3
    if shutil.disk_usage(ROOT).free<required:raise ValueError('Insufficient measured disk margin')
    return {'free_bytes':shutil.disk_usage(ROOT).free,'required_margin_bytes':required,'expansion_factor':15}
