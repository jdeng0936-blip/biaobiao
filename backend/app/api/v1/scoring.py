"""
评分点提取与目录生成 API 路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from dataclasses import asdict

from app.services.scoring_extractor import ScoringExtractor

router = APIRouter(prefix="/api/v1/scoring", tags=["评分点"])

# 服务单例
_extractor: ScoringExtractor | None = None


def get_extractor() -> ScoringExtractor:
    global _extractor
    if _extractor is None:
        _extractor = ScoringExtractor()
    return _extractor


# ============================================================
# 请求/响应模型
# ============================================================
class ExtractRequest(BaseModel):
    """评分点提取请求"""
    bid_document_text: str = Field(
        ..., min_length=100, max_length=50000,
        description="招标文件文本（评分标准部分或全文）"
    )


class OutlineRequest(BaseModel):
    """目录大纲生成请求"""
    bid_document_text: str = Field(
        ..., min_length=100, max_length=50000,
        description="招标文件文本"
    )
    project_context: str = Field(default="", max_length=2000)
    bid_type: str = Field(default="service", description="标书类型")


# ============================================================
# API 端点
# ============================================================
@router.post("/extract")
async def extract_scoring_points(req: ExtractRequest):
    """
    📊 评分点提取

    从招标文件中提取所有评分标准和评分细则，
    输出结构化的评分点 JSON，包含分类、分值、评分要求。
    """
    extractor = get_extractor()
    try:
        result = await extractor.extract_scoring_points(req.bid_document_text)
        return {
            "total_score": result.total_score,
            "categories": result.categories,
            "points": [asdict(p) for p in result.points],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"评分点提取失败: {str(e)}")


@router.post("/outline")
async def generate_outline(req: OutlineRequest):
    """
    📝 评分点驱动目录生成

    先提取评分点，再根据评分点智能生成投标文件目录大纲，
    确保每个评分点都有对应章节覆盖。
    """
    extractor = get_extractor()
    try:
        # Step 1: 提取评分点
        scoring = await extractor.extract_scoring_points(req.bid_document_text)

        # Step 2: 生成目录
        outline = await extractor.generate_outline(
            scoring, req.project_context, req.bid_type
        )

        return {
            "scoring": {
                "total_score": scoring.total_score,
                "categories": scoring.categories,
                "points_count": len(scoring.points),
                "points": [asdict(p) for p in scoring.points],
            },
            "outline": outline,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"目录生成失败: {str(e)}")
