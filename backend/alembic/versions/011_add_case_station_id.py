"""Add station_id to cases table

Revision ID: 011
Revises: 010
Create Date: 2026-04-26

Every case is anchored to a station. The station determines which officers can
see the case and ensures incidents are grouped into the correct operational area.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "cases",
        sa.Column(
            "station_id",
            sa.Integer(),
            sa.ForeignKey("stations.station_id"),
            nullable=True,
        ),
    )
    op.create_index("ix_cases_station_id", "cases", ["station_id"])

    # Back-fill station_id for existing cases from the assigned officer's station
    op.execute("""
        UPDATE cases c
        SET station_id = pu.station_id
        FROM police_users pu
        WHERE c.assigned_to_id = pu.police_user_id
          AND c.station_id IS NULL
          AND pu.station_id IS NOT NULL
    """)


def downgrade() -> None:
    op.drop_index("ix_cases_station_id", table_name="cases")
    op.drop_column("cases", "station_id")
