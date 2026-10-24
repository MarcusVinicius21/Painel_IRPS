"""Local-file preview only; never downloads or schedules a catalogue import."""
import csv,hashlib
from pathlib import Path

def allowed_time(local_datetime):
    return local_datetime.weekday()==5 and 8<=local_datetime.hour<12

def preview(path,kind,expected_sha256,old):
    path=Path(path)
    if kind not in ('CATMAT','CATSER') or path.stat().st_size>250_000_000:raise ValueError('Unsupported bounded catalogue')
    with path.open('rb') as source:sha=hashlib.file_digest(source,'sha256').hexdigest()
    if sha!=expected_sha256:raise ValueError('Checksum mismatch')
    code,name,active=('codigoItem','descricaoItem','statusItem') if kind=='CATMAT' else ('codigoServico','nomeServico','statusServico')
    seen=set();counts={'new':0,'changed':0,'unchanged':0}
    with path.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f,delimiter=';')
        if not {code,name,active}.issubset(reader.fieldnames or []):raise ValueError('Missing columns')
        for row in reader:
            key=row[code]
            if not key.isascii() or not key.isdigit() or key in seen or not row[name].strip() or row[active] not in ('True','False'):raise ValueError('Invalid or duplicated catalogue identity')
            seen.add(key);value=(row[name],row[active]=='True')
            counts['new' if key not in old else 'unchanged' if old[key]==value else 'changed']+=1
    if not seen:raise ValueError('Empty catalogue')
    return {'sha256':sha,'kind':kind,'rows':len(seen),**counts,'missing_from_new':len(set(old)-seen),
            'destructive_deletions':0,'automatic_download':False,'rollback':'Previous immutable snapshots remain queryable; no automatic active-snapshot rollback'}
