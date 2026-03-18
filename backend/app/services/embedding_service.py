"""
Gemini Embedding 服务
为 API 端点提供文本向量化能力
"""
import os
import logging

logger = logging.getLogger("embedding_service")


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
            self.model_name = "gemini-embedding-001"
            self.ready = True
            logger.info("✅ Gemini Embedding 服务就绪")
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
