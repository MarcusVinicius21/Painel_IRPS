"""Append-only internal proposals, communications and reviewed manifestations."""
from alembic import op
revision='0010'
down_revision='0009'
branch_labels=None
depends_on=None

def upgrade():
    conn=op.get_bind().connection.driver_connection
    conn.execute("""
    CREATE TABLE irp_operation (
      org_id uuid NOT NULL REFERENCES organization, id uuid NOT NULL,
      study_id uuid NOT NULL, scenario_revision integer NOT NULL,
      kind text NOT NULL CHECK(kind IN ('suggestion','communication','manifestation','external_act')),
      municipality_ibge char(7) NOT NULL REFERENCES municipality,
      revision integer NOT NULL CHECK(revision>0), supersedes_id uuid,
      payload jsonb NOT NULL, created_by uuid NOT NULL REFERENCES actor,
      created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(org_id,id),
      FOREIGN KEY(org_id,study_id) REFERENCES director_study(org_id,id),
      FOREIGN KEY(org_id,supersedes_id) REFERENCES irp_operation(org_id,id),
      UNIQUE(org_id,study_id,kind,municipality_ibge,revision)
    );
    CREATE INDEX irp_operation_current ON irp_operation(org_id,study_id,kind,municipality_ibge,revision DESC);
    ALTER TABLE irp_operation ENABLE ROW LEVEL SECURITY;
    ALTER TABLE irp_operation FORCE ROW LEVEL SECURITY;
    CREATE POLICY tenant_scope ON irp_operation USING(org_id=nullif(current_setting('irps.org_id',true),'')::uuid) WITH CHECK(org_id=nullif(current_setting('irps.org_id',true),'')::uuid);
    GRANT SELECT,INSERT ON irp_operation TO irps_app;
    CREATE TRIGGER immutable_irp_operation BEFORE UPDATE OR DELETE ON irp_operation FOR EACH ROW EXECUTE FUNCTION irps_deny_mutation();
    """)

def downgrade():
    raise RuntimeError('Preserve as manifestações; restaure somente o banco descartável para reiniciar os testes.')
