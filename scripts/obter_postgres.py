"""Binários oficiais locais ao projeto. Não instala/ativa serviços do Windows."""
from pathlib import Path,PurePosixPath
from urllib.request import urlopen
from urllib.parse import urlsplit,urlunsplit
import zipfile,hashlib,json,time
APP=Path(__file__).resolve().parent.parent
TOOLS=APP/'_tools';TOOLS.mkdir(exist_ok=True)
archive=TOOLS/'postgresql-18.6-windows.zip'
url='https://sbp.enterprisedb.com/getfile.jsp?fileid=1260609'
start=time.monotonic()
if not archive.exists():
 with urlopen(url,timeout=60) as r,archive.open('xb') as f:
  actual=urlsplit(r.url);assert actual.hostname.endswith(('enterprisedb.com','amazonaws.com'))
  total=0
  while block:=r.read(1024*1024):
   total+=len(block)
   if total>600*1024*1024:raise ValueError('Arquivo excede limite local')
   f.write(block)
   if total%(64*1024*1024)==0:print(json.dumps({'downloaded_mb':total//1024//1024}),flush=True)
# Pin local da distribuição obtida por HTTPS nesta rodada; não é checksum publicado pelo fornecedor.
expected_sha256='e2246ba91d22345bc3d017586c09ede52d9df180b1eeb480f050445f1cad84e2'
with archive.open('rb') as f:
 if hashlib.file_digest(f,'sha256').hexdigest()!=expected_sha256:raise ValueError('Distribuição difere do binário validado nesta rodada.')
target=TOOLS/'postgresql';target.mkdir(exist_ok=True)
with zipfile.ZipFile(archive) as z:
 selected=[i for i in z.infolist() if i.filename.startswith(('pgsql/bin/','pgsql/lib/','pgsql/share/')) or i.filename in ('pgsql/LICENSE','pgsql/COPYRIGHT')]
 assert sum(i.file_size for i in selected)<1024*1024*1024
 for i in selected:
  rel=PurePosixPath(i.filename);assert '..' not in rel.parts and not rel.is_absolute()
  if i.is_dir():continue
  p=target/Path(*rel.parts[1:]);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(i))
result={'origin_page':'https://www.enterprisedb.com/download-postgresql-binaries','official_reference':'https://www.postgresql.org/download/windows/','download_url':url,'bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'version':'18.6','extracted_files':len(selected),'local_directory':'_tools/postgresql','global_service_installed_or_started':False,'seconds':round(time.monotonic()-start,2),'licence':'PostgreSQL License; https://www.postgresql.org/about/licence/','vendor_checksum_comparison':'Sem checksum separado fornecido nesta coleta; registrado digest local e origem HTTPS oficial.'}
(APP/'.runtime/postgres-binarios.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:result[k] for k in ('version','bytes','extracted_files','seconds','global_service_installed_or_started')}),flush=True)
