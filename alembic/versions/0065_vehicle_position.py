"""GPS-Positionshistorie für Fahrzeuge + OrgSettings retention

Revision ID: 0065
Revises: 0064
Create Date: 2026-06-12
"""
from alembic import op
from sqlalchemy import text

revision = "0065"
down_revision = "0064"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute(text("""
        CREATE TABLE vehicle_position (
            id              BIGINT       NOT NULL AUTO_INCREMENT,
            incident_id     INT          NULL,
            org_id          BIGINT       NOT NULL,
            vehicle_id      BIGINT       NULL,
            resource_label  VARCHAR(120) NULL,
            lat             DOUBLE       NOT NULL,
            lon             DOUBLE       NOT NULL,
            accuracy_m      FLOAT        NULL,
            source          VARCHAR(8)   NOT NULL DEFAULT 'gps',
            recorded_at     DATETIME     NOT NULL,
            received_at     DATETIME     NOT NULL,
            reported_by     BIGINT       NULL,
            PRIMARY KEY (id),
            KEY idx_vpos_incident  (incident_id),
            KEY idx_vpos_vehicle   (vehicle_id, received_at),
            KEY idx_vpos_org       (org_id, received_at),
            CONSTRAINT fk_vpos_incident FOREIGN KEY (incident_id)
                REFERENCES major_incident(id) ON DELETE SET NULL,
            CONSTRAINT fk_vpos_vehicle  FOREIGN KEY (vehicle_id)
                REFERENCES vehicle_master(id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """))

    conn.execute(text("""
        ALTER TABLE org_settings
            ADD COLUMN position_retention_days INT NOT NULL DEFAULT 30
    """))


def downgrade():
    conn = op.get_bind()
    conn.execute(text("ALTER TABLE org_settings DROP COLUMN position_retention_days"))
    conn.execute(text("DROP TABLE IF EXISTS vehicle_position"))
