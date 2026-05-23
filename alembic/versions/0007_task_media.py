"""task_media: Bilder/PDFs/Videos pro Auftrag

Revision ID: 0007
Revises: 0006
Create Date: 2026-05-23 19:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "task_media",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("task_id", sa.BigInteger(), nullable=False),
        sa.Column("incident_id", sa.BigInteger(), nullable=False),
        sa.Column("uploaded_by_user_id", sa.BigInteger(), nullable=True),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("storage_path", sa.String(500), nullable=False),
        sa.Column("thumb_path", sa.String(500), nullable=True),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("bytes", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("duration_s", sa.Float(), nullable=True),
        sa.Column("pages", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["task_id"], ["task.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["incident_id"], ["incident.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by_user_id"], ["user.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8mb4",
        mysql_engine="InnoDB",
    )
    op.create_index("ix_task_media_task_id", "task_media", ["task_id"])
    op.create_index("ix_task_media_incident_id", "task_media", ["incident_id"])
    op.create_index("ix_task_media_created_at", "task_media", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_task_media_created_at", table_name="task_media")
    op.drop_index("ix_task_media_incident_id", table_name="task_media")
    op.drop_index("ix_task_media_task_id", table_name="task_media")
    op.drop_table("task_media")
