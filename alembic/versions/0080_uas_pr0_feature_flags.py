"""PR 0: UAS-Modul Feature-Flags (OrgSettings.uas_module_enabled)

Revision ID: 0080
Revises: 0079
Create Date: 2026-06-20
"""
from sqlalchemy import text

from alembic import op

revision = "0080"
down_revision = "0079"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("""
        ALTER TABLE org_settings
            ADD COLUMN uas_module_enabled TINYINT(1) NOT NULL DEFAULT 0
    """))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("ALTER TABLE org_settings DROP COLUMN uas_module_enabled"))
