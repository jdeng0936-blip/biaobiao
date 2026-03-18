"""
ORM Model — 脱敏词典表
入库和在线共用同一套映射表（共识 #1）
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DesensitizeEntry(Base):
    """脱敏词典条目"""
    __tablename__ = "desensitize_dict"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # 原始文本（如"XX市政道路改造工程"）
    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    # 占位符（如"[PROJECT_A]"）
    placeholder: Mapped[str] = mapped_column(String(100), nullable=False)
    # 实体类型: project/person/amount/address/phone/org
    entity_type: Mapped[str] = mapped_column(String(30), nullable=False)

    # 租户隔离 + 通用字段
    tenant_id: Mapped[str] = mapped_column(String(50), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    created_by: Mapped[str | None] = mapped_column(String(50), nullable=True)

    __table_args__ = (
        Index("idx_desensitize_tenant_entity", "tenant_id", "entity_type"),
    )
