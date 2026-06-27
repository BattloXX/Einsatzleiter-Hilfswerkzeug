"""Teilnahme: entschuldigt-Flag fuer Uebungen und Veranstaltungen

Revision ID: 0108
Revises: 0107
Create Date: 2026-06-27
"""
from alembic import op
from sqlalchemy import text

revision = "0108"
down_revision = "0107"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(text("""
        ALTER TABLE `teilnahme`
        ADD COLUMN `entschuldigt` TINYINT(1) NOT NULL DEFAULT 0
        AFTER `ausgerueckt`
    """))


def downgrade() -> None:
    op.execute(text("ALTER TABLE `teilnahme` DROP COLUMN `entschuldigt`"))
