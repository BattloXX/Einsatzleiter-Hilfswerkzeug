"""unit_status_reduce: 'Einsatzbereit am Stützpunkt' → 'Einsatzbereit'

Revision ID: 0011
Revises: 0010
Create Date: 2026-05-24 12:00:00.000000
"""
from alembic import op


revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "UPDATE incident_vehicle "
        "SET unit_status='Einsatzbereit' "
        "WHERE unit_status='Einsatzbereit am Stützpunkt'"
    )


def downgrade() -> None:
    pass
