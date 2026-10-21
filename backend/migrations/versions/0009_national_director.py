"""Versioned national catalogue and tenant-scoped director studies and IRP drafts."""
from alembic import op

revision = '0009'
down_revision = '0008'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind().connection.driver_connection
    conn.execute("""
    ALTER TABLE item_version ADD COLUMN org_id uuid REFERENCES organization;
    ALTER TABLE item_version ENABLE ROW LEVEL SECURITY;
    ALTER TABLE item_version FORCE ROW LEVEL SECURITY;
    CREATE POLICY item_read ON item_version FOR SELECT USING(org_id IS NULL OR org_id=nullif(current_setting('irps.org_id',true),'')::uuid);
    CREATE POLICY item_insert ON item_version FOR INSERT WITH CHECK(org_id IS NULL OR org_id=nullif(current_setting('irps.org_id',true),'')::uuid);
    CREATE TABLE national_catalogue_snapshot (
      id uuid PRIMARY KEY, kind text NOT NULL CHECK(kind IN ('CATMAT','CATSER')),
      sha256 text NOT NULL, filename text NOT NULL, origin text NOT NULL,
      imported_at timestamptz NOT NULL DEFAULT now(), row_count integer NOT NULL,
      active_count integer NOT NULL, inactive_count integer NOT NULL,
      UNIQUE(kind,sha256), CHECK(row_count=active_count+inactive_count)
    );
    CREATE TABLE national_catalogue_entry (
      snapshot_id uuid NOT NULL REFERENCES national_catalogue_snapshot,
      code text NOT NULL, name text NOT NULL, active boolean NOT NULL,
      group_code text, group_name text, class_code text, class_name text,
      pdm_code text, pdm_name text, original jsonb NOT NULL,
      search_vector tsvector GENERATED ALWAYS AS
        (to_tsvector('portuguese',translate(lower(coalesce(name,'')||' '||coalesce(group_name,'')||' '||coalesce(class_name,'')||' '||coalesce(pdm_name,'')),
          'ÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇÑáàâãäéèêëíìîïóòôõöúùûüçñ',
          'aaaaaeeeeiiiiooooouuuucnaaaaaeeeeiiiiooooouuuucn'))) STORED,
      PRIMARY KEY(snapshot_id,code)
    );
    CREATE INDEX national_catalogue_search ON national_catalogue_entry USING gin(search_vector);
    CREATE INDEX national_catalogue_class ON national_catalogue_entry(snapshot_id,class_code,active,code);
    CREATE TABLE national_product_link (
      org_id uuid NOT NULL REFERENCES organization, id uuid NOT NULL,
      snapshot_id uuid NOT NULL, code text NOT NULL,
      product_id uuid NOT NULL, justification text NOT NULL, evidence text NOT NULL,
      created_by uuid NOT NULL REFERENCES actor, created_at timestamptz NOT NULL DEFAULT now(),
      PRIMARY KEY(org_id,id), UNIQUE(org_id,snapshot_id,code,product_id),
      FOREIGN KEY(snapshot_id,code) REFERENCES national_catalogue_entry(snapshot_id,code),
      FOREIGN KEY(org_id,product_id) REFERENCES canonical_product(org_id,id)
    );
    CREATE TABLE director_study (
      org_id uuid NOT NULL REFERENCES organization, id uuid NOT NULL,
      scenario_id uuid NOT NULL, scenario_revision integer NOT NULL,
      payload jsonb NOT NULL, context_sha256 text NOT NULL,
      created_by uuid NOT NULL REFERENCES actor, created_at timestamptz NOT NULL DEFAULT now(),
      PRIMARY KEY(org_id,id),
      FOREIGN KEY(org_id,scenario_id,scenario_revision) REFERENCES scenario_version(org_id,scenario_id,revision)
    );
    CREATE INDEX director_study_scenario ON director_study(org_id,scenario_id,created_at DESC);
    CREATE TABLE irp_draft (
      org_id uuid NOT NULL REFERENCES organization, id uuid NOT NULL,
      study_id uuid NOT NULL, payload jsonb NOT NULL, validation jsonb NOT NULL,
      created_by uuid NOT NULL REFERENCES actor, created_at timestamptz NOT NULL DEFAULT now(),
      PRIMARY KEY(org_id,id), FOREIGN KEY(org_id,study_id) REFERENCES director_study(org_id,id)
    );
    GRANT SELECT ON national_catalogue_snapshot,national_catalogue_entry TO irps_app;
    """)
    for table in ('national_catalogue_snapshot','national_catalogue_entry'):
        conn.execute(f'CREATE TRIGGER immutable_{table} BEFORE UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION irps_deny_mutation();')
    for table in ('national_product_link','director_study','irp_draft'):
        conn.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY; ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")
        conn.execute(f"CREATE POLICY tenant_scope ON {table} USING(org_id=nullif(current_setting('irps.org_id',true),'')::uuid) WITH CHECK(org_id=nullif(current_setting('irps.org_id',true),'')::uuid);")
        conn.execute(f'GRANT SELECT,INSERT ON {table} TO irps_app;')
        conn.execute(f'CREATE TRIGGER immutable_{table} BEFORE UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION irps_deny_mutation();')


def downgrade():
    raise RuntimeError('Migration append-only: restaure o banco local descartável em vez de remover evidências.')
