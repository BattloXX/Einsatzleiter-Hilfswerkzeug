"""uas PR 8 – uas_medien (Medien & DSGVO-Workflow)

Revision ID: 0086
Revises: 0085
Create Date: 2026-06-20
"""

from alembic import op
from sqlalchemy import text

revision = "0086"
down_revision = "0085"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("""
        CREATE TABLE uas_medien (
            id                  BIGINT NOT NULL AUTO_INCREMENT,
            org_id              BIGINT NOT NULL,
            uas_flug_id         BIGINT NULL,
            uas_einsatz_id      BIGINT NULL,
            dateiname           VARCHAR(512) NOT NULL,
            dateipfad           VARCHAR(1024) NOT NULL,
            medientyp           VARCHAR(30) NOT NULL,
            dsgvo_status        VARCHAR(30) NOT NULL DEFAULT 'erfasst',
            begruendung         TEXT NULL,
            loeschfrist         DATE NULL,
            geloescht_at        DATETIME NULL,
            erstellt_von        VARCHAR(200) NULL,
            created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            INDEX ix_uas_medien_flug (uas_flug_id),
            INDEX ix_uas_medien_einsatz (uas_einsatz_id),
            INDEX ix_uas_medien_org (org_id),
            CONSTRAINT fk_uas_medien_flug FOREIGN KEY (uas_flug_id)
                REFERENCES uas_flug(id) ON DELETE SET NULL,
            CONSTRAINT fk_uas_medien_einsatz FOREIGN KEY (uas_einsatz_id)
                REFERENCES uas_einsatz(id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("DROP TABLE IF EXISTS uas_medien"))
