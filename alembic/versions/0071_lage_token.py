"""LageToken: QR-Zugangstokens für Großschadenslage

Revision ID: 0071
Revises: 0070
Create Date: 2026-06-14
"""
from alembic import op
import sqlalchemy as sa

revision = "0071"
down_revision = "0070"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "lage_token",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("lage_id", sa.Integer, sa.ForeignKey("major_incident.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("issued_by_user_id", sa.BigInteger, sa.ForeignKey("user.id"), nullable=False),
        sa.Column("revoked_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )


def downgrade():
    op.drop_table("lage_token")
