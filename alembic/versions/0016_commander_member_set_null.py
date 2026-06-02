"""SET NULL FK für incident_vehicle.commander_member_id (Mitglieder-Löschen-Bug)

Revision ID: 0016
Revises: 0015
Create Date: 2026-05-25 21:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "incident_vehicle",
        "commander_member_id",
        existing_type=sa.BigInteger(),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "incident_vehicle",
        "commander_member_id",
        existing_type=sa.BigInteger(),
        nullable=True,
    )
