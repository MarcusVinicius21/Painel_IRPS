"""Bounded source-contract smoke audit; no import, credentials or database writes."""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import hashlib
import json
import time

import httpx

ROOT = Path(__file__).resolve().parents[1]
TARGETS = {
    'PNCP_CONSULTA': 'https://pncp.gov.br/api/consulta/v3/api-docs',
    'PNCP_DETALHE': 'https://pncp.gov.br/api/pncp/v3/api-docs',
    'COMPRAS_GOV': 'https://dadosabertos.compras.gov.br/v3/api-docs',
    'TCE_MG': 'https://dadosabertos.tce.mg.gov.br/',
    'TCE_MG_SICOM': 'https://www.tce.mg.gov.br/sicomconsulta/',
    'TCE_MG_PORTAL_REFERENCIA': 'https://www.tce.mg.gov.br/noticia/Detalhe/1111627683',
}


def summarize_contract(document):
    paths = document.get('paths', {})
    return {'version': document.get('info', {}).get('version'), 'paths_count': len(paths),
            'routes': {path: {'parameters': [x.get('name') for x in methods.get('get', {}).get('parameters', [])],
                              'get': 'get' in methods}
                       for path, methods in paths.items()}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--only', nargs='+', help='Optional fixed target names; never arbitrary URLs.')
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps({'planned': TARGETS, 'executed': False}))
        return
    folder = ROOT / '.runtime/irps-municipal/contracts'
    folder.mkdir(parents=True, exist_ok=True)
    evidence = []
    targets = dict(TARGETS)
    for code in ('3131307', '3168705'):
        targets['PNCP_SMOKE_' + code] = 'https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao?dataInicial=20251001&dataFinal=20251007&codigoModalidadeContratacao=6&codigoMunicipioIbge=' + code + '&pagina=1&tamanhoPagina=10'
    if args.only:
        if set(args.only) - targets.keys():
            parser.error('Unknown fixed target.')
        targets = {name: url for name, url in targets.items() if name in args.only}
    with httpx.Client(timeout=httpx.Timeout(20, connect=8), follow_redirects=False,
                      headers={'User-Agent': 'IRPS-public-contract-audit/1.0'}) as client:
        for name, url in targets.items():
            proof = {'source': name, 'url': url, 'queried_at': datetime.now(timezone.utc).isoformat()}
            try:
                with client.stream('GET', url) as response:
                    proof['http_status'] = response.status_code
                    proof['retry_after'] = response.headers.get('retry-after')
                    content = bytearray()
                    for chunk in response.iter_bytes():
                        content.extend(chunk)
                        if len(content) > 8 * 1024 * 1024:
                            raise ValueError('RESPONSE_LIMIT')
                proof.update(bytes=len(content), sha256=hashlib.sha256(content).hexdigest())
                proof['state'] = 'accessible' if response.status_code in (200, 204) else 'unavailable'
                if response.status_code == 200:
                    (folder / (name + '.raw')).write_bytes(content)
                    try:
                        document = json.loads(content)
                    except (ValueError, UnicodeError):
                        document = None
                    if isinstance(document, dict) and 'paths' in document:
                        proof['contract'] = summarize_contract(document)
                    elif name.startswith('PNCP_SMOKE') and isinstance(document, dict):
                        records = document.get('data')
                        proof['returned_records'] = len(records) if isinstance(records, list) else None
                        proof['total_pages'] = document.get('totalPaginas')
                        proof['total_records_reported'] = document.get('totalRegistros')
                        proof['returned_municipalities'] = sorted({str((r.get('unidadeOrgao') or {}).get('codigoIbge')) for r in records or []})
                elif response.status_code == 204:
                    proof.update(returned_records=0, total_pages=None, total_records_reported=None)
            except (httpx.HTTPError, ValueError) as exc:
                proof['state'] = 'connection_or_size_failure'
                proof['error_type'] = type(exc).__name__
            evidence.append(proof)
            print(json.dumps({k: v for k, v in proof.items() if k != 'contract'}, ensure_ascii=False), flush=True)
            time.sleep(1)
    audit = folder / 'audit.json'
    previous = json.loads(audit.read_text(encoding='utf-8')) if audit.exists() else []
    audit.write_text(json.dumps([x for x in previous if x['source'] not in targets] + evidence, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
