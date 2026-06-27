"""Teilnehmerlisten: Termin, Funktion, Teilnahme + Seed

Revision ID: 0106
Revises: 0105
Create Date: 2026-06-27
"""
from alembic import op
from sqlalchemy import text

revision = "0106"
down_revision = "0105"
branch_labels = None
depends_on = None

_STANDARD_FUNKTIONEN = [
    (1, "Einsatzleiter"),
    (2, "Gruppenkommandant"),
    (3, "Maschinist"),
    (4, "Atemschutztraeger"),
    (5, "Melder"),
    (6, "Fahrer"),
    (7, "Truppfuehrer"),
    (8, "Truppmann"),
    (9, "Sanitaeter"),
    (10, "Sonstige"),
]

_STANDARD_FUNKTIONEN_NAMES = [
    "Einsatzleiter",
    "Gruppenkommandant",
    "Maschinist",
    "Atemschutzträger",
    "Melder",
    "Fahrer",
    "Truppführer",
    "Truppmann",
    "Sanitäter",
    "Sonstige",
]


def upgrade() -> None:
    op.execute(text("""
        CREATE TABLE IF NOT EXISTS `termin` (
            `id`            BIGINT       NOT NULL AUTO_INCREMENT,
            `org_id`        BIGINT       NULL,
            `typ`           ENUM('uebung','veranstaltung') NOT NULL,
            `titel`         VARCHAR(200) NOT NULL,
            `beschreibung`  LONGTEXT     NULL,
            `ort`           VARCHAR(200) NULL,
            `beginn`        DATETIME     NOT NULL,
            `ende`          DATETIME     NULL,
            `ganztaegig`    TINYINT(1)   NOT NULL DEFAULT 0,
            `status`        ENUM('geplant','laufend','abgeschlossen','abgesagt') NOT NULL DEFAULT 'geplant',
            `erstellt_von`  BIGINT       NULL,
            `erstellt_am`   DATETIME     NOT NULL,
            PRIMARY KEY (`id`),
            INDEX `ix_termin_org_id`    (`org_id`),
            INDEX `ix_termin_typ_beginn` (`org_id`, `typ`, `beginn`),
            CONSTRAINT `fk_termin_org`  FOREIGN KEY (`org_id`)
                REFERENCES `fire_dept` (`id`) ON DELETE SET NULL,
            CONSTRAINT `fk_termin_user` FOREIGN KEY (`erstellt_von`)
                REFERENCES `user` (`id`) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """))

    op.execute(text("""
        CREATE TABLE IF NOT EXISTS `funktion` (
            `id`          BIGINT       NOT NULL AUTO_INCREMENT,
            `org_id`      BIGINT       NULL,
            `name`        VARCHAR(100) NOT NULL,
            `sortierung`  INT          NOT NULL DEFAULT 0,
            `aktiv`       TINYINT(1)   NOT NULL DEFAULT 1,
            PRIMARY KEY (`id`),
            INDEX `ix_funktion_org_id` (`org_id`),
            CONSTRAINT `fk_funktion_org` FOREIGN KEY (`org_id`)
                REFERENCES `fire_dept` (`id`) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """))

    op.execute(text("""
        CREATE TABLE IF NOT EXISTS `teilnahme` (
            `id`                BIGINT       NOT NULL AUTO_INCREMENT,
            `org_id`            BIGINT       NULL,
            `bezug_typ`         ENUM('einsatz','uebung','veranstaltung') NOT NULL,
            `bezug_id`          BIGINT       NOT NULL,
            `mitglied_id`       BIGINT       NULL,
            `freitext_name`     VARCHAR(200) NULL,
            `funktion_id`       BIGINT       NULL,
            `fahrzeug_id`       BIGINT       NULL,
            `notiz`             VARCHAR(255) NULL,
            `hinzugefuegt_von`  BIGINT       NULL,
            `hinzugefuegt_am`   DATETIME     NOT NULL,
            PRIMARY KEY (`id`),
            UNIQUE KEY `uq_teilnahme_mitglied` (`org_id`, `bezug_typ`, `bezug_id`, `mitglied_id`),
            INDEX `ix_teilnahme_org_bezug` (`org_id`, `bezug_typ`, `bezug_id`),
            CONSTRAINT `fk_teilnahme_org`      FOREIGN KEY (`org_id`)
                REFERENCES `fire_dept` (`id`) ON DELETE SET NULL,
            CONSTRAINT `fk_teilnahme_mitglied` FOREIGN KEY (`mitglied_id`)
                REFERENCES `member` (`id`) ON DELETE CASCADE,
            CONSTRAINT `fk_teilnahme_funktion` FOREIGN KEY (`funktion_id`)
                REFERENCES `funktion` (`id`) ON DELETE SET NULL,
            CONSTRAINT `fk_teilnahme_fahrzeug` FOREIGN KEY (`fahrzeug_id`)
                REFERENCES `vehicle_master` (`id`) ON DELETE SET NULL,
            CONSTRAINT `fk_teilnahme_user`     FOREIGN KEY (`hinzugefuegt_von`)
                REFERENCES `user` (`id`) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """))

    # Seed Standardfunktionen für alle bestehenden Orgs
    for i, name in enumerate(_STANDARD_FUNKTIONEN_NAMES, start=1):
        op.execute(text(f"""
            INSERT INTO `funktion` (`org_id`, `name`, `sortierung`, `aktiv`)
            SELECT `id`, '{name}', {i}, 1
            FROM `fire_dept`
            WHERE NOT EXISTS (
                SELECT 1 FROM `funktion` f2
                WHERE f2.`org_id` = `fire_dept`.`id`
                  AND f2.`name` = '{name}'
            )
        """))


def downgrade() -> None:
    op.execute(text("DROP TABLE IF EXISTS `teilnahme`"))
    op.execute(text("DROP TABLE IF EXISTS `funktion`"))
    op.execute(text("DROP TABLE IF EXISTS `termin`"))
