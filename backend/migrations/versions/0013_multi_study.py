"""Additive, tenant scoped and immutable multi-item study bindings."""
from alembic import op

revision = '0013'
down_revision = '0012'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind().connection.driver_connection
    conn.execute('''
    CREATE TABLE director_multi_study_version (
      org_id uuid NOT NULL REFERENCES organization, id uuid NOT NULL,
      revision integer NOT NULL CHECK(revision>0), previous_revision integer,
      scenario_id uuid NOT NULL, scenario_revision integer NOT NULL,
      request_id uuid NOT NULL, request_sha256 text NOT NULL,
      payload jsonb NOT NULL CHECK((payload->>'contract_version'='1') IS TRUE), context_sha256 text NOT NULL,
      created_by uuid NOT NULL REFERENCES actor, created_at timestamptz NOT NULL DEFAULT now(),
      PRIMARY KEY(org_id,id,revision), UNIQUE(org_id,request_id),
      CHECK((revision=1 AND previous_revision IS NULL) OR (revision>1 AND previous_revision=revision-1)),
      FOREIGN KEY(org_id,id,previous_revision) REFERENCES director_multi_study_version(org_id,id,revision),
      FOREIGN KEY(org_id,scenario_id,scenario_revision) REFERENCES scenario_version(org_id,scenario_id,revision)
    );
    CREATE TABLE director_multi_study_item (
      org_id uuid NOT NULL, study_id uuid NOT NULL, revision integer NOT NULL,
      item_id text NOT NULL, item_version integer NOT NULL, source_study_id uuid NOT NULL,
      PRIMARY KEY(org_id,study_id,revision,item_id), UNIQUE(org_id,study_id,revision,source_study_id),
      FOREIGN KEY(org_id,study_id,revision) REFERENCES director_multi_study_version(org_id,id,revision),
      FOREIGN KEY(org_id,source_study_id) REFERENCES director_study(org_id,id),
      FOREIGN KEY(item_id,item_version) REFERENCES item_version(id,version)
    );
    ''')
    for table in ('director_multi_study_version','director_multi_study_item'):
        conn.execute(f'ALTER TABLE {table} ENABLE ROW LEVEL SECURITY; ALTER TABLE {table} FORCE ROW LEVEL SECURITY;')
        conn.execute(f"CREATE POLICY tenant_scope ON {table} USING(org_id=nullif(current_setting('irps.org_id',true),'')::uuid) WITH CHECK(org_id=nullif(current_setting('irps.org_id',true),'')::uuid);")
        conn.execute(f'GRANT SELECT,INSERT ON {table} TO irps_app;')
        conn.execute(f'CREATE TRIGGER immutable_{table} BEFORE UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION irps_deny_mutation();')


def downgrade():
    raise RuntimeError('Preserve as versões. Recrie apenas um banco descartável para reiniciar os testes.')
