"""Add user_sessions table for auth session tracking

Revision ID: 010
Revises: 009
Create Date: 2026-03-17 13:20:00
"""
from typing import Sequence, Union

from alembic import op

revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS user_sessions (
            session_id UUID PRIMARY KEY,
            police_user_id INTEGER NOT NULL REFERENCES police_users(police_user_id),
            refresh_token VARCHAR(512),
            user_agent VARCHAR,
            ip_address VARCHAR,
            expires_at TIMESTAMPTZ NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            revoked_at TIMESTAMPTZ
        );
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS user_sessions")
