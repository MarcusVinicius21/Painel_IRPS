"""Inspect changed and untracked source files without printing suspected secret values."""
import hashlib,json,re,subprocess
from pathlib import Path,PurePosixPath
ROOT=Path(__file__).resolve().parents[1]
def git(*args):return subprocess.check_output(['git','-C',str(ROOT),*args]).decode('utf-8').splitlines()
rules={
 'private_key':rb'-----BEGIN (?:RSA |EC |OPENSSH |DSA |ENCRYPTED )?PRIVATE KEY-----',
 'github_token':rb'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{50,})\b',
 'openai_key':rb'\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{32,}\b',
 'google_key':rb'\bAIza[A-Za-z0-9_-]{30,}\b',
 'credential_uri':rb'(?i)(?:postgres(?:ql)?(?:\+psycopg)?|mongodb(?:\+srv)?|redis|https?)://[^\s:/<>]+:[^\s@/<>]{8,}@',
 'jwt_literal':rb'\beyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\b'}
if __name__=='__main__':
 files=sorted(set(git('diff','--name-only','--diff-filter=ACMR')+git('ls-files','--others','--exclude-standard')))
 findings=[]
 for name in files:
  p=PurePosixPath(name);path=ROOT/name
  if set(p.parts)&{'.runtime','.venv','node_modules','uploads','exports','_tools'} or p.name.startswith('.env') and p.name!='.env.example':
   findings.append({'file':name,'rule':'forbidden_path'});continue
  if not path.is_file():continue
  data=path.read_bytes()
  if len(data)>5*1024*1024:findings.append({'file':name,'rule':'large_file_review'})
  for rule,pattern in rules.items():
   for m in re.finditer(pattern,data):findings.append({'file':name,'line':data[:m.start()].count(b'\n')+1,'rule':rule})
 expected={m['file']:m['sha256'] for m in json.loads((ROOT/'docs/validacao/integridade-v4.json').read_text(encoding='utf-8'))['modules']}
 current={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'backend/irps_core').glob('*.py')}
 result={'scope':'local_diff_and_untracked_nonignored','files':files,'findings':findings,'v4_unchanged':current==expected,'secret_values_printed':False}
 out=ROOT/'.runtime/evidencias/diretriz-v2/auditoria-local.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2))
 raise SystemExit(bool(findings) or current!=expected)
