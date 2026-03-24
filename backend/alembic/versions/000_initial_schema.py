"""initial schema — users, projects, desensitize_dict, structured_tables

Revision ID: 000_initial_schema
Revises:
Create Date: 2026-03-19 10:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "000_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── users ──
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("username", sa.String(50), unique=True, index=True, nullable=False),
        sa.Column("email", sa.String(255), unique=True, index=True, nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(100), nullable=True),
        sa.Column("company", sa.String(200), nullable=True),
        sa.Column("role", sa.String(20), server_default="user", nullable=False),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true"), nullable=False),
        sa.Column("tenant_id", sa.String(50), index=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.String(50), nullable=True),
    )

    # ── projects ──
    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(300), index=True, nullable=False),
        sa.Column("project_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), server_default="draft", nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("bid_deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("generated_sections", postgresql.JSONB, nullable=True),
        sa.Column("progress", sa.Integer, server_default="0", nullable=False),
        sa.Column("tenant_id", sa.String(50), index=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.String(50), nullable=True),
    )

    # ── desensitize_dict ──
    op.create_table(
        "desensitize_dict",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("original_text", sa.Text, nullable=False),
        sa.Column("placeholder", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(30), nullable=False),
        sa.Column("tenant_id", sa.String(50), index=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.String(50), nullable=True),
    )
    op.create_index("idx_desensitize_tenant_entity", "desensitize_dict", ["tenant_id", "entity_type"])

    # ── structured_tables ──
    op.create_table(
        "structured_tables",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_file", sa.String(300), nullable=False),
        sa.Column("table_type", sa.String(50), index=True, nullable=False),
        sa.Column("table_title", sa.String(300), nullable=True),
        sa.Column("row_index", sa.Integer, nullable=False),
        sa.Column("row_data", postgresql.JSONB, nullable=False),
        sa.Column("raw_text", sa.Text, nullable=True),
        sa.Column("numeric_value_1", sa.Float, nullable=True),
        sa.Column("numeric_label_1", sa.String(50), nullable=True),
        sa.Column("numeric_value_2", sa.Float, nullable=True),
        sa.Column("numeric_label_2", sa.String(50), nullable=True),
        sa.Column("tenant_id", sa.String(50), index=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.String(50), nullable=True),
    )
    op.create_index("idx_structured_tenant_type", "structured_tables", ["tenant_id", "table_type"])


def downgrade() -> None:
    op.drop_index("idx_structured_tenant_type", table_name="structured_tables")
    op.drop_table("structured_tables")
    op.drop_index("idx_desensitize_tenant_entity", table_name="desensitize_dict")
    op.drop_table("desensitize_dict")
    op.drop_table("projects")
    op.drop_table("users")
