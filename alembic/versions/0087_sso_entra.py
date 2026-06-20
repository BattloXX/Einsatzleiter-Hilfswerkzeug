"""SSO Entra ID – OrgSsoConfig, OrgSsoGroupMap, User-SSO-Spalten, password_hash nullable

Revision ID: 0087
Revises: 0086
Create Date: 2026-06-20 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect as sa_inspect

revision = "0087"
down_revision = "0086"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    # ── user: password_hash nullable, neue SSO-Spalten ───────────────────────
    op.alter_column("user", "password_hash",
                    existing_type=sa.String(255),
                    nullable=True)

    existing_user = {c["name"] for c in sa_inspect(bind).get_columns("user")}
    if "entra_oid" not in existing_user:
        op.add_column("user", sa.Column("entra_oid", sa.String(36), nullable=True))
        op.create_index("ix_user_entra_oid", "user", ["entra_oid"])
    if "entra_tid" not in existing_user:
        op.add_column("user", sa.Column("entra_tid", sa.String(36), nullable=True))
    if "auth_provider" not in existing_user:
        op.add_column("user", sa.Column("auth_provider", sa.String(20),
                                        nullable=False, server_default="local"))

    # ── org_sso_config ────────────────────────────────────────────────────────
    if "org_sso_config" not in sa_inspect(bind).get_table_names():
        op.create_table(
            "org_sso_config",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("org_id", sa.BigInteger(),
                      sa.ForeignKey("fire_dept.id", ondelete="CASCADE"),
                      unique=True, nullable=False),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default="0"),
            sa.Column("tenant_id", sa.String(36), nullable=True),
            sa.Column("client_id", sa.String(36), nullable=True),
            sa.Column("client_secret_enc", sa.Text(), nullable=True),
            sa.Column("authority_base", sa.String(200), nullable=True),
            sa.Column("allowed_domains", sa.String(500), nullable=True),
            sa.Column("default_role_id", sa.Integer(),
                      sa.ForeignKey("role.id"), nullable=True),
            sa.Column("deny_if_no_group", sa.Boolean(), nullable=False, server_default="0"),
            sa.Column("sync_profile", sa.Boolean(), nullable=False, server_default="1"),
            sa.Column("enforce_sso", sa.Boolean(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
        )

    # ── org_sso_group_map ─────────────────────────────────────────────────────
    if "org_sso_group_map" not in sa_inspect(bind).get_table_names():
        op.create_table(
            "org_sso_group_map",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("config_id", sa.Integer(),
                      sa.ForeignKey("org_sso_config.id", ondelete="CASCADE"),
                      nullable=False, index=True),
            sa.Column("entra_group_id", sa.String(36), nullable=False),
            sa.Column("label", sa.String(150), nullable=True),
            sa.Column("role_id", sa.Integer(),
                      sa.ForeignKey("role.id", ondelete="CASCADE"),
                      nullable=False),
        )


def downgrade() -> None:
    bind = op.get_bind()
    tables = sa_inspect(bind).get_table_names()
    if "org_sso_group_map" in tables:
        op.drop_table("org_sso_group_map")
    if "org_sso_config" in tables:
        op.drop_table("org_sso_config")

    existing_user = {c["name"] for c in sa_inspect(bind).get_columns("user")}
    if "auth_provider" in existing_user:
        op.drop_column("user", "auth_provider")
    if "entra_tid" in existing_user:
        op.drop_column("user", "entra_tid")
    if "entra_oid" in existing_user:
        op.drop_index("ix_user_entra_oid", "user")
        op.drop_column("user", "entra_oid")

    # password_hash zurück auf NOT NULL (nur safe wenn keine SSO-User mehr existieren)
    op.alter_column("user", "password_hash",
                    existing_type=sa.String(255),
                    nullable=False,
                    server_default=None)
