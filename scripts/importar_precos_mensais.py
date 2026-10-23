"""One explicit local monthly pilot, after a verified/restored backup; never imports into PNCP."""
import argparse,hashlib,json,sys
from pathlib import Path
from sqlalchemy.engine import make_url
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.config import load_settings
from app.monthly_prices import import_archive


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--target-database',required=True);p.add_argument('--month',required=True)
    p.add_argument('--manifest',required=True);p.add_argument('--backup-proof',required=True);a=p.parse_args()
    s=load_settings();u=make_url(s.owner_database_url.get_secret_value());app=make_url(s.database_url.get_secret_value())
    if s.auth_mode!='operational_local' or u.host not in ('127.0.0.1','localhost') or u.database!=a.target_database or app.database!=u.database or app.host!=u.host:
        raise SystemExit('Confirme o banco operacional local exato. Nenhum banco remoto é aceito.')
    if a.month!='2026-09':raise SystemExit('Este piloto autoriza somente setembro de 2026. Valide outro lote antes de ampliar.')
    proof=json.loads(Path(a.backup_proof).read_text(encoding='utf-8'));backup=ROOT/'.runtime/urgente-precos/backups/antes-mensais.dump'
    with backup.open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
    if not proof.get('restored_to_disposable_database') or proof['sha256']!=sha:raise SystemExit('Backup restaurado e íntegro é obrigatório.')
    manifests=json.loads(Path(a.manifest).read_text(encoding='utf-8'));results=[]
    for m in manifests:
        kind=m['kind'];expected=f'https://repositorio.dados.gov.br/seges/comprasgov/pesquisa_precos/2026/09/{kind}_2026_09.csv.zip'
        if m['url']!=expected or m.get('blocked'):raise SystemExit('Fonte ou tamanho fora do piloto validado.')
        result=import_archive(u.render_as_string(hide_password=False),s.operator_org_id,ROOT/m['path'],kind,a.month,m['sha256'],m['url'],{'archive_bytes':m['bytes'],'uncompressed_bytes':m['uncompressed_bytes'],'source_crc':m['crc'],'source_url':m['url']})
        results.append(result)
    out=ROOT/'docs/IRPS_URGENTE_HISTORICO_PRECOS/U3_IMPORTACAO.json';out.write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps([{k:v for k,v in r.items() if k!='rejections'} for r in results]))
