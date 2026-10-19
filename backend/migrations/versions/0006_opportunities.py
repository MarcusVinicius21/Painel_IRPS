"""Durable historical collection and organization-scoped opportunity curation."""
from alembic import op

revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None

TABLES = ('municipality_group', 'history_collection', 'history_task', 'history_page',
          'opportunity_equivalence', 'opportunity_review', 'opportunity_watch', 'opportunity_alert')

def upgrade():
    conn = op.get_bind().connection.driver_connection
    conn.execute("""
    CREATE TABLE municipality_group(
      org_id uuid NOT NULL REFERENCES organization, id uuid NOT NULL, name text NOT NULL,
      municipalities jsonb NOT NULL, created_by uuid NOT NULL REFERENCES actor,
      created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(org_id,id));
    CREATE TABLE history_collection(
      org_id uuid NOT NULL REFERENCES organization,id uuid NOT NULL,actor_id uuid NOT NULL REFERENCES actor,
      scope jsonb NOT NULL,state text NOT NULL DEFAULT 'ready',dataset text NOT NULL DEFAULT 'official' CHECK(dataset IN ('official','synthetic')),
      pages int NOT NULL DEFAULT 0,records int NOT NULL DEFAULT 0,source_requests int NOT NULL DEFAULT 0,
      resume_after timestamptz,error_code text,created_at timestamptz NOT NULL DEFAULT now(),updated_at timestamptz NOT NULL DEFAULT now(),
      PRIMARY KEY(org_id,id));
    CREATE TABLE history_task(
      org_id uuid NOT NULL,collection_id uuid NOT NULL,id uuid NOT NULL,task_key text NOT NULL,
      provider text NOT NULL,arguments jsonb NOT NULL,state text NOT NULL DEFAULT 'ready',
      attempts int NOT NULL DEFAULT 0,lease_until timestamptz,error_code text,
      PRIMARY KEY(org_id,id),UNIQUE(org_id,collection_id,task_key),
      FOREIGN KEY(org_id,collection_id) REFERENCES history_collection);
    CREATE INDEX history_queue ON history_task(org_id,collection_id,state);
    CREATE TABLE history_page(
      org_id uuid NOT NULL,collection_id uuid NOT NULL,task_id uuid NOT NULL,source_id uuid NOT NULL REFERENCES source_observation,
      record_count int NOT NULL,result jsonb NOT NULL,created_at timestamptz NOT NULL DEFAULT now(),
      PRIMARY KEY(org_id,task_id),FOREIGN KEY(org_id,task_id) REFERENCES history_task,
      FOREIGN KEY(org_id,collection_id) REFERENCES history_collection);
    CREATE TABLE opportunity_equivalence(
      org_id uuid NOT NULL REFERENCES organization,id uuid NOT NULL,name text NOT NULL,category text NOT NULL,
      unit text NOT NULL,members jsonb NOT NULL,justification text NOT NULL,evidence text NOT NULL,
      reviewed_by uuid NOT NULL REFERENCES actor,created_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(org_id,id));
    CREATE TABLE opportunity_review(
      org_id uuid NOT NULL REFERENCES organization,opportunity_key text NOT NULL,revision int NOT NULL,
      data jsonb NOT NULL,actor_id uuid NOT NULL REFERENCES actor,created_at timestamptz NOT NULL DEFAULT now(),
      PRIMARY KEY(org_id,opportunity_key,revision));
    CREATE TABLE opportunity_watch(
      org_id uuid NOT NULL REFERENCES organization,id uuid NOT NULL,actor_id uuid NOT NULL REFERENCES actor,
      name text NOT NULL,filters jsonb NOT NULL,seen jsonb NOT NULL DEFAULT '{}',active boolean NOT NULL DEFAULT true,
      created_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(org_id,id));
    CREATE TABLE opportunity_alert(
      org_id uuid NOT NULL,id uuid NOT NULL,watch_id uuid NOT NULL,actor_id uuid NOT NULL REFERENCES actor,
      fact_id uuid NOT NULL REFERENCES procurement_fact,event_identity text NOT NULL,revision_hash text NOT NULL,
      kind text NOT NULL,before jsonb,after jsonb NOT NULL,created_at timestamptz NOT NULL DEFAULT now(),
      PRIMARY KEY(org_id,id),UNIQUE(org_id,watch_id,event_identity,revision_hash),
      FOREIGN KEY(org_id,watch_id) REFERENCES opportunity_watch);
    CREATE INDEX opportunity_fact_history ON procurement_fact(classification,phase,event_date,item_id) WHERE is_current;
    """)
    for name in TABLES:
        conn.execute(f"ALTER TABLE {name} ENABLE ROW LEVEL SECURITY; ALTER TABLE {name} FORCE ROW LEVEL SECURITY;")
        conn.execute(f"CREATE POLICY tenant_scope ON {name} USING(org_id=nullif(current_setting('irps.org_id',true),'')::uuid) WITH CHECK(org_id=nullif(current_setting('irps.org_id',true),'')::uuid);")
        conn.execute(f'GRANT SELECT,INSERT ON {name} TO irps_app;')
    for name in ('history_collection', 'history_task', 'opportunity_watch'):
        conn.execute(f'GRANT UPDATE ON {name} TO irps_app;')
    for name in ('history_page', 'opportunity_equivalence', 'opportunity_review', 'opportunity_alert'):
        conn.execute(f'CREATE TRIGGER immutable_{name} BEFORE UPDATE OR DELETE ON {name} FOR EACH ROW EXECUTE FUNCTION irps_deny_mutation();')

def downgrade():
    conn = op.get_bind().connection.driver_connection
    conn.execute('DROP INDEX opportunity_fact_history;')
    for name in reversed(TABLES):
        conn.execute(f'DROP TABLE {name};')
