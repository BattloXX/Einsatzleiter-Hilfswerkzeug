"""orgsettings_abfluss – Pegelmessstationen als JSON-Text

Revision ID: 0094
Revises: 0093
Create Date: 2026-06-22
"""
from alembic import op
from sqlalchemy import text

revision = "0094"
down_revision = "0093"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("""
        ALTER TABLE org_settings
            ADD COLUMN abfluss_stationen TEXT NULL
    """))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("""
        ALTER TABLE org_settings
            DROP COLUMN abfluss_stationen
    """))
