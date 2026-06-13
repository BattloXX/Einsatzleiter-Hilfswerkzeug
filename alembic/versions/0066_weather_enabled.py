"""Org-spezifisches Wetter-Flag in OrgSettings

Revision ID: 0066
Revises: 0065
Create Date: 2026-06-13
"""
from alembic import op
from sqlalchemy import text

revision = "0066"
down_revision = "0065"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute(text("""
        ALTER TABLE org_settings
            ADD COLUMN weather_enabled TINYINT(1) NULL DEFAULT NULL
    """))


def downgrade():
    conn = op.get_bind()
    conn.execute(text("ALTER TABLE org_settings DROP COLUMN weather_enabled"))
