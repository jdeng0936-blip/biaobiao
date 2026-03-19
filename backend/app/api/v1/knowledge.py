"""
知识库检索 API 路由
提供语义搜索、知识库统计、文件列表等端点
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional

from app.services.knowledge_service import KnowledgeService
from app.services.embedding_service import GeminiEmbedding

router = APIRouter(prefix="/api/v1/knowledge", tags=["知识库"])

# 临时 tenant_id（正式环境从 JWT 中提取）
DEMO_TENANT = "demo_tenant"

# 服务单例（FastAPI 生命周期内复用）
_knowledge_service: KnowledgeService | None = None
_embedding_service: GeminiEmbedding | None = None


def get_knowledge_service() -> KnowledgeService:
    global _knowledge_service
    if _knowledge_service is None:
        _knowledge_service = KnowledgeService(tenant_id=DEMO_TENANT)
    return _knowledge_service


def get_embedding_service() -> GeminiEmbedding:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = GeminiEmbedding()
    return _embedding_service


# ============================================================
# 请求/响应模型
# ============================================================
class SearchRequest(BaseModel):
    """语义搜索请求"""
    query: str = Field(..., min_length=2, max_length=500, description="搜索关键词或自然语言描述")
    top_k: int = Field(default=10, ge=1, le=50, description="返回结果数量")
    project_type: Optional[str] = Field(default=None, description="过滤工程类型，如 '市政-道路'")
    doc_section: Optional[str] = Field(default=None, description="过滤文档类型: technical/quality/safety/schedule/resource")
    min_density: Optional[str] = Field(default=None, description="最低数据密度: high/medium/low")


class ChunkResult(BaseModel):
    """单条搜索结果"""
    id: str
    content: str
    source_file: str
    chapter: str | None
    section: str | None
    project_type: list[str]
    doc_section: str | None
    craft_tags: list[str]
    char_count: int
    has_params: bool
    data_density: str
    similarity: float


class SearchResponse(BaseModel):
    """搜索响应"""
    query: str
    total: int
    results: list[ChunkResult]


# ============================================================
# API 端点
# ============================================================
@router.post("/search", response_model=SearchResponse)
async def search_knowledge(req: SearchRequest):
    """
    🔍 语义搜索知识片段

    根据自然语言描述，在知识库中检索最相关的标书片段。
    支持按工程类型、文档类型、数据密度过滤。

    示例:
    - "混凝土裂缝防治措施"
    - "市政道路排水管网施工方案"
    - "质量保证体系组织架构"
    """
    # 1. 将查询文本向量化
    emb_service = get_embedding_service()
    if not emb_service.ready:
        raise HTTPException(
            status_code=503,
            detail="Embedding 服务未就绪，请检查 GEMINI_API_KEY 配置"
        )

    try:
        query_vector = emb_service.embed(req.query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"向量化失败: {str(e)}")

    # 2. 语义搜索
    kb_service = get_knowledge_service()
    try:
        results = kb_service.search(
            query_embedding=query_vector,
            top_k=req.top_k,
            project_type=req.project_type,
            doc_section=req.doc_section,
            min_density=req.min_density,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检索失败: {str(e)}")

    return SearchResponse(
        query=req.query,
        total=len(results),
        results=results,
    )


@router.get("/stats")
async def get_knowledge_stats():
    """
    📊 知识库统计信息

    返回总片段数、文件数、数据密度分布等
    """
    kb_service = get_knowledge_service()
    try:
        stats = kb_service.get_stats()
        return {"status": "ok", "data": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/files")
async def list_knowledge_files():
    """
    📂 知识库文件列表

    返回所有已入库的文件及其统计信息
    """
    kb_service = get_knowledge_service()
    try:
        files = kb_service.get_files()
        # 时间序列化处理
        for f in files:
            if f.get("first_added"):
                f["first_added"] = str(f["first_added"])
        return {"status": "ok", "total": len(files), "files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")
