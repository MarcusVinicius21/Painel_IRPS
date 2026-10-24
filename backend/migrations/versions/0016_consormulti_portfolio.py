"""Additive portfolio triage and immutable filter preferences; no national rewrite."""
from alembic import op
revision='0016'
down_revision='0015'
branch_labels=None
depends_on=None


def upgrade():
    c=op.get_bind().connection.driver_connection
    c.execute('''
    CREATE TABLE portfolio_run(org_id uuid NOT NULL REFERENCES organization,id uuid NOT NULL,
      rule_version text NOT NULL,rule_sha256 char(64) NOT NULL,input_sha256 char(64) NOT NULL,
      provenance jsonb NOT NULL,created_at timestamptz NOT NULL DEFAULT now(),created_by uuid NOT NULL REFERENCES actor,
      PRIMARY KEY(org_id,id),UNIQUE(org_id,rule_sha256,input_sha256));
    CREATE TABLE portfolio_group(org_id uuid NOT NULL,run_id uuid NOT NULL,code text NOT NULL,name text NOT NULL,scope text NOT NULL,
      PRIMARY KEY(org_id,run_id,code),FOREIGN KEY(org_id,run_id) REFERENCES portfolio_run(org_id,id));
    CREATE TABLE portfolio_code_link(org_id uuid NOT NULL,run_id uuid NOT NULL,group_code text NOT NULL,
      snapshot_id uuid NOT NULL,code text NOT NULL,technical_status text NOT NULL
        CHECK(technical_status IN ('DIRECT_TECHNICAL','NEEDS_TECH_REVIEW','INDIRECT','EXCLUDED')),
      commercial_status text NOT NULL CHECK(commercial_status IN ('COMMERCIAL_CONFIRMED','COMMERCIAL_PENDING','OUT_OF_PORTFOLIO','UNKNOWN')),
      subgroup text NOT NULL,reason text NOT NULL,multiple_group_reason text,
      PRIMARY KEY(org_id,run_id,group_code,snapshot_id,code),
      FOREIGN KEY(org_id,run_id,group_code) REFERENCES portfolio_group(org_id,run_id,code),
      FOREIGN KEY(snapshot_id,code) REFERENCES national_catalogue_entry(snapshot_id,code));
    CREATE INDEX portfolio_code_search ON portfolio_code_link(org_id,run_id,group_code,technical_status,snapshot_id,code);
    CREATE TABLE portfolio_preference(org_id uuid NOT NULL REFERENCES organization,id uuid NOT NULL,actor_id uuid NOT NULL REFERENCES actor,
      payload jsonb NOT NULL,created_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(org_id,id));
    CREATE INDEX portfolio_pref_latest ON portfolio_preference(org_id,actor_id,created_at DESC,id);
    ''')
    for table in ('portfolio_run','portfolio_group','portfolio_code_link','portfolio_preference'):
        c.execute(f'''ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;ALTER TABLE {table} FORCE ROW LEVEL SECURITY;
        CREATE POLICY tenant_scope ON {table} USING(org_id=nullif(current_setting('irps.org_id',true),'')::uuid)
          WITH CHECK(org_id=nullif(current_setting('irps.org_id',true),'')::uuid);
        GRANT SELECT,INSERT ON {table} TO irps_app;
        CREATE TRIGGER immutable_{table} BEFORE UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION irps_deny_mutation();''')


def downgrade():
    # Only a new, empty disposable database can reverse this schema migration.
    c=op.get_bind().connection.driver_connection
    for table in ('portfolio_preference','portfolio_code_link','portfolio_group','portfolio_run'):
        if c.execute(f'SELECT EXISTS(SELECT 1 FROM {table})').fetchone()[0]:
            raise RuntimeError('Preserve portfolio evidence; rollback by disabling the feature, not deleting rows.')
    for table in ('portfolio_preference','portfolio_code_link','portfolio_group','portfolio_run'):c.execute(f'DROP TABLE {table}')
