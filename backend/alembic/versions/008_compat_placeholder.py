"""Compatibility placeholder for legacy revision 008

Revision ID: 008
Revises: 006
Create Date: 2026-03-17 12:40:00

This migration intentionally does nothing. It exists so databases
already stamped at revision '008' can be recognized by Alembic.
"""
from typing import Sequence, Union

revision: str = "008"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
