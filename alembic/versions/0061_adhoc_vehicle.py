"""Adhoc-Fahrzeug-Flags auf vehicle_master

Revision ID: 0061
Revises: 0060
Create Date: 2026-06-12
"""
from alembic import op
from sqlalchemy import text

revision = "0061"
down_revision = "0060"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute(text("""
        ALTER TABLE vehicle_master
            ADD COLUMN is_adhoc TINYINT(1) NOT NULL DEFAULT 0,
            ADD COLUMN adhoc_org_name VARCHAR(150) NULL,
            ADD COLUMN adhoc_org_short VARCHAR(3) NULL
    """))


def downgrade():
    conn = op.get_bind()
    conn.execute(text("""
        ALTER TABLE vehicle_master
            DROP COLUMN adhoc_org_short,
            DROP COLUMN adhoc_org_name,
            DROP COLUMN is_adhoc
    """))
