"""Reuse saved discovery evidence and census; no network, credentials or database."""
from pathlib import Path
import hashlib,json,sys
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.municipal_portals import inventory


def main():
    folder=ROOT/'.runtime/irps-municipal';scope=json.loads((folder/'census.json').read_text())['scope']
    result=inventory(scope['municipalities']);proofs=[]
    for name in ('ipatinga.json','ipatinga-open.json','timoteo.json','export-browser.json','payment-scope-probes.json','validation.json'):
        path=folder/'financial-discovery'/name;body=path.read_bytes()
        proofs.append({'file':name,'sha256':hashlib.sha256(body).hexdigest()})
    result.update(at=datetime.now(timezone.utc).isoformat(),census_sha256=scope['sha256'],
        evidence=proofs,discovery_reused=True,database_mutated=False)
    (folder/'portal-inventory.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
