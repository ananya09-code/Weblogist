from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("scans", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("url", sa.Text(), nullable=False), sa.Column("normalized_url", sa.Text(), nullable=False), sa.Column("status", sa.String(16), nullable=False), sa.Column("requested_by_ip", sa.String(64)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.Column("started_at", sa.DateTime(timezone=True)), sa.Column("completed_at", sa.DateTime(timezone=True)), sa.Column("error", sa.Text()))
    op.create_index("ix_scans_normalized_url", "scans", ["normalized_url"]); op.create_index("ix_scans_status", "scans", ["status"])
    op.create_table("scan_results", sa.Column("scan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scans.id", ondelete="CASCADE"), primary_key=True), sa.Column("tech_stack", postgresql.JSONB(), nullable=False, server_default="{}"), sa.Column("api_routes", postgresql.JSONB(), nullable=False, server_default="[]"), sa.Column("seo", postgresql.JSONB(), nullable=False, server_default="{}"), sa.Column("performance", postgresql.JSONB(), nullable=False, server_default="{}"), sa.Column("raw_headers", postgresql.JSONB()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()))
def downgrade():
    op.drop_table("scan_results"); op.drop_table("scans")
