"""infoscreen_history_hours – Darstellungszeitraum fuer historische Werte im Wetter-Infoscreen

Revision ID: 0102
Revises: 0101
Create Date: 2026-06-24
"""
from sqlalchemy import text

from alembic import op  # noqa: F401

revision = "0102"
down_revision = "0101"
branch_labels = None
depends_on = None


def _col_exists(conn, table: str, col: str) -> bool:
    row = conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t AND COLUMN_NAME = :c"
    ), {"t": table, "c": col}).scalar()
    return bool(row)


def upgrade() -> None:
    conn = op.get_bind()

    if not _col_exists(conn, "org_settings", "infoscreen_history_hours"):
        conn.execute(text(
            "ALTER TABLE org_settings ADD COLUMN infoscreen_history_hours INT NOT NULL DEFAULT 24"
        ))


def downgrade() -> None:
    conn = op.get_bind()

    if _col_exists(conn, "org_settings", "infoscreen_history_hours"):
        conn.execute(text(
            "ALTER TABLE org_settings DROP COLUMN infoscreen_history_hours"
        ))
