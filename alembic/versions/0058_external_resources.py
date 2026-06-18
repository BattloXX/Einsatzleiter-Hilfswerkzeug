"""Fremdorganisation-Ressourcen: is_external Flag auf vehicle_master

Revision ID: 0058
Revises: 0057
Create Date: 2026-06-18 00:00:00.000000
"""
from alembic import op
from sqlalchemy import text

revision = "0058"
down_revision = "0057"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute(text("""
        ALTER TABLE vehicle_master
        ADD COLUMN is_external BOOLEAN NOT NULL DEFAULT FALSE
    """))


def downgrade():
    conn = op.get_bind()
    conn.execute(text("ALTER TABLE vehicle_master DROP COLUMN is_external"))
