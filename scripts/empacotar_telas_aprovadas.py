"""Package the local review with explicit evidence, immutable baseline checks and no runtime secrets."""
from pathlib import Path
import difflib,hashlib,json,re,subprocess,zipfile
from auditar_diff_local import rules

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'.runtime/sete-telas'
DOC=ROOT/'docs/IRPS_7_TELAS_APROVADAS'


def git(*args):
    return subprocess.check_output(['git','-C',str(ROOT),*args])


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    before=json.loads((RUN/'estado-inicial.json').read_text(encoding='utf-8'))
    branch=git('branch','--show-current').decode().strip();head=git('rev-parse','HEAD').decode().strip()
    if branch!=before['branch'] or head!=before['head']:raise SystemExit('Branch ou HEAD divergem da auditoria inicial.')
    core={p.name:sha(p.read_bytes()) for p in (ROOT/'backend/irps_core').glob('*.py')}
    if core!=before['v4']:raise SystemExit('Núcleo V4 diverge do inventário inicial.')
    if any(not (ROOT/p).is_file() for p in before['files']):raise SystemExit('Há arquivo preexistente ausente; revise antes de empacotar.')
    evidence=DOC/'evidencias';evidence.mkdir(exist_ok=True)
    names=['python-entrega.xml','python-entrega.txt','python-documentos-humanizacao.xml','python-documentos-humanizacao.txt',
           'build-entrega.txt','migracoes.json','dados-verificados.json','dependencias-python.json','dependencias-frontend.json']
    for name in names:(evidence/name).write_bytes((RUN/name).read_bytes())
    pw=json.loads((RUN/'playwright-fechamento.json').read_text(encoding='utf-8'))
    # Keep test identities/statuses and statistics, excluding environment/configuration/raw error bodies.
    tests=[]
    def collect(suite):
        for s in suite.get('specs',[]):
            for t in s.get('tests',[]):
                tests.append({'title':s['title'],'file':s.get('file'),'status':t['status'],
                              'results':[{'status':r['status'],'duration':r['duration']} for r in t['results']]})
        for s in suite.get('suites',[]):collect(s)
    for s in pw['suites']:collect(s)
    if pw['stats']['unexpected'] or pw['stats']['expected']!=25:raise SystemExit('Revise o resultado Playwright antes da entrega.')
    (evidence/'playwright-fechamento.json').write_text(json.dumps({'stats':pw['stats'],'tests':tests},indent=2,ensure_ascii=False),encoding='utf-8')
    (evidence/'playwright-fechamento.txt').write_bytes((RUN/'playwright-fechamento.txt').read_bytes())
    for p in (RUN/'depois').glob('*'):
        if p.suffix not in ('.png','.json'):continue
        folder=DOC/('telas' if p.suffix=='.png' else 'evidencias');folder.mkdir(exist_ok=True);(folder/p.name).write_bytes(p.read_bytes())
    if len(list((DOC/'telas').glob('*.png')))!=28:raise SystemExit('São esperadas 14 capturas de viewport e 14 completas.')
    for p in (RUN/'render-docx').glob('page-*.png'):
        dest=DOC/'documentos-renderizados/docx'/p.name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
    for pattern in ('minuta-pdf-*.png','consolidacao-pdf-*.png'):
        for p in RUN.glob(pattern):
            dest=DOC/'documentos-renderizados'/p.name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
    reference=json.loads((DOC/'referencias/MANIFESTO.json').read_text(encoding='utf-8'))
    for entry in reference['references']:
        if sha((DOC/'referencias'/entry['path']).read_bytes())!=entry['sha256']:raise SystemExit('Referência visual diverge do manifesto original.')

    # Distinguish this increment from the already-dirty initial checkout.
    current=sorted(set(git('ls-files').decode().splitlines()+git('ls-files','--others','--exclude-standard').decode().splitlines()))
    changed=[n for n in current if (ROOT/n).is_file() and before['files'].get(n)!=sha((ROOT/n).read_bytes())]
    source=[n for n in changed if not n.startswith('docs/')]
    (DOC/'ARQUIVOS_ALTERADOS.md').write_text('# Arquivos desta rodada\n\nComparação com o checkout local já modificado na auditoria inicial; não apenas com HEAD.\n\n'+
        '\n'.join('- `'+n+'` · '+('novo' if n not in before['files'] else 'integração sobre arquivo preexistente') for n in source)+
        '\n\nDocumentação, imagens e evidências novas estão em `docs/IRPS_7_TELAS_APROVADAS/`. O diff acumulado inclui também a implementação local anterior, identificada no relatório.\n',encoding='utf-8')
    preservation={'branch':branch,'head':head,'preexisting_missing':[],'v4_unchanged':True,'v4_hashes':core,
                  'increment_source_files':source,'commit_push_merge_deploy_performed':False}
    (evidence/'preservacao.json').write_text(json.dumps(preservation,indent=2),encoding='utf-8')
    (evidence/'git-status-final.txt').write_bytes(git('status','--short'))
    check=subprocess.run(['git','-C',str(ROOT),'diff','--check'],capture_output=True,text=True)
    (evidence/'git-diff-check.txt').write_text('exit_code='+str(check.returncode)+'\n'+check.stdout,encoding='utf-8')
    if check.returncode:raise SystemExit('Resolva git diff --check antes de empacotar.')
    files=sorted(set(git('diff','--name-only','--diff-filter=ACMR').decode().splitlines()+git('ls-files','--others','--exclude-standard').decode().splitlines()))
    findings=[]
    for n in files:
        p=ROOT/n
        if not p.is_file():continue
        if set(Path(n).parts)&{'.runtime','.venv','node_modules','uploads','exports','_tools','output','.git'} or Path(n).name.startswith('.env') and Path(n).name!='.env.example':
            findings.append({'file':n,'rule':'forbidden_path'});continue
        data=p.read_bytes()
        if len(data)>5*1024*1024:findings.append({'file':n,'rule':'large_file_review'})
        for rule,pattern in rules.items():
            if re.search(pattern,data):findings.append({'file':n,'rule':rule})
    audit={'scope':'local diff and nonignored untracked files; no complete Git history certification',
           'files_scanned':len(files),'findings':findings,'v4_unchanged':True,'credentials_printed':False,
           'excluded':['runtime/configuration','database','sessions','uploads','private_quotes','dependencies','original_institutional_documents']}
    (evidence/'auditoria-seguranca.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    if findings:raise SystemExit('Suspeita de arquivo sensível; revise a auditoria local antes de empacotar.')

    previous=ROOT/'output/IRPS_DIRETRIZ_MESTRA_V2_REVISAO_LOCAL_2026-10-20.zip'
    incremental='';payload={};normalized_baselines=[]
    with zipfile.ZipFile(previous) as old:
        old_names=set(old.namelist())
        for n in source:
            raw=(ROOT/n).read_bytes();payload['arquivos/'+n]=raw
            if n in before['files']:
                prior=old.read('arquivos/'+n) if 'arquivos/'+n in old_names else git('show','HEAD:'+n)
                if sha(prior)!=before['files'][n]:
                    # Git objects use LF while the initial Windows checkout can use CRLF.
                    # Accept only a byte representation that exactly matches the saved hash.
                    lf=prior.replace(b'\r\n',b'\n')
                    candidates=[lf,lf.replace(b'\n',b'\r\n')]
                    prior=next((v for v in candidates if sha(v)==before['files'][n]),prior)
                if sha(prior)!=before['files'][n]:
                    if 'arquivos/'+n in old_names:raise SystemExit('O arquivo anterior fornecido diverge do inventário: '+n)
                    # A Git-clean file can have mixed CRLF/LF on disk. Its physical hash is
                    # retained, but the textual diff explicitly uses the normalized Git object.
                    prior=git('show','HEAD:'+n)
                    prior.decode('utf-8')
                    normalized_baselines.append({'file':n,'initial_physical_sha256':before['files'][n],
                                                 'textual_baseline':'Git HEAD normalized text; mixed checkout line endings not reconstructed'})
            else:prior=b''
            try:a=prior.decode('utf-8');b=raw.decode('utf-8')
            except UnicodeDecodeError:continue
            incremental+=''.join(difflib.unified_diff(a.splitlines(keepends=True),b.splitlines(keepends=True),fromfile='a/'+n if prior else '/dev/null',tofile='b/'+n))
    payload['incremento-desta-rodada.patch']=incremental.encode('utf-8')
    # The accumulated overlay includes earlier uncommitted code required by this increment.
    cumulative=git('diff','--binary').decode('utf-8')
    untracked=set(git('ls-files','--others','--exclude-standard').decode().splitlines())
    for n in files:
        if n.startswith('docs/'):continue
        p=ROOT/n
        if not p.is_file():continue
        raw=p.read_bytes();payload['arquivos/'+n]=raw
        if n in untracked:
            try:text=raw.decode('utf-8')
            except UnicodeDecodeError:continue
            cumulative+=''.join(difflib.unified_diff([],text.splitlines(keepends=True),fromfile='/dev/null',tofile='b/'+n))
    payload['alteracoes-locais-acumuladas.patch']=cumulative.encode('utf-8')
    for p in DOC.rglob('*'):
        if p.is_file():payload[str(p.relative_to(DOC)).replace('\\','/')]=p.read_bytes()
    payload['LEIA-ME.txt']=('IRPS telas aprovadas - revisão local\nComece por README.md e galeria.html.\n'
        'arquivos/ contém o overlay de código sobre e65375414792d4baef6ec1eaa6d7384c398448ca, incluindo o trabalho anterior necessário.\n'
        'incremento-desta-rodada.patch compara com o estado local inicial. alteracoes-locais-acumuladas.patch compara com HEAD.\n'
        'Não aplique indiscriminadamente sobre trabalho local. Não é instalador autônomo.\n'
        'A demonstração de planejamento e manifestações é fictícia. Catálogo não comprova compras.\n'
        'Não contém banco, credenciais, sessões, originais recebidos nem custos privados. Nenhum commit/push/deploy.\n').encode('utf-8')
    payload['BASES_DO_DIFF.json']=json.dumps({'normalized_baselines':normalized_baselines,
        'notice':'Physical initial hashes remain recorded. Listed files use the normalized Git text for review, not a claim of byte-identical checkout reconstruction.'},ensure_ascii=False,indent=2).encode('utf-8')
    manifest={'branch':branch,'head':head,'v4_unchanged':True,'normalized_diff_baselines':normalized_baselines,'files':{n:sha(v) for n,v in sorted(payload.items())}}
    payload['manifesto-pacote.json']=json.dumps(manifest,ensure_ascii=False,indent=2).encode('utf-8')
    out=ROOT/'output/IRPS_7_TELAS_REVISAO_LOCAL_2026-10-21.zip';out.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        for n,raw in sorted(payload.items()):z.writestr(n,raw)
    with zipfile.ZipFile(out) as z:
        assert z.testzip() is None
        for n,h in manifest['files'].items():assert sha(z.read(n))==h
    print(json.dumps({'file':str(out),'bytes':out.stat().st_size,'sha256':sha(out.read_bytes()),'members':len(payload),
                      'increment_source_files':len(source),'secret_findings':0,'git_diff_check':0,'v4_unchanged':True},ensure_ascii=False))


if __name__=='__main__':main()
