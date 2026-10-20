"""Append-only normalization and reviewed canonical product generations."""
from alembic import op

revision = '0008'
down_revision = '0007'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind().connection.driver_connection
    conn.execute("""
    CREATE TABLE item_normalization (
      org_id uuid NOT NULL REFERENCES organization,
      id uuid NOT NULL,
      fact_id uuid NOT NULL REFERENCES procurement_fact,
      source_id uuid NOT NULL REFERENCES source_observation,
      algorithm_version text NOT NULL,
      item_id text NOT NULL,
      item_version integer NOT NULL,
      original_description text NOT NULL,
      description_key text NOT NULL,
      original_unit text NOT NULL,
      unit_key text NOT NULL,
      package_signature text,
      catalogue_namespace text,
      catalogue_code text,
      confidence text NOT NULL CHECK (confidence IN ('coded_package','coded_unit','text_unit','incomplete')),
      issues jsonb NOT NULL DEFAULT '[]',
      created_at timestamptz NOT NULL DEFAULT now(),
      PRIMARY KEY (org_id,id),
      UNIQUE (org_id,fact_id,algorithm_version)
    );
    CREATE INDEX normalization_lookup ON item_normalization(org_id,item_id,item_version,algorithm_version);
    CREATE TABLE canonical_product (
      org_id uuid NOT NULL REFERENCES organization,
      id uuid NOT NULL,
      name text NOT NULL,
      category text NOT NULL,
      classification text NOT NULL CHECK (classification IN ('official','synthetic')),
      unit_key text NOT NULL,
      package_signature text,
      members jsonb NOT NULL,
      justification text NOT NULL,
      evidence text NOT NULL,
      reviewed_by uuid NOT NULL REFERENCES actor,
      supersedes_id uuid,
      created_at timestamptz NOT NULL DEFAULT now(),
      PRIMARY KEY (org_id,id),
      FOREIGN KEY (org_id,supersedes_id) REFERENCES canonical_product(org_id,id)
    );
    CREATE INDEX canonical_active ON canonical_product(org_id,created_at DESC);
    """)
    for table in ('item_normalization','canonical_product'):
        conn.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY; ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")
        conn.execute(f"CREATE POLICY tenant_scope ON {table} USING(org_id=nullif(current_setting('irps.org_id',true),'')::uuid) WITH CHECK(org_id=nullif(current_setting('irps.org_id',true),'')::uuid);")
        conn.execute(f"GRANT SELECT,INSERT ON {table} TO irps_app;")
        conn.execute(f"CREATE TRIGGER immutable_{table} BEFORE UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION irps_deny_mutation();")


def downgrade():
    conn = op.get_bind().connection.driver_connection
    conn.execute('DROP TABLE canonical_product; DROP TABLE item_normalization;')
