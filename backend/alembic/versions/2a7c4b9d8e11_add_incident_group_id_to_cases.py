"""Add incident_group_id to cases

Revision ID: 2a7c4b9d8e11
Revises: 1f6a9b7c3d4e
Create Date: 2026-04-15 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "2a7c4b9d8e11"
down_revision: Union[str, None] = "1f6a9b7c3d4e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "cases",
        sa.Column("incident_group_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_unique_constraint(
        "uq_cases_incident_group_id",
        "cases",
        ["incident_group_id"],
    )
    op.create_foreign_key(
        "fk_cases_incident_group_id_incident_groups",
        "cases",
        "incident_groups",
        ["incident_group_id"],
        ["group_id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_cases_incident_group_id_incident_groups",
        "cases",
        type_="foreignkey",
    )
    op.drop_constraint(
        "uq_cases_incident_group_id",
        "cases",
        type_="unique",
    )
    op.drop_column("cases", "incident_group_id")
