"""fire_dept: short_code (3-Zeichen-Kürzel für Fahrzeugdarstellung)

Revision ID: 0024
Revises: 0023
Create Date: 2026-05-30 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect as sa_inspect

revision = "0024"
down_revision = "0023"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    insp = sa_inspect(conn)
    cols = [c["name"] for c in insp.get_columns("fire_dept")]
    if "short_code" not in cols:
        with op.batch_alter_table("fire_dept", schema=None) as batch_op:
            batch_op.add_column(sa.Column("short_code", sa.String(3), nullable=True))


def downgrade():
    with op.batch_alter_table("fire_dept", schema=None) as batch_op:
        batch_op.drop_column("short_code")
