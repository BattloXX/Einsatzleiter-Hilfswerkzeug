"""VehiclePosition: Composite-Index fuer letzte-Position-Query + Retention-Spalte

Revision ID: 0109
Revises: 0108
Create Date: 2026-06-27
"""
from alembic import op
from sqlalchemy import text

revision = "0109"
down_revision = "0108"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Composite-Index fuer: SELECT MAX(received_at) ... WHERE incident_id=X GROUP BY vehicle_id
    op.execute(text("""
        CREATE INDEX IF NOT EXISTS ix_vehpos_incident_vehicle_received
        ON vehicle_position (incident_id, vehicle_id, received_at)
    """))


def downgrade() -> None:
    op.execute(text("DROP INDEX IF EXISTS ix_vehpos_incident_vehicle_received ON vehicle_position"))
