"""Merge case history and auto-grouping migration heads

Revision ID: 012_merge_heads
Revises: 011, 010_auto_grouping_case_metadata
Create Date: 2026-04-27
"""

from typing import Sequence, Union


revision: str = "012_merge_heads"
down_revision: Union[str, Sequence[str], None] = ("011", "010_auto_grouping_case_metadata")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
