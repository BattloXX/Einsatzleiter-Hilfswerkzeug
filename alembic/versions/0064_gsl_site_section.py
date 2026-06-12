"""GSL Einsatzstelle: section_id + section_assigned_mode

Revision ID: 0064
Revises: 0063
Create Date: 2026-06-12
"""
from alembic import op
from sqlalchemy import text

revision = "0064"
down_revision = "0063"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    # section_id ist ein Alias auf sector_id (neue semantische Spalte für auto/manual Zuweisung)
    conn.execute(text("""
        ALTER TABLE incident_site
            ADD COLUMN section_assigned_mode VARCHAR(8) NOT NULL DEFAULT 'auto'
    """))
    # sector_id ist bereits vorhanden und bleibt die FK-Spalte; section_assigned_mode tracked den Modus


def downgrade():
    conn = op.get_bind()
    conn.execute(text("ALTER TABLE incident_site DROP COLUMN section_assigned_mode"))
