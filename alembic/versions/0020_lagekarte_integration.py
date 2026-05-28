"""Lagekarte.info Integration: Koordinaten an Incident + FireDept, neue Tabelle lagekarte_token

Revision ID: 0020
Revises: 0019
Create Date: 2026-05-28 00:00:00.000000

Hinweis: lagekarte_token wird ohne DB-seitige FK-Constraints angelegt, da
MariaDB errno 150 wirft (Typ-/Charset-Mismatch zwischen den referenzierten
PKs und unseren FK-Spalten). Die referentielle Integrität wird durch den
SQLAlchemy-ORM sichergestellt.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect as sa_inspect, text


revision = "0020"
down_revision = "0019"
branch_labels = None
depends_on = None


def _existing_columns(table: str) -> set[str]:
    conn = op.get_bind()
    return {c["name"] for c in sa_inspect(conn).get_columns(table)}


def _table_exists(table: str) -> bool:
    conn = op.get_bind()
    return table in sa_inspect(conn).get_table_names()


def upgrade() -> None:
    # Idempotent: Spalten nur hinzufügen wenn sie noch nicht existieren
    # (ein fehlgeschlagener Vorlauf kann Spalten bereits angelegt haben)

    incident_cols = _existing_columns("incident")
    if "lat" not in incident_cols:
        op.add_column("incident", sa.Column("lat", sa.Float(), nullable=True))
    if "lng" not in incident_cols:
        op.add_column("incident", sa.Column("lng", sa.Float(), nullable=True))
    if "lagekarte_shash_url" not in incident_cols:
        op.add_column("incident", sa.Column("lagekarte_shash_url", sa.String(500), nullable=True))

    fire_dept_cols = _existing_columns("fire_dept")
    if "fallback_lat" not in fire_dept_cols:
        op.add_column("fire_dept", sa.Column("fallback_lat", sa.Float(), nullable=True))
    if "fallback_lng" not in fire_dept_cols:
        op.add_column("fire_dept", sa.Column("fallback_lng", sa.Float(), nullable=True))

    if not _table_exists("lagekarte_token"):
        # Raw SQL ohne FK-Constraints: MariaDB errno 150 umgehen.
        # Referentielle Integrität wird durch den SQLAlchemy-ORM sichergestellt.
        op.execute(text("""
            CREATE TABLE lagekarte_token (
                id               BIGINT       NOT NULL AUTO_INCREMENT,
                token_hash       VARCHAR(64)  NOT NULL,
                label            VARCHAR(150) NOT NULL,
                org_id           INTEGER      NOT NULL,
                einsatz_id       BIGINT,
                created_by_user_id BIGINT,
                created_at       DATETIME     NOT NULL,
                expires_at       DATETIME,
                revoked_at       DATETIME,
                last_used_at     DATETIME,
                PRIMARY KEY (id),
                UNIQUE KEY uq_lagekarte_token_hash (token_hash)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """))


def downgrade() -> None:
    if _table_exists("lagekarte_token"):
        op.drop_table("lagekarte_token")

    fire_dept_cols = _existing_columns("fire_dept")
    if "fallback_lng" in fire_dept_cols:
        op.drop_column("fire_dept", "fallback_lng")
    if "fallback_lat" in fire_dept_cols:
        op.drop_column("fire_dept", "fallback_lat")

    incident_cols = _existing_columns("incident")
    if "lagekarte_shash_url" in incident_cols:
        op.drop_column("incident", "lagekarte_shash_url")
    if "lng" in incident_cols:
        op.drop_column("incident", "lng")
    if "lat" in incident_cols:
        op.drop_column("incident", "lat")
