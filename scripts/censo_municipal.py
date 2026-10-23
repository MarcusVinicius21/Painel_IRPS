"""Read-only municipal census. Only --verify-ibge performs bounded public GETs."""
from datetime import date, datetime, timezone
from pathlib import Path
import argparse
import hashlib
import json
import sys
import time

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from app.config import load_settings
from app.db import Database
from app.municipal_campaign import freeze_scope, pending_matrix, verify_ibge


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify-ibge', action='store_true')
    args = parser.parse_args()
    settings = load_settings()
    if not settings.operator_org_id:
        parser.error('Escolha explicitamente a configuração operacional local.')
    database = Database(settings)
    try:
        with database.transaction(settings.operator_org_id, settings.operator_actor_id) as db:
            db.execute('SET TRANSACTION READ ONLY')
            cities = [dict(x) for x in db.all('SELECT ibge,name,uf FROM municipality ORDER BY ibge')]
    finally:
        database.engine.dispose()
    scope = freeze_scope(cities, date(2025, 10, 1), date(2026, 9, 30))
    proofs = []
    if args.verify_ibge:
        with httpx.Client(timeout=25, follow_redirects=False) as client:
            for city in scope['municipalities']:
                url = 'https://servicodados.ibge.gov.br/api/v1/localidades/municipios/' + city['ibge']
                proof = {'ibge': city['ibge'], 'url': url, 'queried_at': datetime.now(timezone.utc).isoformat()}
                try:
                    response = client.get(url)
                    proof.update(http_status=response.status_code, sha256=hashlib.sha256(response.content).hexdigest())
                    response.raise_for_status()
                    verify_ibge(city, response.json())
                    proof['state'] = 'verified'
                except (httpx.HTTPError, ValueError, TypeError, KeyError):
                    proof['state'] = 'needs_review'
                proofs.append(proof)
                time.sleep(1)
    folder = ROOT / '.runtime/irps-municipal'
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / ('scope-' + scope['sha256'] + '.json')
    encoded = json.dumps(scope, ensure_ascii=False, indent=2) + '\n'
    if target.exists() and target.read_text(encoding='utf-8') != encoded:
        raise ValueError('O manifesto congelado diverge; não foi substituído.')
    target.write_text(encoded, encoding='utf-8')
    (folder / 'census.json').write_text(json.dumps({'scope': scope, 'ibge_evidence': proofs,
        'planned_matrix': pending_matrix(scope)}, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'scope': scope, 'ibge_evidence': proofs, 'planned_cells': len(pending_matrix(scope))}, ensure_ascii=False))


if __name__ == '__main__':
    main()
