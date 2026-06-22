"""verleih_artikel_status – Verfuegbarkeitsstatus fuer eindeutige Artikel

Revision ID: 0095
Revises: 0094
Create Date: 2026-06-22
"""
from alembic import op
from sqlalchemy import text

revision = "0095"
down_revision = "0094"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("""
        ALTER TABLE verleih_artikel
            ADD COLUMN verfuegbarkeit VARCHAR(20) NULL
    """))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("""
        ALTER TABLE verleih_artikel
            DROP COLUMN verfuegbarkeit
    """))
