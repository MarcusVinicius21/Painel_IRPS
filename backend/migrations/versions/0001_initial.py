from pathlib import Path
from alembic import op
revision='0001'
down_revision=None
branch_labels=None
depends_on=None
def upgrade():
 sql=(Path(__file__).resolve().parents[1]/'001_schema.sql').read_text(encoding='utf-8')
 # No bound parameters: psycopg must not interpret PL/pgSQL format('%I').
 op.get_bind().connection.driver_connection.execute(sql)
def downgrade():
 # This migration is used only on the new dedicated database.
 # Preserve alembic_version so Alembic can record the downgrade atomically.
 conn=op.get_bind().connection.driver_connection
 conn.execute("DO $$ DECLARE r record; BEGIN FOR r IN SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename <> 'alembic_version' LOOP EXECUTE format('DROP TABLE IF EXISTS public.%I CASCADE',r.tablename); END LOOP; END $$;")
 conn.execute('DROP FUNCTION IF EXISTS irps_deny_mutation() CASCADE;')
