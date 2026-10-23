"""Download fixed official CNBS snapshots with bounded retries, hashes and reconciliation."""
import csv,hashlib,json,time
from datetime import datetime,timezone
from pathlib import Path
import httpx

ROOT=Path(__file__).resolve().parents[1]
DIRECTORY=ROOT/'.runtime/catalogo-historico-real/fontes'
BASE='https://repositorio.dados.gov.br/seges/comprasgov/catalogo_cnbs/'

def download(name):
    DIRECTORY.mkdir(parents=True,exist_ok=True)
    path=DIRECTORY/name;manifest=DIRECTORY/(name+'.download.json')
    if path.exists() and manifest.exists():
        previous=json.loads(manifest.read_text(encoding='utf-8'))
        with path.open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
        if actual==previous['sha256']:return previous
        raise RuntimeError('Arquivo existente diverge do manifesto; preserve-o para revisão.')
    for attempt in range(3):
        try:
            digest=hashlib.sha256();size=0
            with httpx.stream('GET',BASE+name,timeout=httpx.Timeout(120,connect=20),follow_redirects=False) as r:
                if r.status_code in (429,503):raise RuntimeError('Fonte pediu pausa; não repetir automaticamente.')
                r.raise_for_status()
                metadata={k:r.headers.get(k) for k in ['last-modified','etag','content-length','content-type','date']}
                with path.with_suffix(path.suffix+'.part').open('wb') as f:
                    for chunk in r.iter_bytes(1024*1024):
                        size+=len(chunk)
                        if size>200*1024*1024:raise RuntimeError('Limite de arquivo oficial excedido.')
                        digest.update(chunk);f.write(chunk)
                if metadata['content-length'] and size!=int(metadata['content-length']):raise RuntimeError('Download incompleto.')
            path.with_suffix(path.suffix+'.part').replace(path)
            result={'source_url':BASE+name,'producer':'Secretaria de Gestão e Inovação / Compras.gov.br',
                'discovery_url':'https://www.gov.br/compras/pt-br/cidadao/portal-de-dados-abertos',
                'consulted_at':datetime.now(timezone.utc).isoformat(),'sha256':digest.hexdigest(),'bytes':size,'http_status':200,
                'http_metadata':metadata,'path':str(path.relative_to(ROOT))}
            manifest.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');return result
        except httpx.HTTPError:
            if attempt==2:raise
            time.sleep(5*(attempt+1))

def validate(path,kind):
    code_key,name_key,state_key=('codigoItem','descricaoItem','statusItem') if kind=='CATMAT' else ('codigoServico','nomeServico','statusServico')
    seen=set();active=inactive=0;rejects=[];duplicates=[]
    with path.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f,delimiter=';');headers=reader.fieldnames
        if not {code_key,name_key,state_key}.issubset(headers or []):raise ValueError('Cabeçalhos oficiais não reconhecidos.')
        for number,row in enumerate(reader,2):
            code=row.get(code_key,'')
            if None in row or any(v is None for v in row.values()) or not code.isascii() or not code.isdigit() or not row[name_key].strip() or row[state_key] not in ('True','False'):
                rejects.append({'line':number,'reason':'invalid_columns_code_name_or_state'});continue
            if code in seen:duplicates.append({'line':number,'code':code});continue
            seen.add(code);active+=row[state_key]=='True';inactive+=row[state_key]=='False'
    return {'encoding':'UTF-8','delimiter':';','headers':headers,'source_records':active+inactive+len(rejects)+len(duplicates),
        'unique_valid_records':len(seen),'active':active,'inactive':inactive,'rejected':rejects,'duplicates':duplicates,
        'complete':bool(seen and not rejects and not duplicates)}

def main():
    readme=download('LEIAME.md');result={}
    for kind,name in [('CATMAT','catmat.csv'),('CATSER','catser.csv')]:
        metadata=download(name);result[kind]={**metadata,**validate(DIRECTORY/name,kind),'readme_sha256':readme['sha256']}
        print(json.dumps({'kind':kind,'records':result[kind]['source_records'],'complete':result[kind]['complete'],'sha256':metadata['sha256']}),flush=True)
        if not result[kind]['complete']:raise RuntimeError('Snapshot requer reconciliação; não importar como completo.')
    (DIRECTORY/'MANIFESTO.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__':main()
