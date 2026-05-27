"""Füge unit_name-Feld zu breathing_troop hinzu

Revision ID: 0017
Revises: 0016
Create Date: 2026-05-27 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("breathing_troop") as batch:
        batch.add_column(sa.Column("unit_name", sa.String(100), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("breathing_troop") as batch:
        batch.drop_column("unit_name")
