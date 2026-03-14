"""Rename rule_status 'passed' to 'classified' and add device trust score columns

Revision ID: 008
Revises: 007
Create Date: 2026-03-13

Update rule_status values from 'passed' -> 'classified' to align with user-facing
terminology. Also adds flagged_reports column to devices if not present.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename rule_status 'passed' -> 'classified' in reports table
    op.execute("UPDATE reports SET rule_status = 'classified' WHERE rule_status = 'passed'")

    # Ensure flagged_reports column exists on devices (idempotent)
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'devices' AND column_name = 'flagged_reports'
            ) THEN
                ALTER TABLE devices ADD COLUMN flagged_reports INTEGER NOT NULL DEFAULT 0;
            END IF;
        END$$;
        """
    )


def downgrade() -> None:
    # Reverse: 'classified' -> 'passed'
    op.execute("UPDATE reports SET rule_status = 'passed' WHERE rule_status = 'classified'")
