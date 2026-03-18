"""
ORM Model — Project 项目表
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Project(Base):
    """标书项目表"""
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(300), index=True)
    project_type: Mapped[str] = mapped_column(String(50))  # 市政道路/房建/...
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft/in_progress/completed
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    bid_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # 标书生成的章节内容（JSON 存储已生成内容）
    generated_sections: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # 项目进度
    progress: Mapped[int] = mapped_column(Integer, default=0)  # 0-100

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
