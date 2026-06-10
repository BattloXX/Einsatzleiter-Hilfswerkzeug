"""Vehicle soft-delete: add deleted flag to vehicle_master

Revision ID: 0042
Revises: 0041
Create Date: 2026-06-10 00:00:00.000000
"""
from alembic import op
from sqlalchemy import text

revision = "0042"
down_revision = "0041"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(text(
        "ALTER TABLE `vehicle_master` ADD COLUMN `deleted` TINYINT(1) NOT NULL DEFAULT 0"
    ))


def downgrade():
    op.execute(text("ALTER TABLE `vehicle_master` DROP COLUMN `deleted`"))
