"""Add case_history table for case timeline/audit log

Revision ID: 010
Revises: 009
Create Date: 2026-04-26

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "case_history",
        sa.Column(
            "history_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "case_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cases.case_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("details", postgresql.JSONB(), nullable=True),
        sa.Column(
            "performed_by",
            sa.Integer(),
            sa.ForeignKey("police_users.police_user_id"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_case_history_case_id", "case_history", ["case_id"])
    op.create_index("ix_case_history_created_at", "case_history", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_case_history_created_at", table_name="case_history")
    op.drop_index("ix_case_history_case_id", table_name="case_history")
    op.drop_table("case_history")
