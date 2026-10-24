"""Pinned, bounded stdio client. No shell, browser-selected URLs or inherited secrets."""
import os,json,subprocess,threading,queue,tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
TOOLS=('search_licitacoes','get_licitacao','list_licitacao_itens','list_licitacao_resultados','list_licitacao_arquivos',
 'search_contratos','get_contrato','list_contrato_termos','list_contrato_instrumentos','search_atas_rp','get_ata_rp',
 'get_orgao','get_fornecedor_contratos','search_pca','list_pca_itens','get_cnpj_data','aggregate_licitacoes_por_periodo','compare_periodos')

def installed():
    p=ROOT/'.runtime/licinexus/service/node_modules/@licinexusbr/mcp/package.json'
    return p.is_file() and json.loads(p.read_text(encoding='utf8'))['version']=='0.2.1'

def invoke(tool,args):
    if tool not in TOOLS or not isinstance(args,dict) or len(json.dumps(args))>4096:raise ValueError('Unsupported bounded MCP request')
    if not installed():raise RuntimeError('LICINEXUS_NOT_INSTALLED')
    import shutil
    node=shutil.which('node')
    if not node:raise RuntimeError('NODE_REQUIRED')
    folder=ROOT/'.runtime/licinexus';folder.mkdir(exist_ok=True)
    fd,trace=tempfile.mkstemp(suffix='.jsonl',prefix='call-',dir=folder);os.close(fd)
    env={k:v for k,v in os.environ.items() if k.upper() in ('PATH','SYSTEMROOT','WINDIR','TEMP','TMP','USERPROFILE','LOCALAPPDATA')}
    env.update(IRPS_LX_TRACE=trace,IRPS_LX_BUDGET='8')
    command=[node,'--max-old-space-size=192','--import',(ROOT/'scripts/licinexus_guard.mjs').as_uri(),
             str(folder/'service/node_modules/@licinexusbr/mcp/dist/index.js')]
    proc=subprocess.Popen(command,cwd=folder,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,encoding='utf8')
    inbox=queue.Queue()
    def reader():
        try:
            while line:=proc.stdout.readline(4*1024*1024+1):
                if len(line)>4*1024*1024:inbox.put({'error':{'message':'MCP_RESPONSE_LIMIT'}});return
                try:inbox.put(json.loads(line))
                except ValueError:continue
        finally:inbox.put(None)
    threading.Thread(target=reader,daemon=True).start()
    def rpc(number,method,params):
        proc.stdin.write(json.dumps({'jsonrpc':'2.0','id':number,'method':method,'params':params})+'\n');proc.stdin.flush()
        import time
        end=time.monotonic()+65
        while time.monotonic()<end:
            try:r=inbox.get(timeout=1)
            except queue.Empty:continue
            if r is None:raise RuntimeError('MCP_PROCESS_EXITED')
            if r.get('id')==number:return r
        raise RuntimeError('MCP_DEADLINE')
    try:
        rpc(1,'initialize',{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'irps-backend','version':'1'}})
        result=rpc(2,'tools/call',{'name':tool,'arguments':args})
        path=Path(trace)
        if path.stat().st_size>24*1024*1024:raise RuntimeError('MCP_TRACE_LIMIT')
        responses=[json.loads(line) for line in path.read_text(encoding='utf8').splitlines()]
        return result,responses
    finally:
        if proc.stdin:proc.stdin.close()
        try:proc.wait(timeout=2)
        except subprocess.TimeoutExpired:proc.terminate();proc.wait(timeout=5)
        Path(trace).unlink(missing_ok=True)
