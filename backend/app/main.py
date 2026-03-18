"""
标标 AI — 后端入口
FastAPI + Uvicorn + async/await
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 自动加载 .env 文件（包含 GEMINI_API_KEY 等）
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

# 导入 API 路由
from app.api.v1.knowledge import router as knowledge_router
from app.api.v1.generate import router as generate_router
from app.api.v1.auth import router as auth_router
from app.api.v1.anti_review import router as anti_review_router
from app.api.v1.export import router as export_router
from app.api.v1.scoring import router as scoring_router
from app.api.v1.upload import router as upload_router
from app.api.v1.project import router as project_router
from app.api.v1.craft import router as craft_router
from app.api.v1.variant import router as variant_router

app = FastAPI(
    title="标标 AI API",
    description="全程 AI 赋能的标书制作平台 API",
    version="0.3.0",
)

# CORS 配置（开发环境）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth_router)
app.include_router(knowledge_router)
app.include_router(generate_router)
app.include_router(anti_review_router)
app.include_router(export_router)
app.include_router(scoring_router)
app.include_router(upload_router)
app.include_router(project_router)
app.include_router(craft_router)
app.include_router(variant_router)


# 导入所有 ORM Model（确保 Base.metadata 包含所有表）
from app.models import Project, User, DesensitizeEntry, StructuredTable  # noqa: F401


@app.on_event("startup")
async def startup_event():
    """开发环境自动建表（正式环境应使用 Alembic 迁移）"""
    from app.core.database import get_engine, Base
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/api/health")
async def health_check():
    """健康检查端点"""
    return {"status": "ok", "service": "标标 AI API", "version": "0.3.0"}

