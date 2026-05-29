"""Deduplizierung: task_suggestion, message_suggestion, default_message nach Text

Revision ID: 0025
Revises: 0024
Create Date: 2026-05-29
"""
from alembic import op
from sqlalchemy import text

revision = "0025"
down_revision = "0024"
branch_labels = None
depends_on = None


def _deduplicate(conn, table, junction_table, fk_col):
    dupes = conn.execute(text(
        f"SELECT MIN(id) AS keep_id, `text` FROM `{table}`"
        f" GROUP BY `text` HAVING COUNT(*) > 1"
    )).fetchall()
    for keep_id, text_val in dupes:
        dupe_ids = [
            r[0] for r in conn.execute(text(
                f"SELECT id FROM `{table}` WHERE `text` = :t AND id != :k ORDER BY id"
            ), {"t": text_val, "k": keep_id}).fetchall()
        ]
        for dupe_id in dupe_ids:
            kept_codes = {
                r[0] for r in conn.execute(text(
                    f"SELECT alarm_type_code FROM `{junction_table}` WHERE `{fk_col}` = :k"
                ), {"k": keep_id}).fetchall()
            }
            for code, order in conn.execute(text(
                f"SELECT alarm_type_code, display_order FROM `{junction_table}` WHERE `{fk_col}` = :d"
            ), {"d": dupe_id}).fetchall():
                if code not in kept_codes:
                    conn.execute(text(
                        f"UPDATE `{junction_table}` SET `{fk_col}` = :k"
                        f" WHERE `{fk_col}` = :d AND alarm_type_code = :c"
                    ), {"k": keep_id, "d": dupe_id, "c": code})
                    kept_codes.add(code)
            conn.execute(text(
                f"DELETE FROM `{junction_table}` WHERE `{fk_col}` = :d"
            ), {"d": dupe_id})
            conn.execute(text(f"DELETE FROM `{table}` WHERE id = :d"), {"d": dupe_id})


def upgrade():
    conn = op.get_bind()
    _deduplicate(conn, "task_suggestion", "task_suggestion_alarm", "task_suggestion_id")
    _deduplicate(conn, "message_suggestion", "message_suggestion_alarm", "message_suggestion_id")
    _deduplicate(conn, "default_message", "default_message_alarm", "default_message_id")


def downgrade():
    raise NotImplementedError("downgrade not supported for migration 0025")
