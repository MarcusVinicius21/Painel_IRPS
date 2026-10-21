"""Package the audited local diff and explicitly selected evidence, never the runtime."""
import difflib,hashlib,json,subprocess,zipfile
from pathlib import Path
from auditar_diff_local import rules

ROOT=Path(__file__).resolve().parents[1]
def git(*args):return subprocess.check_output(['git','-C',str(ROOT),*args])

if __name__=='__main__':
    audit=json.loads((ROOT/'.runtime/evidencias/diretriz-v2/auditoria-local.json').read_text(encoding='utf-8'))
    if audit['findings'] or not audit['v4_unchanged']:raise SystemExit('Resolva a auditoria antes de empacotar.')
    files=sorted(set(git('diff','--name-only','--diff-filter=ACMR').decode().splitlines()+git('ls-files','--others','--exclude-standard').decode().splitlines()))
    untracked=set(git('ls-files','--others','--exclude-standard').decode().splitlines())
    payload={};patch=git('diff','--binary').decode('utf-8')
    for name in files:
        path=(ROOT/name).resolve()
        if ROOT not in path.parents or any(p in ('.runtime','.venv','node_modules','_tools','uploads','exports','output','.git') for p in Path(name).parts):
            raise SystemExit('Arquivo fora do escopo de revisão: '+name)
        if not path.is_file():continue
        raw=path.read_bytes()
        if len(raw)>5*1024*1024 or name.startswith('.env'):raise SystemExit('Revise manualmente antes de incluir: '+name)
        if any(__import__('re').search(pattern,raw) for pattern in rules.values()):raise SystemExit('Padrão sensível encontrado em '+name)
        payload['arquivos/'+name]=raw
        if name in untracked:
            try:text=raw.decode('utf-8')
            except UnicodeDecodeError:continue
            patch+=''.join(difflib.unified_diff([],text.splitlines(keepends=True),fromfile='/dev/null',tofile='b/'+name))
    payload['alteracoes-locais.patch']=patch.encode('utf-8')
    docs=ROOT/'docs/DIRETRIZ_MESTRA_V2'
    for path in docs.rglob('*'):
        if path.is_file():payload[str(path.relative_to(docs)).replace('\\','/')]=path.read_bytes()
    evidence=ROOT/'.runtime/evidencias/diretriz-v2'
    for name in ('minuta-demonstrativa.docx','minuta-demonstrativa.pdf','dossie-demonstrativo.zip'):
        payload['demonstracao/'+name]=(evidence/name).read_bytes()
    for path in (evidence/'render-final-validado').glob('page-*.png'):
        payload['demonstracao/docx-renderizado/'+path.name]=path.read_bytes()
    for path in evidence.glob('pdf-final-*.png'):
        payload['demonstracao/pdf-renderizado/'+path.name]=path.read_bytes()
    payload['LEIA-ME.txt']=('IRPS Diretriz Mestra V2 - revisao local\nComece por README.md e RELATORIO.md.\n'
        'O codigo alterado esta em arquivos/. O patch inclui alteracoes anteriores preservadas e este incremento.\n'
        'Use o repositorio base no commit e65375414792d4baef6ec1eaa6d7384c398448ca. Este ZIP nao e uma instalacao autonoma.\n'
        'Minutas e estudos de demonstracao sao ficticios. O catalogo nao comprova compras.\n'
        'Nao contem CSVs integrais, modelos originais, banco, credenciais, sessoes, uploads ou custos comerciais privados.\n'
        'Nenhum commit, push, merge ou deploy foi executado.\n').encode()
    manifest={'branch':git('branch','--show-current').decode().strip(),'head':git('rev-parse','HEAD').decode().strip(),
              'v4_unchanged':True,'files':{name:hashlib.sha256(data).hexdigest() for name,data in sorted(payload.items())}}
    payload['manifesto.json']=json.dumps(manifest,ensure_ascii=False,indent=2).encode('utf-8')
    out=ROOT/'output/IRPS_DIRETRIZ_MESTRA_V2_REVISAO_LOCAL_2026-10-20.zip';out.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        for name,data in sorted(payload.items()):z.writestr(name,data)
    with zipfile.ZipFile(out) as z:
        assert z.testzip() is None
        for name,sha in manifest['files'].items():assert hashlib.sha256(z.read(name)).hexdigest()==sha
    print(json.dumps({'file':str(out),'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'members':len(payload),'source_files_changed':len(files)},ensure_ascii=False))
