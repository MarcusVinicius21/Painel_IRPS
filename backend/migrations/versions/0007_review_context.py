"""Bind human opportunity reviews to the exact assessed context."""
from alembic import op

revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = None

def upgrade():
    op.execute("ALTER TABLE opportunity_review ADD COLUMN context_fingerprint char(64)")
    op.execute("ALTER TABLE opportunity_review ADD CONSTRAINT review_context_sha256 CHECK (context_fingerprint IS NULL OR context_fingerprint ~ '^[0-9a-f]{64}$')")

def downgrade():
    op.execute("ALTER TABLE opportunity_review DROP CONSTRAINT review_context_sha256")
    op.execute("ALTER TABLE opportunity_review DROP COLUMN context_fingerprint")
