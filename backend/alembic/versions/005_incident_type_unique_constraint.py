"""Add unique constraint to incident_types.type_name

Revision ID: 005
Revises: 004
Create Date: 2026-02-27 20:10:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_incident_types_type_name",
        "incident_types",
        ["type_name"]
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_incident_types_type_name",
        "incident_types",
        type_="unique"
    )

