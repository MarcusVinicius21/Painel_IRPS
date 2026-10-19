from alembic import op
revision='0003'
down_revision='0002'
branch_labels=None
depends_on=None
def upgrade():
 conn=op.get_bind().connection.driver_connection
 conn.execute("CREATE TABLE source_backoff(org_id uuid NOT NULL REFERENCES organization,provider text NOT NULL,resume_after timestamptz NOT NULL,PRIMARY KEY(org_id,provider)); ALTER TABLE source_backoff ENABLE ROW LEVEL SECURITY; ALTER TABLE source_backoff FORCE ROW LEVEL SECURITY; CREATE POLICY tenant_scope ON source_backoff USING (org_id=nullif(current_setting('irps.org_id',true),'')::uuid) WITH CHECK (org_id=nullif(current_setting('irps.org_id',true),'')::uuid); GRANT SELECT,INSERT,UPDATE ON source_backoff TO irps_app;")
def downgrade():op.get_bind().connection.driver_connection.execute('DROP TABLE source_backoff;')
