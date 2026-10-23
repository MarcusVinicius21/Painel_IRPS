"""Read-only textual evidence. Request completion is not municipal completeness."""
from datetime import datetime, timezone
from pathlib import Path
import json
import sys
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from app.config import load_settings
from app.db import Database, normalize


def main():
    settings = load_settings()
    if settings.auth_mode != 'operational_local' or make_url(settings.database_url.get_secret_value()).host not in ('127.0.0.1', 'localhost', '::1'):
        raise ValueError('Use configuração explícita do banco operacional local.')
    folder = ROOT / '.runtime/irps-municipal'
    plans = json.loads((folder / 'publication-plans.json').read_text(encoding='utf-8'))
    ids = [p['id'] for p in plans]
    database = Database(settings)
    database.engine.update_execution_options(isolation_level='REPEATABLE READ')
    try:
        with database.transaction(settings.operator_org_id, settings.operator_actor_id) as db:
            db.execute('SET TRANSACTION READ ONLY')
            args = {'o': settings.operator_org_id, 'ids': ids}
            collections = db.all("""SELECT c.id,c.scope->>'start' AS start,c.scope->>'end' AS end,c.state,c.pages,
                c.source_requests,c.error_code,c.resume_after,
                (SELECT count(*) FROM history_task t WHERE t.org_id=c.org_id AND t.collection_id=c.id) AS materialized_tasks
                FROM history_collection c WHERE c.org_id=:o AND c.id=ANY(CAST(:ids AS uuid[])) ORDER BY start""", args)
            tasks = db.all("""SELECT t.state,t.error_code,count(*) AS count FROM history_task t
                WHERE t.org_id=:o AND t.collection_id=ANY(CAST(:ids AS uuid[])) GROUP BY t.state,t.error_code""", args)
            facts = db.all("""SELECT f.municipality_ibge,m.name,f.phase,to_char(f.event_date,'YYYY-MM') AS month,
                count(*) AS observed_records,count(DISTINCT NULLIF(f.obligation_id,'')) AS identifiable_processes
                FROM procurement_fact f JOIN municipality m ON m.ibge=f.municipality_ibge
                WHERE f.org_id=:o AND f.classification='official' AND f.is_current
                  AND f.event_date BETWEEN DATE '2025-10-01' AND DATE '2026-09-30'
                GROUP BY f.municipality_ibge,m.name,f.phase,month ORDER BY f.municipality_ibge,month,f.phase""", args)
            counts = {table: db.one('SELECT count(*) AS n FROM ' + table)['n'] for table in
                      ('national_catalogue_entry', 'price_monthly_snapshot', 'price_monthly_record', 'procurement_fact')}
            sources = db.all("""SELECT DISTINCT s.provider,s.url,s.sha256,s.consulted_at FROM history_page p
                JOIN source_observation s ON s.id=p.source_id
                WHERE p.org_id=:o AND p.collection_id=ANY(CAST(:ids AS uuid[]))
                ORDER BY s.consulted_at DESC LIMIT 10""", args)
    finally:
        database.engine.dispose()
    report = normalize({'at': datetime.now(timezone.utc).isoformat(), 'collections': collections,
        'tasks': tasks, 'observed_facts_by_phase_month': facts, 'protected_counts': counts, 'recent_evidence': sources,
        'municipal_purchase_completeness': None,
        'limitations': ['Tarefas materializadas podem aumentar com a paginação.',
            'Registros são linhas observadas, não número de compras nem consumo.',
            'Município ou mês sem registros não representa zero compras.',
            'Publicação, homologação e contrato permanecem separados.',
            'Preços nacionais não comprovam cobertura municipal.']})
    target = folder / ('progress-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S') + '.json')
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'evidence_file': str(target), 'protected_counts': counts,
        'completed_monthly_plans': sum(c['state'] == 'completed' for c in collections),
        'pages': sum(c['pages'] for c in collections), 'tasks': tasks,
        'municipal_purchase_completeness': None}, ensure_ascii=False))


if __name__ == '__main__':
    main()
