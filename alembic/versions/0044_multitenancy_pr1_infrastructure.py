"""Multi-tenancy PR 1: AuditLog org_id, org_admin role

Revision ID: 0044
Revises: 0043
Create Date: 2026-06-11 00:00:00.000000

BIGINT-Hinweis: fire_dept.id ist BIGINT (seit Migration 0001). Alle FK-Spalten,
die auf fire_dept.id zeigen, müssen ebenfalls BIGINT sein — sonst erzeugt
MariaDB errno 150 "Foreign key constraint is incorrectly formed".
"""
from alembic import op
from sqlalchemy import text

revision = "0044"
down_revision = "0043"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # 1a. org_id auf audit_log – BIGINT (passt zu fire_dept.id BIGINT)
    #     Idempotent: falls ein früherer fehlgeschlagener Lauf die Spalte bereits
    #     als INT angelegt hat, wird der Typ auf BIGINT korrigiert.
    r = conn.execute(text(
        "SELECT COLUMN_TYPE FROM INFORMATION_SCHEMA.COLUMNS"
        " WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'audit_log'"
        " AND COLUMN_NAME = 'org_id'"
    ))
    row = r.fetchone()
    if row is None:
        conn.execute(text(
            "ALTER TABLE `audit_log`"
            "  ADD COLUMN `org_id` BIGINT NULL DEFAULT NULL,"
            "  ADD INDEX `ix_audit_log_org_id` (`org_id`)"
        ))
    else:
        # Spalte existiert bereits (partieller Lauf) — sicherstellen, dass Typ BIGINT ist
        conn.execute(text(
            "ALTER TABLE `audit_log` MODIFY COLUMN `org_id` BIGINT NULL DEFAULT NULL"
        ))

    # 1b. FK-Constraint (nur anlegen wenn noch nicht vorhanden)
    r = conn.execute(text(
        "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS"
        " WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'audit_log'"
        " AND CONSTRAINT_NAME = 'fk_audit_log_org_id'"
    ))
    if r.scalar() == 0:
        conn.execute(text(
            "ALTER TABLE `audit_log`"
            "  ADD CONSTRAINT `fk_audit_log_org_id`"
            "  FOREIGN KEY (`org_id`) REFERENCES `fire_dept` (`id`) ON DELETE SET NULL"
        ))

    # 2. org_admin-Rolle einfügen (falls noch nicht vorhanden)
    conn.execute(text(
        "INSERT IGNORE INTO `role` (`code`, `label`)"
        " VALUES ('org_admin', 'Organisations-Administrator')"
    ))

    # 3. Alle Nutzer mit 'admin'-Rolle erhalten zusätzlich 'org_admin'
    conn.execute(text("""
        INSERT IGNORE INTO `user_role` (`user_id`, `role_id`)
        SELECT ur.user_id, (SELECT id FROM `role` WHERE code = 'org_admin')
        FROM `user_role` ur
        JOIN `role` r ON r.id = ur.role_id AND r.code = 'admin'
        WHERE (SELECT id FROM `role` WHERE code = 'org_admin') IS NOT NULL
    """))


def downgrade():
    conn = op.get_bind()
    conn.execute(text(
        "ALTER TABLE `audit_log`"
        "  DROP FOREIGN KEY `fk_audit_log_org_id`,"
        "  DROP INDEX `ix_audit_log_org_id`,"
        "  DROP COLUMN `org_id`"
    ))
