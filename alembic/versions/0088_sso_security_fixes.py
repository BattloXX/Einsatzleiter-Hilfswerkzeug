"""SSO Security Fixes — allow_email_linking, authority_base-Constraint-Kommentar

Revision ID: 0088
Revises: 0087
Create Date: 2026-06-20 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect as sa_inspect

revision = "0088"
down_revision = "0087"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    existing = {c["name"] for c in sa_inspect(bind).get_columns("org_sso_config")}

    # F-07: allow_email_linking – default False (sicherer Default)
    if "allow_email_linking" not in existing:
        op.add_column("org_sso_config",
                      sa.Column("allow_email_linking", sa.Boolean(),
                                nullable=False, server_default="0"))


def downgrade() -> None:
    bind = op.get_bind()
    existing = {c["name"] for c in sa_inspect(bind).get_columns("org_sso_config")}
    if "allow_email_linking" in existing:
        op.drop_column("org_sso_config", "allow_email_linking")
