"""
Gemini Embedding 服务
为 API 端点提供文本向量化能力
模型名从 llm_registry.yaml 的 embedding 任务配置读取，禁止硬编码。
"""
import os
import logging
from pathlib import Path

import yaml

logger = logging.getLogger("embedding_service")

# 从 llm_registry.yaml 读取 embedding 模型名
_REGISTRY_PATH = Path(__file__).parent / ".." / "llm" / "llm_registry.yaml"
_DEFAULT_EMBEDDING_MODEL = "gemini-embedding-001"


def _load_embedding_model_name() -> str:
    """从 llm_registry.yaml 读取 embedding 任务的主模型名"""
    try:
        with open(_REGISTRY_PATH, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        return config.get("tasks", {}).get("embedding", {}).get("primary", _DEFAULT_EMBEDDING_MODEL)
    except Exception as e:
        logger.warning(f"⚠️ 无法读取 llm_registry.yaml，使用默认模型: {e}")
        return _DEFAULT_EMBEDDING_MODEL


class GeminiEmbedding:
    """Gemini Embedding API 封装"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.ready = False

        if not self.api_key:
            logger.warning("⚠️ GEMINI_API_KEY 未配置")
            return

        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
            self.model_name = _load_embedding_model_name()
            self.ready = True
            logger.info(f"✅ Gemini Embedding 服务就绪 — 模型: {self.model_name}")
        except ImportError:
            logger.error("❌ 请安装: pip install google-genai")

    def embed(self, text: str) -> list[float]:
        """将单条文本转为向量"""
        if not self.ready:
            raise RuntimeError("Gemini Embedding 服务未就绪，请检查 GEMINI_API_KEY")

        result = self.client.models.embed_content(
            model=self.model_name,
            contents=[text],
        )
        return result.embeddings[0].values

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """批量向量化"""
        if not self.ready:
            raise RuntimeError("Gemini Embedding 服务未就绪")

        result = self.client.models.embed_content(
            model=self.model_name,
            contents=texts,
        )
        return [emb.values for emb in result.embeddings]

