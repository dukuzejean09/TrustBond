"""Add incident_group_id to reports and expose IncidentGroup metadata

Revision ID: 1f6a9b7c3d4e
Revises: 8249aed786d3
Create Date: 2026-04-15 00:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "1f6a9b7c3d4e"
down_revision: Union[str, None] = "8249aed786d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "reports",
        sa.Column("incident_group_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(
        "ix_reports_incident_group_id",
        "reports",
        ["incident_group_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_reports_incident_group_id_incident_groups",
        "reports",
        "incident_groups",
        ["incident_group_id"],
        ["group_id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_reports_incident_group_id_incident_groups",
        "reports",
        type_="foreignkey",
    )
    op.drop_index("ix_reports_incident_group_id", table_name="reports")
    op.drop_column("reports", "incident_group_id")
