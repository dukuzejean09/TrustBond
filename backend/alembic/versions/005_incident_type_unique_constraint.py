"""Add unique constraint to incident_types.type_name

Revision ID: 007
Revises: 006
Create Date: 2026-02-27 20:10:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'uq_incident_types_type_name'
            ) THEN
                ALTER TABLE incident_types
                ADD CONSTRAINT uq_incident_types_type_name UNIQUE (type_name);
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE incident_types
        DROP CONSTRAINT IF EXISTS uq_incident_types_type_name;
        """
    )

