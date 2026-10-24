"""Add requested monitoring scope without asserting membership or purchase coverage."""
from alembic import op
revision='0017'
down_revision='0016'
branch_labels=None
depends_on=None

def upgrade():
    c=op.get_bind().connection.driver_connection
    c.execute('''CREATE TABLE monitoring_target(
      org_id uuid NOT NULL REFERENCES organization,municipality_ibge char(7) NOT NULL REFERENCES municipality,
      origin_name text NOT NULL,origin text NOT NULL,source_id uuid NOT NULL REFERENCES source_observation,
      roster_sha256 char(64) NOT NULL,membership_status text NOT NULL CHECK(membership_status IN ('PENDING','CONFIRMED','NOT_CONFIRMED')),
      monitoring_enabled boolean NOT NULL,validated_at timestamptz NOT NULL DEFAULT now(),
      created_by uuid NOT NULL REFERENCES actor,PRIMARY KEY(org_id,municipality_ibge));
      ALTER TABLE monitoring_target ENABLE ROW LEVEL SECURITY;ALTER TABLE monitoring_target FORCE ROW LEVEL SECURITY;
      CREATE POLICY tenant_scope ON monitoring_target USING(org_id=nullif(current_setting('irps.org_id',true),'')::uuid)
        WITH CHECK(org_id=nullif(current_setting('irps.org_id',true),'')::uuid);
      GRANT SELECT,INSERT ON monitoring_target TO irps_app;
      CREATE TRIGGER immutable_monitoring_target BEFORE UPDATE OR DELETE ON monitoring_target
        FOR EACH ROW EXECUTE FUNCTION irps_deny_mutation();''')

def downgrade():
    c=op.get_bind().connection.driver_connection
    if c.execute('SELECT EXISTS(SELECT 1 FROM monitoring_target)').fetchone()[0]:raise RuntimeError('Preserve monitoring evidence')
    c.execute('DROP TABLE monitoring_target')
