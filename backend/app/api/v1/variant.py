"""
API 路由 — 变体生成引擎
提供变体配置、批量生成、相似度矩阵查询。
"""
import uuid
import random
from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/variants", tags=["变体生成引擎"])


# ──────────────────────────── 数据模型 ────────────────────────────

class VariantConfig(BaseModel):
    """变体生成配置"""
    dimensions: dict[str, list[str]]  # { "craft": ["明挖法","顶管法"], "style": [...] }
    target_count: int = 10
    source_text: Optional[str] = None  # 原始标书文本


class VariantItem(BaseModel):
    """变体条目"""
    id: str
    name: str
    style: str
    similarity: float
    score: Optional[float] = None
    status: str  # done/generating/pending


# ──────────────────────────── 内存存储 ────────────────────────────

_variants_store: list[dict] = []


# ──────────────────────────── 接口实现 ────────────────────────────

@router.get("/dimensions")
async def get_dimensions():
    """获取变体维度配置项"""
    return {
        "dimensions": [
            {"id": "craft", "label": "施工方案路线", "desc": "3-5 种等效可行施工工法",
             "options": ["明挖法", "顶管法", "盾构法", "沉管法"]},
            {"id": "style", "label": "语言风格", "desc": "不同的叙事口吻和行文风格",
             "options": ["技术严谨型", "实战经验型", "学术引用型", "简洁务实型", "官方公文型"]},
            {"id": "layout", "label": "排版结构", "desc": "章节顺序/分节粒度/图表位置",
             "options": ["工序先行型", "质量优先型", "安全突出型", "标准规范型"]},
            {"id": "params", "label": "工期/参数浮动", "desc": "合理区间内浮动设备参数和工期节点",
             "options": ["±3%", "±5%", "±8%", "±10%"]},
            {"id": "cases", "label": "引用案例轮换", "desc": "从企业业绩库中轮换不同历史项目",
             "options": ["2023年市政道路A项目", "2024年排水管网B项目", "2022年桥梁C项目", "2024年房建D项目"]},
            {"id": "format", "label": "排版样式", "desc": "6+ 种文档视觉样式模板",
             "options": ["传统稳重", "现代简约", "图文丰富", "数据驱动", "极简留白", "工程蓝图"]},
        ]
    }


@router.post("/generate")
async def generate_variants(config: VariantConfig):
    """根据配置生成变体列表（模拟生成）"""
    global _variants_store
    _variants_store = []

    styles = config.dimensions.get("style", ["技术严谨型"])
    crafts = config.dimensions.get("craft", ["明挖法"])
    formats = config.dimensions.get("format", ["传统稳重"])

    for i in range(min(config.target_count, 20)):
        style_pick = styles[i % len(styles)]
        craft_pick = crafts[i % len(crafts)]
        format_pick = formats[i % len(formats)]

        variant = {
            "id": str(uuid.uuid4())[:8],
            "name": f"变体 {chr(65 + i // 3)}-{(i % 3) + 1:02d}",
            "style": f"{style_pick}+{craft_pick}+{format_pick}",
            "similarity": round(random.uniform(4, 18), 1),
            "score": round(random.uniform(85, 95), 1) if i < config.target_count - 2 else None,
            "status": "done" if i < config.target_count - 2 else ("generating" if i == config.target_count - 2 else "pending"),
        }
        _variants_store.append(variant)

    return {
        "variants": _variants_store,
        "stats": {
            "done": sum(1 for v in _variants_store if v["status"] == "done"),
            "generating": sum(1 for v in _variants_store if v["status"] == "generating"),
            "pending": sum(1 for v in _variants_store if v["status"] == "pending"),
            "avg_score": round(
                sum(v["score"] for v in _variants_store if v["score"]) /
                max(1, sum(1 for v in _variants_store if v["score"])), 1
            ),
        },
    }


@router.get("/list")
async def list_variants():
    """获取已生成的变体列表"""
    return {"variants": _variants_store}


@router.get("/similarity-matrix")
async def similarity_matrix():
    """获取变体间相似度矩阵"""
    done_variants = [v for v in _variants_store if v["status"] == "done"][:6]
    labels = [v["name"] for v in done_variants]
    n = len(labels)

    # 生成对称矩阵
    matrix = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            val = round(random.uniform(5, 20), 1)
            matrix[i][j] = val
            matrix[j][i] = val

    return {"labels": labels, "matrix": matrix}
