from pathlib import Path
import subprocess,hashlib,json,zipfile,re,shutil,sys
sys.path.insert(0,'scripts')
from auditar_diff_local import rules
root=Path('.').resolve();report=root/'docs/IRPS_REFINAMENTO_PIXEL_PERFECT';runtime=root/'.runtime/pixel-perfect'
# Refresh incremental patch after all source edits. Baseline bytes are preserved outside the archive.
base=json.loads((runtime/'baseline.json').read_text());changed=[]
for folder in ('frontend','backend','scripts'):
 for p in (root/folder).rglob('*'):
  if not p.is_file() or p.suffix not in ('.tsx','.ts','.css','.py','.cjs') or any(x in ('node_modules','__pycache__','.venv') for x in p.parts):continue
  n=p.relative_to(root).as_posix()
  if base.get(n)!=hashlib.sha256(p.read_bytes()).hexdigest():changed.append(n)
# Include precisely this round's source overlay and audit documents, not the whole dirty checkout.
files={f'IRPS_REFINAMENTO/{p.relative_to(report).as_posix()}':p for p in report.rglob('*') if p.is_file()}
for n in changed:files['arquivos/'+n]=root/n
for n in ('plan.md','TODO.md'):files['contexto-local/'+n]=root/n
for p in (runtime/'browser').glob('*assertions.json'):files['IRPS_REFINAMENTO/evidencias/geometria/'+p.name]=p
findings=[]
for name,p in files.items():
 if any(part in {'.env','.git','node_modules','.venv','uploads','exports'} for part in Path(name).parts):findings.append({'file':name,'rule':'forbidden_path'})
 if p.suffix.lower() in {'.png','.jpg','.pdf','.docx'}:continue
 data=p.read_bytes()
 for rule,pattern in rules.items():
  if re.search(pattern,data):findings.append({'file':name,'rule':rule})
core={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'backend/irps_core').glob('*.py')}
unchanged=all(base['backend/irps_core/'+n]==sha for n,sha in core.items())
security={'scope':'arquivos do pacote e diff local; padrões conhecidos, não certificação absoluta','findings':findings,'v4_unchanged':unchanged,'forbidden_files_included':False,'credentials_or_sessions_included':False,'source_files_this_round':changed,'production_actions':False}
(report/'SEGURANCA.json').write_text(json.dumps(security,ensure_ascii=False,indent=2),encoding='utf-8')
if findings or not unchanged:raise SystemExit('Pacote bloqueado: consulte SEGURANCA.json sem valores secretos.')
files['IRPS_REFINAMENTO/SEGURANCA.json']=report/'SEGURANCA.json'
manifest={n:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for n,p in sorted(files.items())}
(report/'MANIFESTO.json').write_text(json.dumps({'scope':'Revisão incremental, aplicar somente após comparar o estado local. Não é instalador nem projeto independente.','files':manifest},ensure_ascii=False,indent=2),encoding='utf-8')
files['IRPS_REFINAMENTO/MANIFESTO.json']=report/'MANIFESTO.json'
out=root/'output/IRPS_REFINAMENTO_PIXEL_PERFECT_2026-10-21.zip';out.parent.mkdir(exist_ok=True)
# A new review archive, distinct from all previous deliverables.
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for n,p in sorted(files.items()):z.write(p,n)
with zipfile.ZipFile(out) as z:
 assert z.testzip() is None
 for n,v in manifest.items():assert hashlib.sha256(z.read(n)).hexdigest()==v['sha256']
result={'zip':str(out),'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'members':len(files),'findings':len(findings),'v4_unchanged':unchanged}
(runtime/'pacote.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
