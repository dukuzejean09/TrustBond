"""Add system_config table

Revision ID: 011
Revises: 010
Create Date: 2026-03-17 13:32:00
"""
from typing import Sequence, Union

from alembic import op

revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS system_config (
            config_key VARCHAR(100) PRIMARY KEY,
            config_value JSONB NOT NULL,
            description VARCHAR,
            updated_by INTEGER REFERENCES police_users(police_user_id),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS system_config")
