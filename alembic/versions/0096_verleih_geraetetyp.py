"""verleih_geraetetyp – Geraetetypen, Artikel-FK, Stueckliste-FK, eindeutige Artikelnr

Revision ID: 0096
Revises: 0095
Create Date: 2026-06-22
"""
from alembic import op
from sqlalchemy import text

revision = "0096"
down_revision = "0095"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Neue Tabelle fuer Geraetetypen
    conn.execute(text("""
        CREATE TABLE verleih_geraetetyp (
            id          BIGINT       NOT NULL AUTO_INCREMENT PRIMARY KEY,
            org_id      BIGINT       NOT NULL,
            name        VARCHAR(200) NOT NULL,
            beschreibung TEXT         NULL,
            aktiv       TINYINT(1)   NOT NULL DEFAULT 1,
            created_at  DATETIME     NOT NULL
        )
    """))
    conn.execute(text(
        "CREATE INDEX ix_verleih_geraetetyp_org ON verleih_geraetetyp(org_id)"
    ))

    # 2. FK-Spalte in verleih_artikel
    conn.execute(text("""
        ALTER TABLE verleih_artikel
            ADD COLUMN geraetetyp_id BIGINT NULL
    """))

    # 3. FK-Spalte in verleih_stueckliste_position
    conn.execute(text("""
        ALTER TABLE verleih_stueckliste_position
            ADD COLUMN geraetetyp_id BIGINT NULL
    """))

    # 4. Duplikate vor dem Unique-Index bereinigen:
    #    Alle (org_id, artikel_nr)-Duplikate erhalten ein Suffix "_2", "_3" usw.
    rows = conn.execute(text("""
        SELECT id, org_id, artikel_nr
        FROM verleih_artikel
        WHERE artikel_nr IS NOT NULL
        ORDER BY org_id, artikel_nr, id
    """)).fetchall()

    seen: dict = {}
    for row in rows:
        rid, org_id, artikel_nr = row[0], row[1], row[2]
        key = (org_id, artikel_nr)
        if key not in seen:
            seen[key] = 1
        else:
            seen[key] += 1
            new_nr = f"{artikel_nr}_{seen[key]}"
            conn.execute(
                text("UPDATE verleih_artikel SET artikel_nr = :nr WHERE id = :id"),
                {"nr": new_nr, "id": rid},
            )

    # 5. Eindeutige Artikelnr pro Org (NULL darf mehrfach vorkommen – MySQL-Standard)
    conn.execute(text("""
        CREATE UNIQUE INDEX ix_verleih_artikel_org_nr
            ON verleih_artikel(org_id, artikel_nr)
    """))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("DROP INDEX ix_verleih_artikel_org_nr ON verleih_artikel"))
    conn.execute(text("ALTER TABLE verleih_stueckliste_position DROP COLUMN geraetetyp_id"))
    conn.execute(text("ALTER TABLE verleih_artikel DROP COLUMN geraetetyp_id"))
    conn.execute(text("DROP TABLE verleih_geraetetyp"))
