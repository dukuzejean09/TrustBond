"""Add stations table and station link columns

Revision ID: 009
Revises: 008
Create Date: 2026-03-17 12:50:00
"""
from typing import Sequence, Union

from alembic import op

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS stations (
            station_id SERIAL PRIMARY KEY,
            station_code VARCHAR(50) NOT NULL UNIQUE,
            station_name VARCHAR(150) NOT NULL,
            station_type VARCHAR(30) NOT NULL,
            location_id INTEGER REFERENCES locations(location_id),
            latitude NUMERIC(10, 7),
            longitude NUMERIC(10, 7),
            address_text VARCHAR,
            phone_number VARCHAR(50),
            email VARCHAR(255),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name='police_users' AND column_name='station_id'
            ) THEN
                ALTER TABLE police_users ADD COLUMN station_id INTEGER;
            END IF;

            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname='fk_police_users_station_id'
            ) THEN
                ALTER TABLE police_users
                ADD CONSTRAINT fk_police_users_station_id
                FOREIGN KEY (station_id) REFERENCES stations(station_id);
            END IF;
        END $$;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name='reports' AND column_name='handling_station_id'
            ) THEN
                ALTER TABLE reports ADD COLUMN handling_station_id INTEGER;
            END IF;

            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname='fk_reports_handling_station_id'
            ) THEN
                ALTER TABLE reports
                ADD CONSTRAINT fk_reports_handling_station_id
                FOREIGN KEY (handling_station_id) REFERENCES stations(station_id);
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname='fk_reports_handling_station_id'
            ) THEN
                ALTER TABLE reports DROP CONSTRAINT fk_reports_handling_station_id;
            END IF;
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='reports' AND column_name='handling_station_id'
            ) THEN
                ALTER TABLE reports DROP COLUMN handling_station_id;
            END IF;

            IF EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname='fk_police_users_station_id'
            ) THEN
                ALTER TABLE police_users DROP CONSTRAINT fk_police_users_station_id;
            END IF;
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='police_users' AND column_name='station_id'
            ) THEN
                ALTER TABLE police_users DROP COLUMN station_id;
            END IF;
        END $$;
        """
    )

    op.execute("DROP TABLE IF EXISTS stations")
