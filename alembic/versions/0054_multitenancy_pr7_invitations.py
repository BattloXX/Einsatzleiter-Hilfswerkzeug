"""Multi-tenancy PR 7: Einladungsmodell – OrgInvitation, OrgPartner,
WebSocket org-Kanäle

Revision ID: 0054
Revises: 0053
Create Date: 2026-06-11 00:00:00.000000
"""
from alembic import op
from sqlalchemy import text

revision = "0054"
down_revision = "0053"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # 1. OrgPartner: konfigurierte Nachbar-/Partner-Orgs
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS org_partner (
            org_id         INT NOT NULL,
            partner_org_id INT NOT NULL,
            notify_on_incident TINYINT(1) NOT NULL DEFAULT 1,
            PRIMARY KEY (org_id, partner_org_id),
            CONSTRAINT fk_op_org     FOREIGN KEY (org_id)         REFERENCES fire_dept(id) ON DELETE CASCADE,
            CONSTRAINT fk_op_partner FOREIGN KEY (partner_org_id) REFERENCES fire_dept(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """))

    # 2. OrgInvitation: Einladungen zu Einsätzen
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS org_invitation (
            id                  BIGINT       NOT NULL AUTO_INCREMENT,
            incident_id         BIGINT       NOT NULL,
            inviting_org_id     INT          NOT NULL,
            invited_org_id      INT          NOT NULL,
            status              VARCHAR(20)  NOT NULL DEFAULT 'pending',
            created_by_user_id  BIGINT       NULL,
            created_at          DATETIME     NOT NULL,
            updated_at          DATETIME     NOT NULL,
            PRIMARY KEY (id),
            UNIQUE KEY uq_org_invitation_incident_org (incident_id, invited_org_id),
            INDEX ix_org_invitation_invited_org (invited_org_id),
            CONSTRAINT fk_oi_incident     FOREIGN KEY (incident_id)        REFERENCES incident(id)    ON DELETE CASCADE,
            CONSTRAINT fk_oi_inviting_org FOREIGN KEY (inviting_org_id)    REFERENCES fire_dept(id)   ON DELETE CASCADE,
            CONSTRAINT fk_oi_invited_org  FOREIGN KEY (invited_org_id)     REFERENCES fire_dept(id)   ON DELETE CASCADE,
            CONSTRAINT fk_oi_created_by   FOREIGN KEY (created_by_user_id) REFERENCES user(id)        ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """))


def downgrade():
    conn = op.get_bind()
    conn.execute(text("DROP TABLE IF EXISTS org_invitation"))
    conn.execute(text("DROP TABLE IF EXISTS org_partner"))
