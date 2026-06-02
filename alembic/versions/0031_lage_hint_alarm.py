"""Alarmstichwort-Zuweisung für Lage-Hinweise

Revision ID: 0031
Revises: 0030
Create Date: 2026-06-02 23:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "0031"
down_revision = "0030"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "lage_hint_alarm",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "lage_hint_id",
            sa.Integer(),
            sa.ForeignKey("lage_hint.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "alarm_type_code",
            sa.String(10),
            sa.ForeignKey("alarm_type.code", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8mb4",
        mysql_engine="InnoDB",
    )


def downgrade() -> None:
    op.drop_table("lage_hint_alarm")
