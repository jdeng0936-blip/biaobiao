"""
应用配置管理 — Pydantic Settings
从 .env 读取所有配置项，统一管理
"""
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """全局配置"""

    # ---- 项目基础 ----
    APP_NAME: str = "标标 AI"
    APP_VERSION: str = "0.3.0"
    DEBUG: bool = True

    # ---- 数据库 ----
    DATABASE_URL: str = "postgresql+asyncpg://mac111@localhost:5432/biaobiao"
    # 同步连接（用于 Alembic 迁移和旧代码过渡）
    DATABASE_URL_SYNC: str = "postgresql://mac111@localhost:5432/biaobiao"

    # ---- Redis ----
    REDIS_URL: str = "redis://localhost:6379/0"

    # ---- JWT ----
    JWT_SECRET_KEY: str = "biaobiao-ai-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24小时
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ---- LLM API Keys ----
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # ---- CORS ----
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001"

    # ---- LangFuse ----
    LANGFUSE_PUBLIC_KEY: Optional[str] = None
    LANGFUSE_SECRET_KEY: Optional[str] = None
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"

    model_config = {
        "env_file": str(Path(__file__).resolve().parent.parent.parent / ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


# 全局单例
_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
