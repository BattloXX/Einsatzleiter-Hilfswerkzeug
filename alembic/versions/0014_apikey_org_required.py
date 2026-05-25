"""api_key.org_id wird Pflicht (Backfill auf Home-Org / Wolfurt)

Revision ID: 0014
Revises: 0013
Create Date: 2026-05-25 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) Backfill: alle NULL-org_id-Keys auf die Home-Org setzen
    #    (Fallback: erste fire_dept-Zeile, falls is_home_org nirgends gesetzt ist)
    op.execute(
        """
        UPDATE api_key
        SET org_id = (
            SELECT id FROM fire_dept
            ORDER BY is_home_org DESC, id ASC
            LIMIT 1
        )
        WHERE org_id IS NULL
        """
    )
    # 2) Spalte auf NOT NULL setzen
    op.alter_column(
        "api_key", "org_id",
        existing_type=sa.Integer(),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "api_key", "org_id",
        existing_type=sa.Integer(),
        nullable=True,
    )
