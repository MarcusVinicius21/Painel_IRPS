"""Record one reviewed FCP commit locally; preserve the paused M/D/X ledger."""
import argparse,hashlib,json,re,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='f35074827b0f9b5b5530bf15db68cf67300179af'


def git(*args):return subprocess.check_output(['git','-C',str(ROOT),*args]).decode('utf-8').strip()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('task');p.add_argument('title');p.add_argument('files',nargs='+');a=p.parse_args()
    if not re.fullmatch(r'FCP0[1-9]',a.task):raise ValueError('INVALID_TASK')
    if git('branch','--show-current')!='feat/cobertura-municipal-12m-2026-10-23':raise ValueError('UNEXPECTED_BRANCH')
    subprocess.run(['git','merge-base','--is-ancestor',BASE,'HEAD'],cwd=ROOT,check=True)
    if git('diff','--cached','--name-only'):raise ValueError('PREEXISTING_STAGE')
    previous=[]
    for line in git('log','--reverse','--format=%H%x09%s',BASE+'..HEAD').splitlines():
        sha,title=line.split('\t',1);match=re.match(r'^irps\((FCP0[1-9])\): ',title)
        if match:previous.append({'id':match[1],'sha':sha})
    if a.task!=f'FCP{len(previous)+1:02}':raise ValueError('PRESERVE_SEQUENTIAL_QUEUE')
    report='docs/implementacao/foco-consormulti/'+a.task+'.md'
    text=(ROOT/report).read_text(encoding='utf-8')
    if not re.search(r'^Status: (PASS|PARTIAL|BLOCKED)$',text,re.M):raise ValueError('REPORT_STATUS_REQUIRED')
    for item in json.loads((ROOT/'docs/validacao/integridade-v4.json').read_text())['modules']:
        if hashlib.sha256((ROOT/'backend/irps_core'/item['file']).read_bytes()).hexdigest()!=item['sha256']:raise ValueError('V4_CHANGED')
    if git('diff',BASE,'--','backend/irps_core','docs/design/referencias-irps'):raise ValueError('PROTECTED_FILES_CHANGED')
    files=sorted(set(a.files+[report]))
    for name in files:
        path=(ROOT/name).resolve()
        if ROOT not in path.parents or re.search(r'(^|/)(\.runtime|\.venv|node_modules)/|\.(zip|dump|log|raw|png|jpg)$',name,re.I):raise ValueError('UNSUITABLE_FILE')
        body=path.read_bytes()
        if len(body)>2_000_000:raise ValueError('OVERSIZE_FILE')
        for pattern in [rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY',rb'\bgh[pousr]_[A-Za-z0-9]{30,}',
            rb'\bsk-(?:proj-)?[A-Za-z0-9_-]{32,}',rb'\bAIza[A-Za-z0-9_-]{30,}',
            rb'(?i)(?:postgres(?:ql)?(?:\+psycopg)?|https?)://[^\s:/<>]+:[^\s@/<>]{8,}@']:
            if re.search(pattern,body):raise ValueError('POSSIBLE_SECRET: '+name)
    subprocess.run(['git','diff','--check'],cwd=ROOT,check=True)
    subprocess.run(['git','add','--',*files],cwd=ROOT,check=True)
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True)
    subprocess.run(['git','commit','-m',f'irps({a.task}): {a.title}'],cwd=ROOT,check=True)
    previous.append({'id':a.task,'sha':git('rev-parse','HEAD')})
    for row in previous:
        content=git('show',row['sha']+':docs/implementacao/foco-consormulti/'+row['id']+'.md')
        row['status']=re.search(r'^Status: (PASS|PARTIAL|BLOCKED)$',content,re.M)[1]
    folder=ROOT/'.runtime/irps-fcp';folder.mkdir(exist_ok=True)
    (folder/'ledger.json').write_text(json.dumps(previous,indent=2),encoding='utf-8')
    (folder/'STATUS_GERAL.json').write_text(json.dumps({'current_task':f'FCP{len(previous)+1:02}' if len(previous)<9 else None,
        'base_sha':BASE,'legacy_queue':'PAUSED_AND_PRESERVED','completed':previous,
        'updated_at':datetime.now(timezone.utc).isoformat()},indent=2),encoding='utf-8')
    print(previous[-1]['sha'])


if __name__=='__main__':main()
