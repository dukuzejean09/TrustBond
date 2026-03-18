"""Backfill audit_logs user_agent column

Revision ID: 014
Revises: 013
Create Date: 2026-03-17 14:22:00
"""
from typing import Sequence, Union

from alembic import op

revision: str = "014"
down_revision: Union[str, None] = "013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE audit_logs
        ADD COLUMN IF NOT EXISTS user_agent VARCHAR;
        """
    )


def downgrade() -> None:
    pass
