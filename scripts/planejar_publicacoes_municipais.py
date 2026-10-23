"""Plan PNCP publication gaps for the frozen census; collection is a separate tick."""
from datetime import date, datetime, timezone
from pathlib import Path
import argparse
import hashlib
import json
import sys
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from app.config import load_settings
from app.db import Database
from app import sources
from app.modality import COLLECTABLE_CODES
from app.municipal_campaign import freeze_scope
from app.municipal_plan import create_publication_plan
from app.opportunity_schemas import HistoricalScope


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--months', nargs='+')
    args = parser.parse_args()
    folder = ROOT / '.runtime/irps-municipal'
    census = json.loads((folder / 'census.json').read_text(encoding='utf-8'))
    scope = census['scope']
    assert scope == freeze_scope(scope['municipalities'], date(2025, 10, 1), date(2026, 9, 30))
    assert len(census['ibge_evidence']) == len(scope['municipalities']) and all(x['state'] == 'verified' for x in census['ibge_evidence'])
    months = args.months or scope['months']
    if len(set(months)) != len(months) or set(months) - set(scope['months']):
        parser.error('Selecione competências únicas do manifesto de doze meses.')
    if not args.execute:
        print(json.dumps({'executed': False, 'municipalities': scope['municipalities'], 'months': months,
                          'modality_allowlist': sorted(COLLECTABLE_CODES)}, ensure_ascii=False))
        return
    settings = load_settings()
    if settings.auth_mode != 'operational_local' or make_url(settings.database_url.get_secret_value()).host not in ('localhost', '127.0.0.1', '::1') or settings.ai_enabled:
        parser.error('Selecione o ambiente do operador local sem IA paga.')
    url, status, raw, data = sources.public_get('https://pncp.gov.br/api/pncp/v1/modalidades')
    if not isinstance(data, list) or any(type(r.get('id')) is not int for r in data):
        raise ValueError('Domínio de modalidades mudou; confira antes da coleta.')
    codes = sorted({r['id'] for r in data})
    if set(codes) != COLLECTABLE_CODES:
        raise ValueError('O domínio oficial mudou; não foi criado um plano incompleto.')
    (folder / 'domain-evidence.json').write_text(json.dumps({'url': url, 'http_status': status,
        'sha256': hashlib.sha256(raw).hexdigest(), 'queried_at': datetime.now(timezone.utc).isoformat(), 'codes': codes}, indent=2), encoding='utf-8')
    database = Database(settings)
    plans = []
    try:
        for month in months:
            first = date.fromisoformat(month + '-01')
            following = date(first.year + (first.month == 12), first.month % 12 + 1, 1)
            from datetime import timedelta
            body = HistoricalScope(municipalities=[c['ibge'] for c in scope['municipalities']], start=first,
                end=following - timedelta(days=1), modalities=codes, items=False, results=False, max_pages=2000, size=20)
            with database.transaction(settings.operator_org_id, settings.operator_actor_id) as db:
                ctx = sources.job_context(db, settings.operator_org_id, settings.operator_actor_id)
                plan = create_publication_plan(ctx, body)
            plans.append({'month': month, **plan})
            # Persist after EACH committed plan. Restart resolves the exact key.
            (folder / 'publication-plans.json').write_text(json.dumps(plans, indent=2), encoding='utf-8')
            print(json.dumps(plans[-1]), flush=True)
    finally:
        database.engine.dispose()


if __name__ == '__main__':
    main()
