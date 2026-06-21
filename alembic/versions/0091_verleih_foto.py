"""Geräteverleih – Beweis-Fotos je Ausleihe

Revision ID: 0091
Revises: 0090
Create Date: 2026-06-21
"""

from alembic import op
from sqlalchemy import text

revision = "0091"
down_revision = "0090"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS verleih_foto (
            id                BIGINT NOT NULL AUTO_INCREMENT,
            ausleihe_id       BIGINT NOT NULL,
            org_id            BIGINT NULL,
            stored_filename   VARCHAR(64) NOT NULL,
            original_filename VARCHAR(255) NOT NULL,
            bytes             BIGINT NOT NULL DEFAULT 0,
            uploaded_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            uploaded_by       BIGINT NULL,
            PRIMARY KEY (id),
            INDEX ix_verleih_foto_ausleihe (ausleihe_id),
            CONSTRAINT fk_verleih_foto_ausleihe FOREIGN KEY (ausleihe_id)
                REFERENCES verleih_ausleihe(id) ON DELETE CASCADE,
            CONSTRAINT fk_verleih_foto_user FOREIGN KEY (uploaded_by)
                REFERENCES user(id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("DROP TABLE IF EXISTS verleih_foto"))
