"""Read immutable official archives; export aggregate quality only, without supplier IDs."""
import csv,io,json,zipfile,hashlib,argparse
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
UNIT_FIELDS=('nome_unidade_fornecimento','nome_unidade_medida','sigla_unidade_medida')

def quality(rows):
    total=missing=alternate=0;suppliers=set();different=0
    for row in rows:
        total+=1
        candidates=[str(row.get(k) or '').strip() for k in UNIT_FIELDS]
        # Mirrors original precedence; whitespace-only values must remain flagged.
        selected=next((row.get(k) for k in UNIT_FIELDS if row.get(k)),None)
        if not str(selected or '').strip():
            missing+=1
            if str(row.get('sigla_unidade_fornecimento') or '').strip():alternate+=1
            if row.get('ni_fornecedor'):suppliers.add(row['ni_fornecedor'])
        if len(set(x for x in candidates if x))>1:different+=1
    return dict(source_rows=total,unknown_unit=missing,unknown_with_supply_abbreviation=alternate,
                suppliers_with_unknown_unit=len(suppliers),different_unit_fields=different,
                recovered_units=0,algorithm='source-unit-audit-v1',source_unchanged=True)

def audit(manifest):
    files=json.loads(manifest.read_text(encoding='utf-8'))['files']
    september={x['kind']:x for x in json.loads((ROOT/'docs/IRPS_URGENTE_HISTORICO_PRECOS/U3_INTEGRIDADE_ZIPS.json').read_text(encoding='utf-8'))}
    result=[]
    for f in files:
        source=f if f.get('path') else september[f['kind']]
        path=ROOT/source['path']
        with path.open('rb') as stream:sha=hashlib.file_digest(stream,'sha256').hexdigest()
        assert sha==source['sha256']
        with zipfile.ZipFile(path) as z:
            assert z.testzip() is None and len(z.infolist())==1
            with z.open(z.infolist()[0]) as raw:
                reader=csv.DictReader(io.TextIOWrapper(raw,encoding='utf-8-sig'),delimiter=';')
                fields=reader.fieldnames;summary=quality(reader)
        assert summary['source_rows']==f['source_rows']
        result.append(dict(month=f['month'],kind=f['kind'],sha256=sha,url=f['url'],unit_columns=[k for k in fields if 'unidade' in k],**summary))
        print(f['month'],f['kind'],summary['unknown_unit'],flush=True)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);args=p.parse_args()
    output=(ROOT/args.output).resolve();assert (ROOT/'.runtime').resolve() in output.parents
    output.write_text(json.dumps(audit(ROOT/'.runtime/irps-12-meses/sources/manifest.json'),ensure_ascii=False,indent=2),encoding='utf-8')
