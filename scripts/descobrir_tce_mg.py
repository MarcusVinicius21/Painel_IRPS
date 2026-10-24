"""Bounded anonymous GETs to institutional TCE links. No TLS bypass, login or DB writes."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,sys
import httpx
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.tce_discovery import inspect_html,dataset_decisions,official_link

TARGETS={'open_data':'https://dadosabertos.tce.mg.gov.br/',
    'sicom_reference':'https://www.tce.mg.gov.br/sicomconsulta/',
    'institutional_notice':'https://www.tce.mg.gov.br/noticia/Detalhe/1111627683'}
MAX_BYTES=4*1024*1024


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--execute',action='store_true')
    args=parser.parse_args()
    if not args.execute:print(json.dumps({'executed':False,'targets':TARGETS}));return
    folder=ROOT/'.runtime/irps-municipal/tce-discovery';folder.mkdir(parents=True,exist_ok=True)
    oldfolder=ROOT/'.runtime/irps-municipal/contracts'
    old=json.loads((oldfolder/'audit.json').read_text(encoding='utf-8'))
    reused={'sicom_reference':'TCE_MG_SICOM','institutional_notice':'TCE_MG_PORTAL_REFERENCIA'}
    probes=[];additional={}
    with httpx.Client(timeout=httpx.Timeout(20,connect=8),follow_redirects=False,
        headers={'User-Agent':'IRPS-public-discovery/1.0','Accept':'text/html,application/json'}) as client:
        for name,url in [*TARGETS.items()]:
            proof={'target':name,'url':url,'at':datetime.now(timezone.utc).isoformat()};content=None
            previous=next((p for p in old if p['source']==reused.get(name)),None)
            path=oldfolder/(reused.get(name,'unavailable')+'.raw')
            if previous and previous.get('http_status')==200 and path.exists() and (datetime.now(timezone.utc)-datetime.fromisoformat(previous['queried_at'])).total_seconds()<86400:
                body=path.read_bytes()
                if hashlib.sha256(body).hexdigest()==previous.get('sha256'):
                    content=body;proof.update(http_status=200,reused_saved_evidence=True,original_consulted_at=previous['queried_at'])
            if content is None:
                try:
                    with client.stream('GET',url) as response:
                        proof.update(http_status=response.status_code,retry_after=response.headers.get('retry-after'))
                        body=bytearray()
                        for chunk in response.iter_bytes():
                            body.extend(chunk)
                            if len(body)>MAX_BYTES:raise ValueError('RESPONSE_LIMIT')
                    content=bytes(body)
                except (httpx.HTTPError,ValueError) as exc:
                    proof.update(state='connection_or_response_limit_failure',error_type=type(exc).__name__)
            if content is not None:
                proof.update(bytes=len(content),sha256=hashlib.sha256(content).hexdigest())
                if proof.get('http_status')==200:
                    (folder/(name+'.raw')).write_bytes(content);proof.update(inspect_html(content,url))
                    for link in proof['official_links']:
                        if link in ('https://fiscalizandocomtce.tce.mg.gov.br/','https://bancodepreco.tce.mg.gov.br/'):
                            additional[link]=name
                else:proof['state']='http_unavailable'
            probes.append(proof);print(json.dumps({k:v for k,v in proof.items() if k not in ('official_links','download_candidates')},ensure_ascii=False),flush=True)
        for number,(url,parent) in enumerate(sorted(additional.items())):
            proof={'target':'official_alternative_'+str(number),'url':url,'linked_from':parent,'at':datetime.now(timezone.utc).isoformat()}
            try:
                with client.stream('GET',url) as response:
                    proof['http_status']=response.status_code;body=bytearray()
                    for chunk in response.iter_bytes():
                        body.extend(chunk)
                        if len(body)>MAX_BYTES:raise ValueError('RESPONSE_LIMIT')
                proof.update(bytes=len(body),sha256=hashlib.sha256(body).hexdigest())
                if response.status_code==200:
                    (folder/(proof['target']+'.raw')).write_bytes(body);proof.update(inspect_html(bytes(body),url))
                else:proof['state']='http_unavailable'
            except (httpx.HTTPError,ValueError) as exc:proof.update(state='connection_or_response_limit_failure',error_type=type(exc).__name__)
            probes.append(proof);print(json.dumps({k:v for k,v in proof.items() if k not in ('official_links','download_candidates')},ensure_ascii=False),flush=True)
    report={'at':datetime.now(timezone.utc).isoformat(),'probes':probes,'datasets':dataset_decisions(probes),
    'database_mutated':False,'tls_verification_disabled':False,'explicit_credentials_used':False,'municipal_completeness':None}
    (folder/'discovery.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')


if __name__=='__main__':main()
