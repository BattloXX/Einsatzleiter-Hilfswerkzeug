"""org timezone column

Revision ID: 0006
Revises: 0005
Create Date: 2026-05-23 18:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "fire_dept",
        sa.Column("timezone", sa.String(64), nullable=True),
    )
    # Bestehende Orgs auf Europe/Vienna setzen, damit Anzeige sofort lokalisiert ist.
    op.execute("UPDATE fire_dept SET timezone = 'Europe/Vienna' WHERE timezone IS NULL")


def downgrade() -> None:
    op.drop_column("fire_dept", "timezone")
