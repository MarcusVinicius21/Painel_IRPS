"""Read-only buyer census, backed by the precise archived official publication."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from app.config import load_settings
from app.db import Database, normalize
from app.municipal_campaign import buyer_identity


def main():
    settings = load_settings()
    if not settings.operator_org_id:
        raise ValueError('Selecione configuração operacional explícita.')
    database = Database(settings)
    try:
        with database.transaction(settings.operator_org_id, settings.operator_actor_id) as db:
            db.execute('SET TRANSACTION READ ONLY')
            buyers = db.all("SELECT * FROM buyer WHERE org_id=:o AND classification='official' ORDER BY municipality_ibge,cnpj,unit_code", {'o': settings.operator_org_id})
            result = []
            for buyer in buyers:
                evidence = db.all("""SELECT f.event_identity,s.url,s.sha256,s.consulted_at,s.body FROM procurement_fact f
                    JOIN source_observation s ON s.id=f.source_id AND s.org_id=f.org_id
                    WHERE f.org_id=:o AND f.buyer_id=:b AND f.provider='PNCP' AND f.classification='official'
                    AND s.classification='official' AND s.http_status=200
                    ORDER BY s.consulted_at DESC,f.id""", {'o': settings.operator_org_id, 'b': buyer['id']})
                identities = []
                for proof in evidence:
                    payload = json.loads(proof.pop('body'))
                    data = payload.get('data', []) if isinstance(payload, dict) else payload
                    if not isinstance(data, list):
                        continue
                    record = next((x for x in data if isinstance(x, dict) and x.get('numeroControlePNCP') == proof['event_identity'].removesuffix(':publication')), None)
                    if record:
                        identities.append({**buyer_identity(buyer, record), 'evidence': normalize(proof)})
                signatures = {(x['cnpj'], x['unit_code'], x['municipality_ibge'], x['sphere'], x['power']) for x in identities}
                result.append({'buyer_id': str(buyer['id']), 'name': buyer['name'], 'cnpj': buyer['cnpj'],
                    'unit_code': buyer['unit_code'], 'municipality_ibge': buyer['municipality_ibge'],
                    'state': 'verified' if identities and len(signatures) == 1 and all(x['state'] == 'verified' for x in identities) else 'ORGAO_NAO_VERIFICADO',
                    'conflicting_evidence': len(signatures) > 1, 'identities': identities})
    finally:
        database.engine.dispose()
    target = ROOT / '.runtime/irps-municipal/buyers.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'buyers': len(result), 'verified': sum(x['state'] == 'verified' for x in result),
        'distinct_cnpjs': len({x['cnpj'] for x in result}), 'conflicts': sum(x['conflicting_evidence'] for x in result)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
