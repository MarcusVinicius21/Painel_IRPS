"""Small CNPJ-only CGU query; official sanctions are not municipal purchases."""
import hashlib,json,re
from datetime import datetime,timezone
import httpx
from .portal_credentials import load_portal_key
from .security import fail
from .sources import observe

BASE='https://api.portaldatransparencia.gov.br/api-de-dados/ceis'

def sanctions(ctx,cnpj,transport=None):
    ctx.require('sources.sync')
    if not re.fullmatch(r'\d{14}',cnpj):fail(422,'Informe o CNPJ com 14 números.')
    key=load_portal_key()
    if not key:fail(503,'A consulta federal ainda precisa da chave autorizada.','KEY_REQUIRED')
    # Redirects disabled: the key can never follow a redirect to another host.
    try:
        with httpx.Client(timeout=httpx.Timeout(20,connect=5),follow_redirects=False,transport=transport) as client:
            with client.stream('GET',BASE,params={'codigoSancionado':cnpj,'pagina':1},headers={'chave-api-dados':key,'Accept':'application/json'}) as r:
                body=bytearray()
                for part in r.iter_bytes():
                    body.extend(part)
                    if len(body)>2*1024*1024:fail(502,'A resposta excedeu o limite desta consulta.','SOURCE_LIMIT')
                status=r.status_code;url=str(r.url)
    except httpx.HTTPError:fail(502,'Não foi possível consultar a fonte federal agora.','SOURCE_CONNECTION')
    proof={'provider':'PORTAL_TRANSPARENCIA','url':url,'http_status':status,'sha256':hashlib.sha256(body).hexdigest(),
           'consulted_at':datetime.now(timezone.utc).isoformat(),'municipal_purchase_history':False}
    if status!=200:
        return {**proof,'state':'blocked' if status in (401,403) else 'retry_later','records':[],
                'error_code':'AUTH_REJECTED' if status in (401,403) else 'HTTP_'+str(status)}
    try:data=json.loads(body)
    except ValueError:fail(502,'A fonte devolveu um formato inesperado.','SOURCE_FORMAT')
    if not isinstance(data,list) or len(data)>1000 or any(not isinstance(x,dict) for x in data):fail(502,'A resposta precisa de conferência.','SOURCE_FORMAT')
    # Exact CNPJ filter must be proved if rows are returned; no CPF data imported.
    for row in data:
        person=row.get('pessoa') or row.get('sancionado') or {}
        code=str(person.get('cnpjFormatado') or person.get('cpfCnpj') or row.get('cpfCnpj') or row.get('codigoSancionado') or '')
        if re.sub(r'\D','',code)!=cnpj:fail(502,'A resposta não confirmou o CNPJ solicitado.','SOURCE_IDENTITY_MISMATCH')
    sid=observe(ctx,'PORTAL_TRANSPARENCIA',url,status,bytes(body),{'scope':'CEIS_CNPJ_FIRST_PAGE','cnpj':cnpj,'pages':1,'complete_sanctions_check':False})
    return {**proof,'state':'available','source_id':str(sid),'records':data,'record_count':len(data),
            'complete_sanctions_check':False,'notice':'Consulta CEIS de uma página. Não comprova regularidade nem histórico de compras.'}
