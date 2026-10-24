"""Durable singleton schedule per organization; reuses source queue locks."""
from alembic import op
revision='0018'
down_revision='0017'
branch_labels=None
depends_on=None
def upgrade():
 c=op.get_bind().connection.driver_connection
 c.execute('''CREATE TABLE monitoring_schedule(org_id uuid PRIMARY KEY REFERENCES organization,
   enabled boolean NOT NULL DEFAULT true,cursor bigint NOT NULL DEFAULT 0 CHECK(cursor>=0),
   next_run timestamptz NOT NULL DEFAULT now(),last_run timestamptz,last_request timestamptz,
   last_error text,last_result jsonb NOT NULL DEFAULT '{}',updated_at timestamptz NOT NULL DEFAULT now());
   ALTER TABLE monitoring_schedule ENABLE ROW LEVEL SECURITY;ALTER TABLE monitoring_schedule FORCE ROW LEVEL SECURITY;
   CREATE POLICY tenant_scope ON monitoring_schedule USING(org_id=nullif(current_setting('irps.org_id',true),'')::uuid)
    WITH CHECK(org_id=nullif(current_setting('irps.org_id',true),'')::uuid);
   GRANT SELECT,INSERT,UPDATE ON monitoring_schedule TO irps_app;''')
def downgrade():
 c=op.get_bind().connection.driver_connection
 if c.execute('SELECT EXISTS(SELECT 1 FROM monitoring_schedule)').fetchone()[0]:raise RuntimeError('Preserve schedule history')
 c.execute('DROP TABLE monitoring_schedule')
