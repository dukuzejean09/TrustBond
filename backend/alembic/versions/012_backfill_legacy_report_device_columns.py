"""Backfill legacy reports/devices columns to match current models

Revision ID: 012
Revises: 011
Create Date: 2026-03-17 14:05:00
"""
from typing import Sequence, Union

from alembic import op

revision: str = "012"
down_revision: Union[str, None] = "011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # reports table: add missing columns used by ORM/API in newer code.
    op.execute(
        """
        ALTER TABLE reports
            ADD COLUMN IF NOT EXISTS report_number VARCHAR(20),
            ADD COLUMN IF NOT EXISTS location_id INTEGER,
            ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'pending',
            ADD COLUMN IF NOT EXISTS flag_reason TEXT,
            ADD COLUMN IF NOT EXISTS verification_status VARCHAR(20) DEFAULT 'pending',
            ADD COLUMN IF NOT EXISTS verified_by INTEGER,
            ADD COLUMN IF NOT EXISTS verified_at TIMESTAMPTZ,
            ADD COLUMN IF NOT EXISTS features_extracted_at TIMESTAMPTZ,
            ADD COLUMN IF NOT EXISTS app_version VARCHAR(50),
            ADD COLUMN IF NOT EXISTS network_type VARCHAR(20),
            ADD COLUMN IF NOT EXISTS battery_level NUMERIC(5,2),
            ADD COLUMN IF NOT EXISTS context_tags VARCHAR[] DEFAULT ARRAY[]::VARCHAR[];
        """
    )

    # Add missing foreign keys only when absent.
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'fk_reports_location_id'
            ) THEN
                ALTER TABLE reports
                ADD CONSTRAINT fk_reports_location_id
                FOREIGN KEY (location_id) REFERENCES locations(location_id);
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'fk_reports_verified_by'
            ) THEN
                ALTER TABLE reports
                ADD CONSTRAINT fk_reports_verified_by
                FOREIGN KEY (verified_by) REFERENCES police_users(police_user_id);
            END IF;
        END $$;
        """
    )

    # Unique index for human-readable report numbers.
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ix_reports_report_number
        ON reports (report_number)
        WHERE report_number IS NOT NULL;
        """
    )

    # Backfill report_number for legacy rows where missing.
    op.execute(
        """
        WITH numbered AS (
            SELECT
                report_id,
                TO_CHAR(COALESCE(reported_at, NOW()) AT TIME ZONE 'UTC', 'YYYY') AS yr,
                ROW_NUMBER() OVER (
                    PARTITION BY TO_CHAR(COALESCE(reported_at, NOW()) AT TIME ZONE 'UTC', 'YYYY')
                    ORDER BY reported_at NULLS LAST, report_id
                ) AS rn
            FROM reports
            WHERE report_number IS NULL
        )
        UPDATE reports r
        SET report_number = 'RPT-' || n.yr || '-' || LPAD(n.rn::TEXT, 4, '0')
        FROM numbered n
        WHERE r.report_id = n.report_id;
        """
    )

    # devices table: add missing moderation column.
    op.execute(
        """
        ALTER TABLE devices
        ADD COLUMN IF NOT EXISTS is_banned BOOLEAN DEFAULT FALSE;
        """
    )


def downgrade() -> None:
    # Safe partial downgrade (keeps data in place by design).
    pass
