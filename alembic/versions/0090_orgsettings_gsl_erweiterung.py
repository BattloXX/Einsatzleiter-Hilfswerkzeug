"""OrgSettings: GSL-Feature-Flags per Org + Geräteverleih-Konfiguration

Revision ID: 0090
Revises: 0089
Create Date: 2026-06-21
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect as sa_inspect

revision = "0090"
down_revision = "0089"
branch_labels = None
depends_on = None

_NEW_COLUMNS = [
    # GSL-Feature-Flags je Org
    ("mi_feature_stab",           sa.Boolean(), "1"),
    ("mi_feature_funkjournal",     sa.Boolean(), "1"),
    ("mi_feature_meldungen",       sa.Boolean(), "1"),
    ("mi_feature_sektoren",        sa.Boolean(), "1"),
    ("mi_feature_karte",           sa.Boolean(), "1"),
    ("mi_feature_zeitreise",       sa.Boolean(), "1"),
    ("mi_feature_ressourcen",      sa.Boolean(), "1"),
    ("mi_feature_uebergreifend",   sa.Boolean(), "1"),
    ("mi_feature_geraeteverleih",  sa.Boolean(), "1"),
    # Geräteverleih-Konfiguration
    ("gsl_verleih_erinnerung_stunden",  sa.Integer(), None),
    ("gsl_verleih_sms_ausleih_text",    sa.Text(), None),
    ("gsl_verleih_sms_erinnerung_text", sa.Text(), None),
]


def upgrade() -> None:
    bind = op.get_bind()
    existing = {c["name"] for c in sa_inspect(bind).get_columns("org_settings")}

    for col_name, col_type, default in _NEW_COLUMNS:
        if col_name in existing:
            continue
        if default is not None:
            op.add_column(
                "org_settings",
                sa.Column(col_name, col_type, nullable=False, server_default=default),
            )
        else:
            op.add_column(
                "org_settings",
                sa.Column(col_name, col_type, nullable=True),
            )


def downgrade() -> None:
    bind = op.get_bind()
    existing = {c["name"] for c in sa_inspect(bind).get_columns("org_settings")}
    for col_name, _, _ in reversed(_NEW_COLUMNS):
        if col_name in existing:
            op.drop_column("org_settings", col_name)
