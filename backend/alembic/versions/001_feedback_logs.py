"""create feedback_logs table

Revision ID: 001_feedback_logs
Revises:
Create Date: 2026-03-19 12:10:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "001_feedback_logs"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "feedback_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("section_id", sa.String(100), index=True, nullable=False),
        sa.Column("section_title", sa.String(500), nullable=False),
        sa.Column("action", sa.String(20), index=True, nullable=False),
        sa.Column("original_text", sa.Text, nullable=False),
        sa.Column("revised_text", sa.Text, nullable=True),
        sa.Column("diff_ratio", sa.Float, nullable=True),
        sa.Column("flywheel_triggered", sa.Boolean, default=False, nullable=False),
        sa.Column("trace_id", sa.String(100), nullable=True),
        # 四个通用审计字段
        sa.Column("tenant_id", sa.String(50), index=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("created_by", sa.String(50), nullable=True),
    )

    # 复合索引：租户 + 动作维度的快速统计
    op.create_index(
        "ix_feedback_tenant_action",
        "feedback_logs",
        ["tenant_id", "action"],
    )


def downgrade() -> None:
    op.drop_index("ix_feedback_tenant_action", table_name="feedback_logs")
    op.drop_table("feedback_logs")
