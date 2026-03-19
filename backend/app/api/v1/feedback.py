"""
用户反馈 API — 数据飞轮入口
接收前端的 采纳 / 编辑 / 拒绝 反馈，驱动 SFT 数据积累
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.feedback_service import FeedbackFlywheelService

router = APIRouter(prefix="/api/v1/feedback", tags=["反馈飞轮"])


class FeedbackRequest(BaseModel):
    """反馈请求体 — Pydantic V2 强校验"""
    section_id: str = Field(..., min_length=1, description="章节 ID")
    action: Literal["accept", "edit", "reject"] = Field(..., description="反馈动作")
    original_text: str = Field(..., min_length=1, description="AI 原始生成内容")
    revised_text: Optional[str] = Field(None, description="用户修改后的内容（仅 action=edit 时必填）")
    section_title: Optional[str] = Field(None, description="章节标题")
    trace_id: Optional[str] = Field(None, description="LangFuse 跟踪 ID")
    tenant_id: str = Field(default="default", description="租户 ID")


class FeedbackResponse(BaseModel):
    success: bool
    message: str
    flywheel_triggered: bool = Field(False, description="是否触发了飞轮数据下沉")


class FeedbackStatsResponse(BaseModel):
    total: int
    accept_count: int
    edit_count: int
    reject_count: int
    accept_rate: float
    edit_rate: float
    reject_rate: float
    flywheel_sunk: int


@router.post("", response_model=FeedbackResponse)
async def submit_feedback(
    req: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    接收用户对 AI 生成内容的反馈

    - accept: 用户采纳 AI 原文，记录正向反馈
    - edit: 用户修改了 AI 原文，触发飞轮数据下沉
    - reject: 用户拒绝 AI 原文，记录负向反馈
    """
    if req.action == "edit" and not req.revised_text:
        raise HTTPException(
            status_code=422,
            detail="action=edit 时必须提供 revised_text（修改后文本）"
        )

    try:
        service = FeedbackFlywheelService(tenant_id=req.tenant_id)
        flywheel_triggered = await service.ingest_feedback(
            db=db,
            target_section=req.section_title or req.section_id,
            section_id=req.section_id,
            original_ai_text=req.original_text,
            user_revised_text=req.revised_text or req.original_text,
            action=req.action,
            trace_id=req.trace_id,
        )

        action_labels = {
            "accept": "✅ 正向反馈已记录",
            "edit": "✏️ 修改反馈已记录，飞轮运转中",
            "reject": "❌ 负向反馈已记录",
        }

        return FeedbackResponse(
            success=True,
            message=action_labels.get(req.action, "反馈已记录"),
            flywheel_triggered=flywheel_triggered,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"反馈处理失败: {str(e)}")


@router.get("/stats", response_model=FeedbackStatsResponse)
async def get_feedback_stats(
    tenant_id: str = "default",
    db: AsyncSession = Depends(get_db),
):
    """
    获取反馈统计数据 — Dashboard 数据飞轮面板

    返回各类反馈的数量、占比和飞轮下沉总量。
    """
    try:
        stats = await FeedbackFlywheelService.get_stats(
            db=db,
            tenant_id=tenant_id,
        )
        return FeedbackStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"统计查询失败: {str(e)}")
