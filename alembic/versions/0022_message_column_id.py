"""message: column_id Spalte (Meldungen in andere Spalten verschieben)

Revision ID: 0022
Revises: 0021
Create Date: 2026-05-28 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect as sa_inspect

revision = "0022"
down_revision = "0021"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    insp = sa_inspect(conn)
    cols = [c["name"] for c in insp.get_columns("message")]

    if "column_id" not in cols:
        with op.batch_alter_table("message", schema=None) as batch_op:
            batch_op.add_column(sa.Column("column_id", sa.BigInteger(), nullable=True))
            batch_op.create_foreign_key(
                "fk_message_column_id",
                "incident_column",
                ["column_id"],
                ["id"],
                ondelete="SET NULL",
            )

        # Backfill: set column_id to the 'messages' column of each incident
        conn.execute(sa.text(
            "UPDATE message m "
            "JOIN incident_column ic ON ic.incident_id = m.incident_id AND ic.code = 'messages' "
            "SET m.column_id = ic.id"
        ))


def downgrade():
    with op.batch_alter_table("message", schema=None) as batch_op:
        try:
            batch_op.drop_constraint("fk_message_column_id", type_="foreignkey")
        except Exception:
            pass
        batch_op.drop_column("column_id")
