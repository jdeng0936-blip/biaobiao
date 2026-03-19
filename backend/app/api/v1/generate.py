"""
标书内容生成 API 路由
RAG 检索 → Gemini 流式生成 → SSE 推送
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional

from app.services.knowledge_service import KnowledgeService
from app.services.embedding_service import GeminiEmbedding
from app.services.generate_service import BidGenerateService

router = APIRouter(prefix="/api/v1/generate", tags=["内容生成"])

# 服务单例
_generate_service: BidGenerateService | None = None
_knowledge_service: KnowledgeService | None = None
_embedding_service: GeminiEmbedding | None = None


def get_services():
    global _generate_service, _knowledge_service, _embedding_service
    if _generate_service is None:
        _generate_service = BidGenerateService()
    if _knowledge_service is None:
        _knowledge_service = KnowledgeService()
    if _embedding_service is None:
        _embedding_service = GeminiEmbedding()
    return _generate_service, _knowledge_service, _embedding_service


# ============================================================
# 请求模型
# ============================================================
class GenerateRequest(BaseModel):
    """标书内容生成请求"""
    section_title: str = Field(..., description="章节标题，如「3.4 质量保证措施」")
    section_type: str = Field(default="technical", description="章节类型: technical/quality/safety/schedule/resource")
    project_name: str = Field(default="", description="项目名称")
    project_type: str = Field(default="", description="工程类型，如「市政道路」")
    requirements: Optional[str] = Field(default=None, description="用户补充要求")
    use_rag: bool = Field(default=True, description="是否使用知识库增强")
    rag_top_k: int = Field(default=5, ge=1, le=10, description="RAG 检索条数")


# ============================================================
# API 端点
# ============================================================
@router.post("/section")
async def generate_section(req: GenerateRequest):
    """
    📝 生成标书章节内容（SSE 流式）

    流程：
    1. 用章节标题向量化 → 语义搜索知识库
    2. 将检索到的知识片段注入 Prompt
    3. Gemini 流式生成标书内容
    4. SSE 逐字推送到前端
    """
    gen_service, kb_service, emb_service = get_services()

    if not gen_service.ready:
        raise HTTPException(status_code=503, detail="Gemini 生成服务未就绪")

    # 1. RAG 检索（如果启用）
    rag_chunks = []
    if req.use_rag and emb_service.ready:
        try:
            # 用章节标题 + 工程类型作为搜索查询
            search_query = f"{req.project_type} {req.section_title}"
            query_vector = emb_service.embed(search_query)
            rag_chunks = kb_service.search(
                query_embedding=query_vector,
                top_k=req.rag_top_k,
                doc_section=req.section_type if req.section_type != "technical" else None,
            )
        except Exception as e:
            # RAG 失败不影响生成，降级为无知识库
            rag_chunks = []

    # 2. 构建项目上下文
    project_context = f"项目: {req.project_name}" if req.project_name else ""
    if req.project_type:
        project_context += f" | 类型: {req.project_type}"

    # 3. 流式生成
    async def event_generator():
        async for chunk in gen_service.generate_stream(
            section_title=req.section_title,
            section_type=req.section_type,
            project_context=project_context,
            project_type=req.project_type,
            rag_chunks=rag_chunks,
            user_requirements=req.requirements,
        ):
            yield chunk

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


class ChatRequest(BaseModel):
    """AI 对话请求 — 针对模块的精准问答"""
    module_content: str = Field(default="", description="引用的模块文本内容")
    user_question: str = Field(..., description="用户的实际问题")
    project_name: str = Field(default="", description="项目名称")
    project_type: str = Field(default="", description="工程类型")
    use_rag: bool = Field(default=True, description="是否使用知识库增强")


@router.post("/chat")
async def chat_with_ai(req: ChatRequest):
    """
    💬 AI 助手对话（SSE 流式）— 精准回答模块提问

    与标书生成完全分离的对话接口：
    - 使用专用的咨询顾问 Prompt
    - 只针对用户问题回答，不复述原文
    - 回答后附带引申提问建议
    """
    gen_service, kb_service, emb_service = get_services()

    if not gen_service.ready:
        raise HTTPException(status_code=503, detail="Gemini 服务未就绪")

    # RAG 检索（精简，最多2条）
    rag_chunks = []
    if req.use_rag and emb_service.ready and req.user_question:
        try:
            query_vector = emb_service.embed(req.user_question)
            rag_chunks = kb_service.search(
                query_embedding=query_vector,
                top_k=2,
            )
        except Exception:
            pass

    project_context = f"项目: {req.project_name}" if req.project_name else ""
    if req.project_type:
        project_context += f" | 类型: {req.project_type}"

    async def event_generator():
        async for chunk in gen_service.generate_chat_stream(
            module_content=req.module_content,
            user_question=req.user_question,
            project_context=project_context,
            rag_chunks=rag_chunks,
        ):
            yield chunk

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
