"""fcm_token: FCM Registration Tokens für native Android-Push

Revision ID: 0025
Revises: 0024
Create Date: 2026-05-30 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect as sa_inspect

revision = "0025"
down_revision = "0024"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    insp = sa_inspect(conn)
    tables = insp.get_table_names()

    # Neue Tabelle fcm_token
    if "fcm_token" not in tables:
        op.create_table(
            "fcm_token",
            sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.BigInteger, sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
            sa.Column("device_token_id", sa.BigInteger, sa.ForeignKey("device_token.id", ondelete="SET NULL"), nullable=True),
            sa.Column("token", sa.String(512), unique=True, nullable=False),
            sa.Column("platform", sa.String(20), nullable=False, server_default="android"),
            sa.Column("created_at", sa.DateTime, nullable=False),
            sa.Column("last_used_at", sa.DateTime, nullable=True),
        )

    # device_token: location fields + duty_active
    dt_cols = [c["name"] for c in insp.get_columns("device_token")]
    with op.batch_alter_table("device_token", schema=None) as batch_op:
        if "last_lat" not in dt_cols:
            batch_op.add_column(sa.Column("last_lat", sa.Float, nullable=True))
        if "last_lng" not in dt_cols:
            batch_op.add_column(sa.Column("last_lng", sa.Float, nullable=True))
        if "last_location_at" not in dt_cols:
            batch_op.add_column(sa.Column("last_location_at", sa.DateTime, nullable=True))
        if "duty_active" not in dt_cols:
            batch_op.add_column(sa.Column("duty_active", sa.Boolean, nullable=False, server_default="0"))


def downgrade():
    op.drop_table("fcm_token")
    with op.batch_alter_table("device_token", schema=None) as batch_op:
        batch_op.drop_column("duty_active")
        batch_op.drop_column("last_location_at")
        batch_op.drop_column("last_lng")
        batch_op.drop_column("last_lat")
