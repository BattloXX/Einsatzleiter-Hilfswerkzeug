"""uas_medien – Datei-Upload-Felder (kind, thumb, mime, bytes, dimensions)

Revision ID: 0093
Revises: 0092
Create Date: 2026-06-21
"""
from alembic import op
from sqlalchemy import text

revision = "0093"
down_revision = "0092"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("""
        ALTER TABLE uas_medien
            ADD COLUMN kind              VARCHAR(16)   NULL AFTER dateipfad,
            ADD COLUMN thumb_path        VARCHAR(500)  NULL AFTER kind,
            ADD COLUMN mime_type         VARCHAR(100)  NULL AFTER thumb_path,
            ADD COLUMN bytes             BIGINT        NOT NULL DEFAULT 0 AFTER mime_type,
            ADD COLUMN width             INT           NULL AFTER bytes,
            ADD COLUMN height            INT           NULL AFTER width,
            ADD COLUMN duration_s        DOUBLE        NULL AFTER height,
            ADD COLUMN uploaded_by_user_id BIGINT      NULL AFTER duration_s,
            ADD CONSTRAINT fk_uas_medien_user
                FOREIGN KEY (uploaded_by_user_id) REFERENCES user(id) ON DELETE SET NULL
    """))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("ALTER TABLE uas_medien DROP FOREIGN KEY fk_uas_medien_user"))
    conn.execute(text("""
        ALTER TABLE uas_medien
            DROP COLUMN kind,
            DROP COLUMN thumb_path,
            DROP COLUMN mime_type,
            DROP COLUMN bytes,
            DROP COLUMN width,
            DROP COLUMN height,
            DROP COLUMN duration_s,
            DROP COLUMN uploaded_by_user_id
    """))
