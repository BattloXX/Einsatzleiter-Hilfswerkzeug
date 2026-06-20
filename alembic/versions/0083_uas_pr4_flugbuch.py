"""uas PR 4 – uas_flug und uas_checkliste

Revision ID: 0083
Revises: 0082
Create Date: 2026-06-20
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision = "0083"
down_revision = "0082"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("""
        CREATE TABLE uas_flug (
            id                      BIGINT NOT NULL AUTO_INCREMENT,
            org_id                  BIGINT NOT NULL,
            uas_einsatz_id          BIGINT NOT NULL,
            lfd_nr                  INT NOT NULL DEFAULT 1,
            datum                   DATE NOT NULL,
            pilot_id                BIGINT NULL,
            device_id               BIGINT NULL,
            start_ort               VARCHAR(200) NULL,
            landung_ort             VARCHAR(200) NULL,
            start_at                DATETIME NULL,
            landung_at              DATETIME NULL,
            dauer_min               INT NULL,
            durchfuehrung           VARCHAR(10) NOT NULL DEFAULT 'vlos',
            payload                 JSON NULL,
            grundlage               VARCHAR(20) NOT NULL DEFAULT 'open_a1',
            bescheid_nr             VARCHAR(100) NULL,
            geplante_flughoehe_m    FLOAT NULL,
            contingency_volume_m    FLOAT NULL,
            ground_risk_buffer_m    FLOAT NULL,
            abstand_menschenansammlung_m FLOAT NULL,
            flughoehe_konform       TINYINT(1) NOT NULL DEFAULT 0,
            nachtbetrieb            TINYINT(1) NOT NULL DEFAULT 0,
            beleuchtung_bestaetigt  TINYINT(1) NOT NULL DEFAULT 0,
            gesamteinsatzleiter     VARCHAR(150) NULL,
            einsatzleiter_drohne    VARCHAR(150) NULL,
            unfall                  TINYINT(1) NOT NULL DEFAULT 0,
            bemerkungen             TEXT NULL,
            status                  VARCHAR(15) NOT NULL DEFAULT 'offen',
            inhalt_hash             VARCHAR(64) NULL,
            created_at              DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at              DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            INDEX ix_uas_flug_einsatz (uas_einsatz_id),
            INDEX ix_uas_flug_org (org_id),
            INDEX ix_uas_flug_pilot (pilot_id),
            CONSTRAINT fk_uas_flug_einsatz FOREIGN KEY (uas_einsatz_id)
                REFERENCES uas_einsatz(id) ON DELETE RESTRICT,
            CONSTRAINT fk_uas_flug_pilot FOREIGN KEY (pilot_id)
                REFERENCES uas_pilot(id) ON DELETE SET NULL,
            CONSTRAINT fk_uas_flug_device FOREIGN KEY (device_id)
                REFERENCES uas_device(id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """))

    conn.execute(text("""
        CREATE TABLE uas_checkliste (
            id                      BIGINT NOT NULL AUTO_INCREMENT,
            org_id                  BIGINT NOT NULL,
            uas_flug_id             BIGINT NOT NULL,
            typ                     VARCHAR(15) NOT NULL DEFAULT 'vorflug',
            punkte                  JSON NULL,
            erledigt_von_pilot      VARCHAR(150) NULL,
            erledigt_von_zweitperson VARCHAR(150) NULL,
            abgeschlossen_at        DATETIME NULL,
            created_at              DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            INDEX ix_uas_checkliste_flug (uas_flug_id),
            INDEX ix_uas_checkliste_org (org_id),
            CONSTRAINT fk_uas_checkliste_flug FOREIGN KEY (uas_flug_id)
                REFERENCES uas_flug(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """))

    # FK von uas_flugbewegung.uas_flug_id nachrüsten
    conn.execute(text("""
        ALTER TABLE uas_flugbewegung
        ADD CONSTRAINT fk_uas_flugbewegung_flug
            FOREIGN KEY (uas_flug_id) REFERENCES uas_flug(id) ON DELETE SET NULL
    """))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("ALTER TABLE uas_flugbewegung DROP FOREIGN KEY fk_uas_flugbewegung_flug"))
    conn.execute(text("DROP TABLE IF EXISTS uas_checkliste"))
    conn.execute(text("DROP TABLE IF EXISTS uas_flug"))
