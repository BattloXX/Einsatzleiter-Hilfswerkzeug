"""CrossSiteMarker: Notizen (log_entry) und Medien (media)

Revision ID: 0070
Revises: 0069
Create Date: 2026-06-13
"""
from alembic import op
from sqlalchemy import text

revision = "0070"
down_revision = "0069"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS cross_marker_log_entry (
            id          INT          NOT NULL AUTO_INCREMENT PRIMARY KEY,
            marker_id   INT          NOT NULL,
            ts          DATETIME     NOT NULL,
            user_id     BIGINT       NULL,
            author_name VARCHAR(120) NULL,
            text        TEXT         NOT NULL,
            INDEX ix_cmle_marker (marker_id),
            CONSTRAINT fk_cmle_marker FOREIGN KEY (marker_id)
                REFERENCES cross_site_marker(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """))
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS cross_marker_media (
            id                INT          NOT NULL AUTO_INCREMENT PRIMARY KEY,
            marker_id         INT          NOT NULL,
            stored_filename   VARCHAR(64)  NOT NULL,
            original_filename VARCHAR(255) NOT NULL,
            media_type        VARCHAR(12)  NOT NULL DEFAULT 'image',
            uploaded_at       DATETIME     NOT NULL,
            uploaded_by       BIGINT       NULL,
            author_name       VARCHAR(120) NULL,
            bytes             BIGINT       NOT NULL DEFAULT 0,
            org_id            BIGINT       NULL,
            INDEX ix_cmm_marker (marker_id),
            INDEX ix_cmm_org    (org_id),
            CONSTRAINT fk_cmm_marker FOREIGN KEY (marker_id)
                REFERENCES cross_site_marker(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """))


def downgrade():
    conn = op.get_bind()
    conn.execute(text("DROP TABLE IF EXISTS cross_marker_media"))
    conn.execute(text("DROP TABLE IF EXISTS cross_marker_log_entry"))
