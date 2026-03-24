"""
润色服务 API 路由 — 独立多轮润色接口

支持:
  - 单章节多轮润色（SSE 流式反馈进度）
  - 全文档润色
"""
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional

from app.core.deps import get_tenant_id
from app.services.polish_service import PolishService, PolishContext

router = APIRouter(prefix="/api/v1/polish", tags=["润色引擎"])


# ============================================================
# 请求/响应模型
# ============================================================
class PolishSectionRequest(BaseModel):
    """单章节润色请求"""
    content: str = Field(..., min_length=10, description="待润色的章节内容")
    section_title: str = Field(default="", description="章节标题")
    section_type: str = Field(default="technical", description="章节类型")
    project_type: str = Field(default="", description="工程类型")
    scoring_points: list[str] = Field(default=[], description="评分点列表")
    min_rounds: int = Field(default=3, ge=1, le=5, description="最少润色轮数")
    max_rounds: int = Field(default=5, ge=1, le=8, description="最多润色轮数")
    glossary: dict[str, str] = Field(default={}, description="自定义术语对照表")


class PolishChangeResponse(BaseModel):
    """单个修改点"""
    level: str
    original: str
    polished: str
    reason: str


class PolishRoundResponse(BaseModel):
    """单轮润色结果"""
    round_num: int
    level: str
    changes_count: int
    quality_score: float


class PolishResultResponse(BaseModel):
    """润色完整结果"""
    original_length: int
    final_length: int
    final_content: str
    round_count: int
    total_changes: int
    quality_improvement: float
    summary: str
    rounds: list[PolishRoundResponse]


# ============================================================
# API 端点
# ============================================================
@router.post("/section")
async def polish_section(
    req: PolishSectionRequest,
    tenant_id: str = Depends(get_tenant_id),
):
    """
    ✨ 单章节多轮润色（SSE 流式反馈进度 + 最终结果）

    五级递进润色管道：
    - Round 1: L1 术语规范化 + L2 文风一致性
    - Round 2: L3 逻辑连贯性 + L4 专业深化
    - Round 3: L5 亮点提炼
    """
    service = PolishService(tenant_id=tenant_id)
    context = PolishContext(
        project_type=req.project_type,
        section_title=req.section_title,
        section_type=req.section_type,
        scoring_points=req.scoring_points,
        glossary=req.glossary,
    )

    async def event_generator():
        status_messages = []

        async def status_callback(msg: str):
            status_messages.append(msg)
            yield_data = json.dumps(
                {"type": "status", "text": msg}, ensure_ascii=False
            )
            # 注意：闭包问题，这里只记录，流式在主循环中推送

        # 直接执行润色管道（非流式，因为每轮需要完整内容）
        try:
            yield "data: " + json.dumps(
                {"type": "status", "text": "🚀 润色管道启动..."},
                ensure_ascii=False
            ) + "\n\n"

            result = await service.polish_pipeline(
                content=req.content,
                context=context,
                min_rounds=req.min_rounds,
                max_rounds=req.max_rounds,
            )

            # 推送各轮次进度
            for r in result.rounds:
                yield "data: " + json.dumps({
                    "type": "round_complete",
                    "round_num": r.round_num,
                    "level": r.level,
                    "changes_count": len(r.changes),
                    "quality_score": r.quality_score,
                }, ensure_ascii=False) + "\n\n"

            # 推送最终结果
            yield "data: " + json.dumps({
                "type": "result",
                "final_content": result.final_content,
                "round_count": result.round_count,
                "total_changes": result.total_changes,
                "quality_improvement": result.quality_improvement,
                "summary": result.summary,
            }, ensure_ascii=False) + "\n\n"

            yield "data: " + json.dumps({"type": "done"}, ensure_ascii=False) + "\n\n"

        except Exception as e:
            yield "data: " + json.dumps({
                "type": "error",
                "message": str(e),
            }, ensure_ascii=False) + "\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/full", response_model=PolishResultResponse)
async def polish_full_document(
    req: PolishSectionRequest,
    tenant_id: str = Depends(get_tenant_id),
):
    """
    ✨ 全文档润色（同步返回完整结果）

    适用场景：单次润色全文，不需要流式进度反馈。
    """
    service = PolishService(tenant_id=tenant_id)
    context = PolishContext(
        project_type=req.project_type,
        section_title=req.section_title,
        section_type=req.section_type,
        scoring_points=req.scoring_points,
        glossary=req.glossary,
    )

    result = await service.polish_pipeline(
        content=req.content,
        context=context,
        min_rounds=req.min_rounds,
        max_rounds=req.max_rounds,
    )

    return PolishResultResponse(
        original_length=len(result.original_content),
        final_length=len(result.final_content),
        final_content=result.final_content,
        round_count=result.round_count,
        total_changes=result.total_changes,
        quality_improvement=result.quality_improvement,
        summary=result.summary,
        rounds=[
            PolishRoundResponse(
                round_num=r.round_num,
                level=r.level,
                changes_count=len(r.changes),
                quality_score=r.quality_score,
            )
            for r in result.rounds
        ],
    )
