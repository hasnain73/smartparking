"""add spot_signals table

Revision ID: 0001
Revises:
Create Date: 2026-04-24
"""

from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'signaltype') THEN
                CREATE TYPE signaltype AS ENUM ('free', 'occupied');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'sourcetype') THEN
                CREATE TYPE sourcetype AS ENUM ('user', 'passive');
            END IF;
        END $$;
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS spot_signals (
            id          SERIAL PRIMARY KEY,
            spot_id     UUID NOT NULL REFERENCES parking_spots(id) ON DELETE CASCADE,
            signal_type signaltype NOT NULL,
            source_type sourcetype NOT NULL,
            confidence_score FLOAT NOT NULL DEFAULT 0.5,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS spot_signals")
    op.execute("DROP TYPE IF EXISTS signaltype")
    op.execute("DROP TYPE IF EXISTS sourcetype")
