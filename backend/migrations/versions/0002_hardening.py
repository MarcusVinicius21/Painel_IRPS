from alembic import op
revision='0002'
down_revision='0001'
branch_labels=None
depends_on=None

def upgrade():
 conn=op.get_bind().connection.driver_connection
 conn.execute('REVOKE INSERT,UPDATE,DELETE ON membership FROM irps_app;')
 conn.execute('ALTER TABLE private_quote ADD CONSTRAINT quote_current_version_fk FOREIGN KEY(org_id,id,current_revision) REFERENCES quote_version(org_id,quote_id,revision) DEFERRABLE INITIALLY DEFERRED;')
 for name in ('calculation','calculation_line','extracted_document','document','artifact','audit_event'):
  # All identifiers are hardcoded migration constants.
  conn.execute(f'CREATE TRIGGER immutable_{name} BEFORE UPDATE OR DELETE ON {name} FOR EACH ROW EXECUTE FUNCTION irps_deny_mutation();')
  conn.execute(f'REVOKE UPDATE,DELETE ON {name} FROM irps_app;')

def downgrade():
 conn=op.get_bind().connection.driver_connection
 for name in ('calculation','calculation_line','extracted_document','document','artifact','audit_event'):
  conn.execute(f'DROP TRIGGER IF EXISTS immutable_{name} ON {name};');conn.execute(f'GRANT UPDATE,DELETE ON {name} TO irps_app;')
 conn.execute('ALTER TABLE private_quote DROP CONSTRAINT quote_current_version_fk;')
 conn.execute('GRANT INSERT,UPDATE,DELETE ON membership TO irps_app;')
