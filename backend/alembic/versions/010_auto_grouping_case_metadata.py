"""Add incident-group links and auto-case metadata

Revision ID: 010_auto_grouping_case_metadata
Revises: 8249aed786d3
Create Date: 2026-04-09 15:50:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "010_auto_grouping_case_metadata"
down_revision = "8249aed786d3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "incident_groups",
        sa.Column("distinct_device_count", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "incident_groups",
        sa.Column("radius_meters", sa.Numeric(precision=8, scale=2), nullable=True),
    )
    op.add_column(
        "incident_groups",
        sa.Column("confidence_score", sa.Numeric(precision=5, scale=2), nullable=True),
    )
    op.add_column(
        "incident_groups",
        sa.Column("grouping_method", sa.String(length=50), nullable=False, server_default="ai_auto_grouped"),
    )
    op.add_column(
        "incident_groups",
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "incident_groups",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )

    op.add_column(
        "reports",
        sa.Column("incident_group_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "reports_incident_group_id_fkey",
        "reports",
        "incident_groups",
        ["incident_group_id"],
        ["group_id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_reports_incident_group_id", "reports", ["incident_group_id"], unique=False)

    op.add_column(
        "cases",
        sa.Column("incident_group_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "cases",
        sa.Column("device_count", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "cases",
        sa.Column("auto_created", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "cases",
        sa.Column("source", sa.String(length=30), nullable=False, server_default="manual"),
    )
    op.add_column(
        "cases",
        sa.Column("auto_group_confidence", sa.Numeric(precision=5, scale=2), nullable=True),
    )
    op.create_foreign_key(
        "cases_incident_group_id_fkey",
        "cases",
        "incident_groups",
        ["incident_group_id"],
        ["group_id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_cases_incident_group_id", "cases", ["incident_group_id"], unique=True)

    op.execute(
        """
        UPDATE incident_groups
        SET distinct_device_count = GREATEST(COALESCE(report_count, 0), 1)
        WHERE distinct_device_count IS NULL OR distinct_device_count = 1
        """
    )
    op.execute(
        """
        UPDATE cases AS c
        SET device_count = COALESCE(stats.device_count, CASE WHEN COALESCE(c.report_count, 0) > 0 THEN 1 ELSE 0 END)
        FROM (
            SELECT cr.case_id, COUNT(DISTINCT r.device_id) AS device_count
            FROM case_reports AS cr
            JOIN reports AS r ON r.report_id = cr.report_id
            GROUP BY cr.case_id
        ) AS stats
        WHERE c.case_id = stats.case_id
        """
    )

    op.alter_column("incident_groups", "distinct_device_count", server_default=None)
    op.alter_column("incident_groups", "grouping_method", server_default=None)
    op.alter_column("incident_groups", "is_active", server_default=None)
    op.alter_column("cases", "device_count", server_default=None)
    op.alter_column("cases", "auto_created", server_default=None)
    op.alter_column("cases", "source", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_cases_incident_group_id", table_name="cases")
    op.drop_constraint("cases_incident_group_id_fkey", "cases", type_="foreignkey")
    op.drop_column("cases", "auto_group_confidence")
    op.drop_column("cases", "source")
    op.drop_column("cases", "auto_created")
    op.drop_column("cases", "device_count")
    op.drop_column("cases", "incident_group_id")

    op.drop_index("ix_reports_incident_group_id", table_name="reports")
    op.drop_constraint("reports_incident_group_id_fkey", "reports", type_="foreignkey")
    op.drop_column("reports", "incident_group_id")

    op.drop_column("incident_groups", "is_active")
    op.drop_column("incident_groups", "metadata")
    op.drop_column("incident_groups", "grouping_method")
    op.drop_column("incident_groups", "confidence_score")
    op.drop_column("incident_groups", "radius_meters")
    op.drop_column("incident_groups", "distinct_device_count")
