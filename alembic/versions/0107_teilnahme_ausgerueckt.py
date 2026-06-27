"""Teilnahme: ausgerueckt-Flag fuer Einsaetze

Revision ID: 0107
Revises: 0106
Create Date: 2026-06-27
"""
from alembic import op
from sqlalchemy import text

revision = "0107"
down_revision = "0106"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(text("""
        ALTER TABLE `teilnahme`
        ADD COLUMN `ausgerueckt` TINYINT(1) NOT NULL DEFAULT 0
        AFTER `notiz`
    """))


def downgrade() -> None:
    op.execute(text("ALTER TABLE `teilnahme` DROP COLUMN `ausgerueckt`"))
