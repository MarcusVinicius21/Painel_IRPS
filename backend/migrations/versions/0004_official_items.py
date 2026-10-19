from alembic import op
revision='0004'
down_revision='0003'
branch_labels=None
depends_on=None
def upgrade():op.get_bind().connection.driver_connection.execute("GRANT INSERT ON item_version TO irps_app; CREATE TRIGGER item_version_immutable BEFORE UPDATE OR DELETE ON item_version FOR EACH ROW EXECUTE FUNCTION irps_deny_mutation();")
def downgrade():op.get_bind().connection.driver_connection.execute('REVOKE INSERT ON item_version FROM irps_app; DROP TRIGGER item_version_immutable ON item_version;')
