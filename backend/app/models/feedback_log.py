"""
ORM Model — FeedbackLog 数据飞轮反馈记录表

记录用户对 AI 生成内容的采纳/修改/拒绝反馈，
驱动 SFT/RLHF 数据积累和知识库自我进化。
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Text, Float, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class FeedbackLog(Base):
    """数据飞轮反馈记录表"""
    __tablename__ = "feedback_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # 章节标识
    section_id: Mapped[str] = mapped_column(String(100), index=True)
    section_title: Mapped[str] = mapped_column(String(500))

    # 反馈动作：accept / edit / reject
    action: Mapped[str] = mapped_column(String(20), index=True)

    # AI 原文 & 用户修订文本
    original_text: Mapped[str] = mapped_column(Text)
    revised_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # diff 差异比率（仅 action=edit 时有值）
    diff_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)

    # 是否触发了飞轮下沉
    flywheel_triggered: Mapped[bool] = mapped_column(default=False)

    # LangFuse 链路跟踪 ID
    trace_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # === 通用审计字段（全局铁律） ===
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

    # 复合索引：租户 + 动作维度快速统计
    __table_args__ = (
        Index("ix_feedback_tenant_action", "tenant_id", "action"),
    )
