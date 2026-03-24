"""
反 AI 阅标审查 API 路由
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.core.deps import get_tenant_id
from app.services.anti_review_service import AntiReviewService

router = APIRouter(prefix="/api/v1/anti-review", tags=["反AI审查"])


# ============================================================
# 请求/响应模型
# ============================================================
class ReviewRequest(BaseModel):
    """审查请求"""
    text: str = Field(..., min_length=50, max_length=50000, description="待审查文本")
    section_title: str = Field(default="未知章节", max_length=200)


class BatchReviewRequest(BaseModel):
    """批量审查请求"""
    sections: dict[str, str] = Field(..., description="章节标题→内容映射")


class ReviewResponse(BaseModel):
    """审查结果"""
    section_title: str
    risk_score: int
    risk_level: str
    details: dict
    suggestions: list[str]


# ============================================================
# API 端点
# ============================================================
@router.post("/check", response_model=ReviewResponse)
async def check_text(
    req: ReviewRequest,
    tenant_id: str = Depends(get_tenant_id),
):
    """
    🔍 AI 痕迹检测

    对单段文本进行 L1 统计特征 + L2 语料基线双层检测，
    返回风险分数（0-100）和改写建议。
    """
    service = AntiReviewService()
    try:
        result = service.review(req.text, req.section_title)
        return ReviewResponse(
            section_title=result.section_title,
            risk_score=result.risk_score,
            risk_level=result.risk_level,
            details=result.details,
            suggestions=result.suggestions,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"审查失败: {str(e)}")


@router.post("/batch", response_model=list[ReviewResponse])
async def batch_check(
    req: BatchReviewRequest,
    tenant_id: str = Depends(get_tenant_id),
):
    """
    📋 批量 AI 痕迹检测

    对多个章节同时检测，返回每个章节的独立审查结果。
    """
    if not req.sections:
        raise HTTPException(status_code=400, detail="章节内容不能为空")

    service = AntiReviewService()
    try:
        results = service.review_sections(req.sections)
        return [
            ReviewResponse(
                section_title=r.section_title,
                risk_score=r.risk_score,
                risk_level=r.risk_level,
                details=r.details,
                suggestions=r.suggestions,
            )
            for r in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量审查失败: {str(e)}")
