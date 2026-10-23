"""Preview or advance existing public collections. Never creates a duplicate collector."""
import argparse
import json
from pathlib import Path
import sys
from uuid import UUID
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from app.config import load_settings
from app.db import Database, normalize
from app.history_runner import run_tick


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--collection', type=UUID, action='append', required=True)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--max-attempts', type=int, default=20)
    parser.add_argument('--max-seconds', type=int, default=60)
    args = parser.parse_args()
    settings = load_settings()
    url = make_url(settings.database_url.get_secret_value())
    if settings.auth_mode != 'operational_local' or url.host not in ('127.0.0.1', 'localhost', '::1') or settings.ai_enabled:
        parser.error('Use a configuração explícita do operador local, sem IA paga.')
    database = Database(settings)
    try:
        result = run_tick(database, settings.operator_org_id, settings.operator_actor_id,
                          [str(cid) for cid in args.collection], execute=args.execute,
                          max_attempts=args.max_attempts, max_seconds=args.max_seconds)
        print(json.dumps(normalize(result), ensure_ascii=False, indent=2))
    finally:
        database.engine.dispose()


if __name__ == '__main__':
    main()
