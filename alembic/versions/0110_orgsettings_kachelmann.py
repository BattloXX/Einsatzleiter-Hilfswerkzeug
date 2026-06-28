"""OrgSettings: kachelmann_api_key je Org

Revision ID: 0110
Revises: 0109
Create Date: 2026-06-28
"""
from alembic import op
import sqlalchemy as sa

revision = "0110"
down_revision = "0109"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("org_settings") as batch:
        batch.add_column(
            sa.Column("kachelmann_api_key", sa.String(200), nullable=True),
        )


def downgrade() -> None:
    with op.batch_alter_table("org_settings") as batch:
        batch.drop_column("kachelmann_api_key")
