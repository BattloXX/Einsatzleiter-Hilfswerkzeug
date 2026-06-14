"""Reclassify old resource journal entries to ressource/ressource_fhr categories.

Revision ID: 0075
Revises: 0074_gsl_leader_history
Create Date: 2026-06-14
"""
from alembic import op
import sqlalchemy as sa

revision = '0075'
down_revision = '0074'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ressource-Aktionen (Zuweisung, Status, Pool) → 'ressource'
    op.execute(sa.text("""
        UPDATE lage_journal_entry
        SET category = 'ressource'
        WHERE category IN ('anweisung', 'sonstiges')
          AND (
            text LIKE '% -> Abschnitt "%'
            OR text LIKE '% -> Einsatzstelle "%'
            OR text LIKE '% → Pool/Reserve zurückgeführt%'
            OR text LIKE 'Ressource hinzugefügt:%'
            OR text LIKE '%: Status % → %'
          )
    """))

    # Führungswechsel (Einheitsführer, EL, AbsLtr) → 'ressource_fhr'
    op.execute(sa.text("""
        UPDATE lage_journal_entry
        SET category = 'ressource_fhr'
        WHERE category IN ('entscheidung', 'sonstiges')
          AND (
            text LIKE '%: Einheitsführer →%'
            OR text LIKE 'Einsatzleiter →%'
            OR text LIKE 'Abschnittsleiter Abschnitt%→%'
          )
    """))


def downgrade() -> None:
    # Not reversible without tracking original categories
    pass
