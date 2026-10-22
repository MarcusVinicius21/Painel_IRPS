"""Append-only internal review events bound to immutable IRP drafts."""
from alembic import op
revision='0014'
down_revision='0013'
branch_labels=None
depends_on=None


def upgrade():
    conn=op.get_bind().connection.driver_connection
    conn.execute("""
    CREATE TABLE irp_draft_review (
      org_id uuid NOT NULL REFERENCES organization, id uuid NOT NULL,
      draft_id uuid NOT NULL, revision integer NOT NULL CHECK(revision>0),previous_id uuid,
      status text NOT NULL CHECK(status IN ('requested','changes_requested','reviewed_internal')),
      note text NOT NULL CHECK(length(trim(note))>=10),context_sha256 text NOT NULL CHECK(length(context_sha256)=64),
      created_by uuid NOT NULL REFERENCES actor,created_at timestamptz NOT NULL DEFAULT now(),
      PRIMARY KEY(org_id,id),UNIQUE(org_id,draft_id,revision),
      FOREIGN KEY(org_id,draft_id) REFERENCES irp_draft(org_id,id),
      FOREIGN KEY(org_id,previous_id) REFERENCES irp_draft_review(org_id,id)
    );
    ALTER TABLE irp_draft_review ENABLE ROW LEVEL SECURITY;
    ALTER TABLE irp_draft_review FORCE ROW LEVEL SECURITY;
    CREATE POLICY tenant_scope ON irp_draft_review USING(org_id=nullif(current_setting('irps.org_id',true),'')::uuid) WITH CHECK(org_id=nullif(current_setting('irps.org_id',true),'')::uuid);
    GRANT SELECT,INSERT ON irp_draft_review TO irps_app;
    CREATE TRIGGER immutable_irp_draft_review BEFORE UPDATE OR DELETE ON irp_draft_review FOR EACH ROW EXECUTE FUNCTION irps_deny_mutation();
    """)


def downgrade():raise RuntimeError('Preserve os pareceres. Recrie somente bancos descartáveis para reiniciar testes.')
