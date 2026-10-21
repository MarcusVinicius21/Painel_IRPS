"""Append-only incomplete workflow snapshots, never validated planning inputs."""
from alembic import op

revision='0012'
down_revision='0011'
branch_labels=None
depends_on=None


def upgrade():
    op.get_bind().connection.driver_connection.execute('''
    CREATE TABLE director_progress(
      org_id uuid NOT NULL REFERENCES organization,id uuid NOT NULL,
      supersedes_id uuid,payload jsonb NOT NULL,created_by uuid NOT NULL REFERENCES actor,
      created_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(org_id,id),UNIQUE(org_id,supersedes_id),
      FOREIGN KEY(org_id,supersedes_id) REFERENCES director_progress(org_id,id));
    ALTER TABLE director_progress ENABLE ROW LEVEL SECURITY;
    ALTER TABLE director_progress FORCE ROW LEVEL SECURITY;
    CREATE POLICY tenant_scope ON director_progress
      USING(org_id=nullif(current_setting('irps.org_id',true),'')::uuid)
      WITH CHECK(org_id=nullif(current_setting('irps.org_id',true),'')::uuid);
    GRANT SELECT,INSERT ON director_progress TO irps_app;
    CREATE TRIGGER immutable_director_progress BEFORE UPDATE OR DELETE ON director_progress
      FOR EACH ROW EXECUTE FUNCTION irps_deny_mutation();
    ''')


def downgrade():
    raise RuntimeError('Append-only: preserve progress snapshots; use disposable database backups.')
