"""One explicit local monthly pilot, after a verified/restored backup; never imports into PNCP."""
import argparse,hashlib,json,sys
from pathlib import Path
from sqlalchemy.engine import make_url
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.config import load_settings
from app.monthly_prices import import_archive
from monthly_import_support import target,private_path,validate_manifest,backup_gate
from backup_precos_mensais import counts
import psycopg


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--target-database',required=True);p.add_argument('--month',required=True)
    p.add_argument('--manifest',required=True);p.add_argument('--backup-proof',required=True)
    p.add_argument('--first-month',default='2025-10');p.add_argument('--last-month',default='2026-09')
    p.add_argument('--output',default='.runtime/irps-12-meses/latest-import.json');a=p.parse_args()
    s=load_settings();u=make_url(s.owner_database_url.get_secret_value());app=make_url(s.database_url.get_secret_value())
    if s.auth_mode!='operational_local' or u.host not in ('127.0.0.1','localhost') or u.database!=a.target_database or app.database!=u.database or app.host!=u.host:
        raise SystemExit('Confirme o banco operacional local exato. Nenhum banco remoto é aceito.')
    manifests=validate_manifest(json.loads(Path(a.manifest).read_text(encoding='utf-8')),a.month,a.first_month,a.last_month)
    proof=json.loads(private_path(a.backup_proof).read_text(encoding='utf-8'))
    with psycopg.connect(u.render_as_string(hide_password=False).replace('+psycopg','')) as conn:before=counts(conn,s.operator_org_id)
    resources=backup_gate(proof,s,before,sum(m['uncompressed_bytes'] for m in manifests));results=[]
    for m in manifests:
        kind=m['kind'];expected=f"https://repositorio.dados.gov.br/seges/comprasgov/pesquisa_precos/{a.month.replace('-','/')}/{kind}_{a.month.replace('-','_')}.csv.zip"
        if m['url']!=expected or m.get('blocked'):raise SystemExit('Fonte ou tamanho fora do piloto validado.')
        result=import_archive(u.render_as_string(hide_password=False),s.operator_org_id,ROOT/m['path'],kind,a.month,m['sha256'],m['url'],{'archive_bytes':m['bytes'],'uncompressed_bytes':m['uncompressed_bytes'],'source_crc':m['crc'],'source_url':m['url'],'backup_sha256':proof['sha256'],'resource_gate':resources},max_uncompressed_bytes=m['uncompressed_bytes'],max_rows=max(500000,m['uncompressed_bytes']//20))
        results.append(result)
    out=private_path(a.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps([{k:v for k,v in r.items() if k!='rejections'} for r in results]))
