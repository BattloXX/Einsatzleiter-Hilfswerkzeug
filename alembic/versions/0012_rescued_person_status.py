"""rescued_person_status: status-Spalte mit Default 'gefunden'

Revision ID: 0012
Revises: 0011
Create Date: 2026-05-24 12:05:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "rescued_person",
        sa.Column("status", sa.String(20), nullable=False, server_default="gefunden"),
    )


def downgrade() -> None:
    op.drop_column("rescued_person", "status")
