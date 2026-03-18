"""
标标 AI — 后端入口
FastAPI + Uvicorn + async/await
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="标标 AI API",
    description="全程 AI 赋能的标书制作平台 API",
    version="0.1.0",
)

# CORS 配置（开发环境）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check():
    """健康检查端点"""
    return {"status": "ok", "service": "标标 AI API", "version": "0.1.0"}
