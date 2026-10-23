"""Independent immutable monthly Compras.gov price evidence, never PNCP facts."""
from alembic import op
revision='0015'
down_revision='0014'
branch_labels=None
depends_on=None


def upgrade():
    c=op.get_bind().connection.driver_connection
    c.execute('''
    CREATE TABLE price_monthly_snapshot(
      org_id uuid NOT NULL REFERENCES organization,id uuid NOT NULL,kind text NOT NULL CHECK(kind IN ('material','servico')),
      month date NOT NULL,archive_sha256 char(64) NOT NULL,source_url text NOT NULL,metadata jsonb NOT NULL,
      source_rows integer NOT NULL,accepted_rows integer NOT NULL,rejected_rows integer NOT NULL,duplicate_rows integer NOT NULL,
      imported_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(org_id,id),UNIQUE(org_id,kind,month,archive_sha256)
    );
    CREATE TABLE price_monthly_record(
      org_id uuid NOT NULL,snapshot_id uuid NOT NULL,source_key text NOT NULL,record_sha256 char(64) NOT NULL,
      line_number integer NOT NULL,code text NOT NULL,purchase_date date NOT NULL,source_updated_at text,body jsonb NOT NULL,
      PRIMARY KEY(org_id,snapshot_id,source_key,record_sha256),
      FOREIGN KEY(org_id,snapshot_id) REFERENCES price_monthly_snapshot(org_id,id)
    );
    CREATE INDEX monthly_price_code_period ON price_monthly_record(org_id,code,purchase_date,snapshot_id);
    CREATE INDEX monthly_price_snapshot_scope ON price_monthly_snapshot(org_id,kind,month,imported_at DESC);
    ALTER TABLE price_monthly_snapshot ENABLE ROW LEVEL SECURITY;ALTER TABLE price_monthly_snapshot FORCE ROW LEVEL SECURITY;
    ALTER TABLE price_monthly_record ENABLE ROW LEVEL SECURITY;ALTER TABLE price_monthly_record FORCE ROW LEVEL SECURITY;
    CREATE POLICY tenant_scope ON price_monthly_snapshot USING(org_id=nullif(current_setting('irps.org_id',true),'')::uuid) WITH CHECK(org_id=nullif(current_setting('irps.org_id',true),'')::uuid);
    CREATE POLICY tenant_scope ON price_monthly_record USING(org_id=nullif(current_setting('irps.org_id',true),'')::uuid) WITH CHECK(org_id=nullif(current_setting('irps.org_id',true),'')::uuid);
    GRANT SELECT,INSERT ON price_monthly_snapshot,price_monthly_record TO irps_app;
    CREATE TRIGGER monthly_snapshot_immutable BEFORE UPDATE OR DELETE ON price_monthly_snapshot FOR EACH ROW EXECUTE FUNCTION irps_deny_mutation();
    CREATE TRIGGER monthly_record_immutable BEFORE UPDATE OR DELETE ON price_monthly_record FOR EACH ROW EXECUTE FUNCTION irps_deny_mutation();
    ''')


def downgrade():raise RuntimeError('Preserve os arquivos e suas versões. Use somente bancos descartáveis para reiniciar testes.')
