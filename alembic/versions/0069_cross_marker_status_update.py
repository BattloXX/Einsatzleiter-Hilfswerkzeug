"""CrossSiteMarker: neues Status-Set (unbestaetigt/aktiv/in_bearbeitung/beobachtung/behoben)

Revision ID: 0069
Revises: 0068
Create Date: 2026-06-13
"""
from alembic import op
from sqlalchemy import text

revision = "0069"
down_revision = "0068"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    # Alte Status-Werte auf neues Set migrieren
    conn.execute(text("""
        UPDATE cross_site_marker SET status = 'unbestaetigt' WHERE status = 'gemeldet'
    """))
    conn.execute(text("""
        UPDATE cross_site_marker SET status = 'aktiv' WHERE status = 'bestaetigt'
    """))
    conn.execute(text("""
        UPDATE cross_site_marker SET status = 'behoben' WHERE status = 'aufgehoben'
    """))
    # Spalten-Default aktualisieren
    conn.execute(text("""
        ALTER TABLE cross_site_marker
        ALTER COLUMN status SET DEFAULT 'aktiv'
    """))


def downgrade():
    conn = op.get_bind()
    conn.execute(text("""
        UPDATE cross_site_marker SET status = 'gemeldet' WHERE status = 'unbestaetigt'
    """))
    conn.execute(text("""
        UPDATE cross_site_marker SET status = 'bestaetigt' WHERE status = 'aktiv'
    """))
    conn.execute(text("""
        UPDATE cross_site_marker SET status = 'aufgehoben' WHERE status = 'beobachtung'
    """))
    conn.execute(text("""
        ALTER TABLE cross_site_marker
        ALTER COLUMN status SET DEFAULT 'gemeldet'
    """))
