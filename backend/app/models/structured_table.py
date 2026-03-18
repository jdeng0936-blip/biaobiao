"""
ORM Model — 结构化表格数据（共识 #2 中 C 类表格）
工程量清单、配合比表、检验批次表 → 入关系表 → SQL 精确查询
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Text, Float, Integer, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class StructuredTable(Base):
    """结构化表格数据 — 每行一条记录"""
    __tablename__ = "structured_tables"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # 来源信息
    source_file: Mapped[str] = mapped_column(String(300))
    table_type: Mapped[str] = mapped_column(String(50), index=True)
    # 表格类型: bill_of_quantities / mix_ratio / inspection_batch / material_list / equipment_list

    # 表格元数据
    table_title: Mapped[str | None] = mapped_column(String(300), nullable=True)
    row_index: Mapped[int] = mapped_column(Integer)  # 行序号

    # 结构化数据（key-value JSON）
    # 如: {"材料": "水泥", "规格": "P.O42.5", "用量": "380kg/m³", "强度等级": "C30"}
    row_data: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # 原始文本（用于语义搜索 fallback）
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 数值字段（用于范围查询，从 row_data 中提取的关键数值）
    numeric_value_1: Mapped[float | None] = mapped_column(Float, nullable=True)  # 如用量
    numeric_label_1: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 如"水泥用量"
    numeric_value_2: Mapped[float | None] = mapped_column(Float, nullable=True)
    numeric_label_2: Mapped[str | None] = mapped_column(String(50), nullable=True)

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
        Index("idx_structured_tenant_type", "tenant_id", "table_type"),
    )
