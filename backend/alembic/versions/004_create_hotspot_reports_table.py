"""Create hotspot_reports association table

Revision ID: 004
Revises: 003
Create Date: 2026-03-17 20:00:01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Table may already exist if created by migration 001 — skip if so.
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if not inspector.has_table("hotspot_reports"):
        op.create_table(
            "hotspot_reports",
            sa.Column("hotspot_id", sa.Integer, sa.ForeignKey("hotspots.hotspot_id"), primary_key=True),
            sa.Column("report_id", sa.UUID(as_uuid=True), sa.ForeignKey("reports.report_id"), primary_key=True),
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if inspector.has_table("hotspot_reports"):
        op.drop_table("hotspot_reports")
