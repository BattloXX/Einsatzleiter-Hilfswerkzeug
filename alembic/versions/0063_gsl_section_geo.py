"""GSL Abschnitte: Geometrie + Sort-Order auf site_sector

Revision ID: 0063
Revises: 0062
Create Date: 2026-06-12
"""
from alembic import op
from sqlalchemy import text

revision = "0063"
down_revision = "0062"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute(text("""
        ALTER TABLE site_sector
            ADD COLUMN geometry          MEDIUMTEXT NULL,
            ADD COLUMN sort_order        INT        NOT NULL DEFAULT 0,
            ADD COLUMN leader_assignment_id INT     NULL,
            ADD CONSTRAINT fk_sector_leader
                FOREIGN KEY (leader_assignment_id)
                REFERENCES gsl_staff_assignment(id)
                ON DELETE SET NULL
    """))


def downgrade():
    conn = op.get_bind()
    conn.execute(text("ALTER TABLE site_sector DROP FOREIGN KEY fk_sector_leader"))
    conn.execute(text("""
        ALTER TABLE site_sector
            DROP COLUMN leader_assignment_id,
            DROP COLUMN sort_order,
            DROP COLUMN geometry
    """))
