from alembic import op
revision='0005'
down_revision='0004'
branch_labels=None
depends_on=None
def upgrade():
 conn=op.get_bind().connection.driver_connection
 conn.execute("CREATE TABLE official_catalogue_entry(org_id uuid NOT NULL REFERENCES organization,id uuid PRIMARY KEY,provider text NOT NULL,code text NOT NULL,revision_hash char(64) NOT NULL,description text NOT NULL,unit text,active boolean,source_id uuid NOT NULL REFERENCES source_observation,body jsonb NOT NULL,UNIQUE(provider,code,revision_hash)); ALTER TABLE official_catalogue_entry ENABLE ROW LEVEL SECURITY; ALTER TABLE official_catalogue_entry FORCE ROW LEVEL SECURITY; CREATE POLICY public_read ON official_catalogue_entry FOR SELECT USING(true); CREATE POLICY tenant_insert ON official_catalogue_entry FOR INSERT WITH CHECK(org_id=nullif(current_setting('irps.org_id',true),'')::uuid); GRANT SELECT,INSERT ON official_catalogue_entry TO irps_app; CREATE TRIGGER catalogue_immutable BEFORE UPDATE OR DELETE ON official_catalogue_entry FOR EACH ROW EXECUTE FUNCTION irps_deny_mutation();")
def downgrade():op.get_bind().connection.driver_connection.execute('DROP TABLE official_catalogue_entry;')
