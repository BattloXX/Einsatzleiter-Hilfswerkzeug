"""template matrix: Auftragsvorlagen/Meldungsvorlagen/Default-Meldungen als n:m zu Alarmtypen

Revision ID: 0024
Revises: 0023
Create Date: 2026-05-29
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy import text

revision = "0024"
down_revision = "0023"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # ── task_suggestion_alarm ──────────────────────────────────────────────────
    op.create_table(
        "task_suggestion_alarm",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("task_suggestion_id", sa.BigInteger,
                  sa.ForeignKey("task_suggestion.id", ondelete="CASCADE"), nullable=False),
        sa.Column("alarm_type_code", sa.String(10),
                  sa.ForeignKey("alarm_type.code", ondelete="CASCADE"), nullable=False),
        sa.Column("display_order", sa.Integer, server_default="0", nullable=False),
        mysql_charset="utf8mb4",
        mysql_engine="InnoDB",
    )
    conn.execute(text("""
        INSERT INTO task_suggestion_alarm (task_suggestion_id, alarm_type_code, display_order)
        SELECT id, alarm_type_code, display_order FROM task_suggestion
    """))
    op.drop_column("task_suggestion", "alarm_type_code")
    op.drop_column("task_suggestion", "display_order")

    # ── message_suggestion_alarm ───────────────────────────────────────────────
    op.create_table(
        "message_suggestion_alarm",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("message_suggestion_id", sa.BigInteger,
                  sa.ForeignKey("message_suggestion.id", ondelete="CASCADE"), nullable=False),
        sa.Column("alarm_type_code", sa.String(10),
                  sa.ForeignKey("alarm_type.code", ondelete="CASCADE"), nullable=False),
        sa.Column("display_order", sa.Integer, server_default="0", nullable=False),
        mysql_charset="utf8mb4",
        mysql_engine="InnoDB",
    )
    conn.execute(text("""
        INSERT INTO message_suggestion_alarm (message_suggestion_id, alarm_type_code, display_order)
        SELECT id, alarm_type_code, display_order FROM message_suggestion
    """))
    op.drop_column("message_suggestion", "alarm_type_code")
    op.drop_column("message_suggestion", "display_order")

    # ── default_message_alarm ──────────────────────────────────────────────────
    op.create_table(
        "default_message_alarm",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("default_message_id", sa.Integer,
                  sa.ForeignKey("default_message.id", ondelete="CASCADE"), nullable=False),
        sa.Column("alarm_type_code", sa.String(10),
                  sa.ForeignKey("alarm_type.code", ondelete="CASCADE"), nullable=False),
        sa.Column("display_order", sa.Integer, server_default="0", nullable=False),
        sa.Column("due_after_sec", sa.Integer, server_default="300", nullable=False),
        mysql_charset="utf8mb4",
        mysql_engine="InnoDB",
    )
    conn.execute(text("""
        INSERT INTO default_message_alarm (default_message_id, alarm_type_code, display_order, due_after_sec)
        SELECT id, alarm_type_code, 0, due_after_sec FROM default_message
    """))
    op.drop_column("default_message", "alarm_type_code")
    op.drop_column("default_message", "due_after_sec")


def downgrade():
    raise NotImplementedError("downgrade not supported for migration 0024")
