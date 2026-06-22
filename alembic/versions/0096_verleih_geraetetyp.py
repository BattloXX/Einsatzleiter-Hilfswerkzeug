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


def _col_exists(conn, table: str, column: str) -> bool:
    row = conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t AND COLUMN_NAME = :c"
    ), {"t": table, "c": column}).scalar()
    return bool(row)


def _table_exists(conn, table: str) -> bool:
    row = conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.TABLES "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t"
    ), {"t": table}).scalar()
    return bool(row)


def _index_exists(conn, table: str, index: str) -> bool:
    row = conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.STATISTICS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t AND INDEX_NAME = :i"
    ), {"t": table, "i": index}).scalar()
    return bool(row)


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Neue Tabelle fuer Geraetetypen
    if not _table_exists(conn, "verleih_geraetetyp"):
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
    if not _index_exists(conn, "verleih_geraetetyp", "ix_verleih_geraetetyp_org"):
        conn.execute(text(
            "CREATE INDEX ix_verleih_geraetetyp_org ON verleih_geraetetyp(org_id)"
        ))

    # 2. FK-Spalte in verleih_artikel
    if not _col_exists(conn, "verleih_artikel", "geraetetyp_id"):
        conn.execute(text(
            "ALTER TABLE verleih_artikel ADD COLUMN geraetetyp_id BIGINT NULL"
        ))

    # 3. FK-Spalte in verleih_stueckliste_position
    if not _col_exists(conn, "verleih_stueckliste_position", "geraetetyp_id"):
        conn.execute(text(
            "ALTER TABLE verleih_stueckliste_position ADD COLUMN geraetetyp_id BIGINT NULL"
        ))

    # Eindeutigkeit der Artikelnr wird nur in der Applikationsschicht geprueft
    # (aktive Artikel pro Org). MySQL unterstuetzt keinen partiellen UNIQUE INDEX
    # mit WHERE-Klausel, daher kein DB-Constraint hier.


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("ALTER TABLE verleih_stueckliste_position DROP COLUMN geraetetyp_id"))
    conn.execute(text("ALTER TABLE verleih_artikel DROP COLUMN geraetetyp_id"))
    conn.execute(text("DROP TABLE verleih_geraetetyp"))
