"""Backfill legacy device columns to match current model

Revision ID: 013
Revises: 012
Create Date: 2026-03-17 14:15:00
"""
from typing import Sequence, Union

from alembic import op

revision: str = "013"
down_revision: Union[str, None] = "012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE devices
            ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMPTZ,
            ADD COLUMN IF NOT EXISTS spam_flags INTEGER DEFAULT 0,
            ADD COLUMN IF NOT EXISTS is_blacklisted BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS blacklist_reason VARCHAR;
        """
    )


def downgrade() -> None:
    # No destructive downgrade for backfill migration.
    pass
