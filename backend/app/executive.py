"""Read-only executive projections. Catalogue size is never historical coverage."""
from .db import normalize


def section(ctx, name):
    ctx.require('read')
    if name == 'catalogue':
        rows = ctx.db.all('''WITH latest AS (SELECT DISTINCT ON(kind) * FROM national_catalogue_snapshot
            ORDER BY kind,imported_at DESC,id DESC)
            SELECT s.kind,s.id,s.imported_at,s.row_count,s.active_count,s.inactive_count,
              (SELECT count(DISTINCT l.code) FROM national_product_link l JOIN canonical_product p
                ON p.org_id=l.org_id AND p.id=l.product_id WHERE l.snapshot_id=s.id AND l.org_id=:o
                AND p.classification='official' AND NOT EXISTS (SELECT 1 FROM canonical_product newer
                  WHERE newer.org_id=p.org_id AND newer.supersedes_id=p.id)) AS reviewed_linked_codes
            FROM latest s ORDER BY kind''', {'o': ctx.org_id})
        return normalize({'snapshots': rows, 'purchase_history_implied': False,
                          'coverage_denominator': 'Códigos dos arquivos importados; não representa compras nacionais.'})
    if name == 'history':
        base = " FROM procurement_fact WHERE is_current AND classification='official'"
        return normalize({
            'phases': ctx.db.all('SELECT provider,phase,count(*) AS records,count(DISTINCT municipality_ibge) AS municipalities'+base+' GROUP BY provider,phase ORDER BY phase,provider'),
            'municipalities': ctx.db.all('''SELECT m.ibge,m.name,m.uf,count(*) AS records
                FROM procurement_fact f JOIN municipality m ON m.ibge=f.municipality_ibge
                WHERE f.is_current AND f.classification='official' GROUP BY m.ibge,m.name,m.uf ORDER BY m.name'''),
            'monthly': ctx.db.all("SELECT to_char(event_date,'YYYY-MM') AS month,phase,count(*) AS records"+base+" AND event_date IS NOT NULL GROUP BY month,phase ORDER BY month,phase"),
            'items': ctx.db.all('''SELECT item_id,item_version,phase,min(description) AS description,count(*) AS records,
                count(DISTINCT municipality_ibge) AS municipalities
                FROM procurement_fact WHERE is_current AND classification='official' AND item_id IS NOT NULL
                GROUP BY item_id,item_version,phase ORDER BY count(*) DESC,item_id,item_version,phase LIMIT 6'''),
            'notice': 'Registros atuais por fase. Linhas de itens não representam compras independentes. Cobertura municipal incompleta.'})
    return normalize({
        'collections': ctx.db.all('''SELECT t.state,count(*) AS tasks FROM history_task t JOIN history_collection c
            ON c.org_id=t.org_id AND c.id=t.collection_id WHERE t.org_id=:o AND c.dataset='official'
            GROUP BY t.state ORDER BY t.state''', {'o': ctx.org_id}),
        'studies': ctx.db.all('''SELECT id,scenario_id,scenario_revision,payload->>'name' AS name,
            payload->>'classification' AS classification,created_at FROM director_study
            WHERE org_id=:o ORDER BY created_at DESC,id DESC LIMIT 8''', {'o': ctx.org_id}),
        'activities': ctx.db.all('''SELECT action,created_at FROM audit_event WHERE org_id=:o
            AND action IN ('director.study_created','irp.draft_created','irp.manifestation_recorded',
                          'irp.suggestion_recorded','irp.communication_recorded','irp.dossier_exported','irp.draft_prepared')
            ORDER BY created_at DESC,id DESC LIMIT 6''', {'o': ctx.org_id})})
