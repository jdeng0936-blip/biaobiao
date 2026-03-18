"""
Gemini Provider — Google Gemini API 适配器
"""
import os
import logging
from typing import AsyncGenerator

from app.llm.providers.base import BaseLLMProvider, ModelConfig, LLMResponse

logger = logging.getLogger("llm.gemini")


class GeminiProvider(BaseLLMProvider):
    """Google Gemini API Provider"""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.client = None

        if not self.api_key:
            logger.warning("⚠️ GEMINI_API_KEY 未配置")
            return

        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
            logger.info("✅ Gemini Provider 就绪")
        except ImportError:
            logger.error("❌ 请安装: pip install google-genai")

    def is_ready(self) -> bool:
        return self.client is not None

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        config: ModelConfig,
    ) -> LLMResponse:
        """非流式生成"""
        if not self.is_ready():
            raise RuntimeError("Gemini Provider 未就绪")

        # 合并 system + user prompt（Gemini 不原生支持 system role）
        combined = system_prompt + "\n\n" + user_prompt

        response = self.client.models.generate_content(
            model=config.model_name,
            contents=[{"role": "user", "parts": [{"text": combined}]}],
        )

        return LLMResponse(
            text=response.text or "",
            model=config.model_name,
        )

    async def generate_stream(
        self,
        system_prompt: str,
        user_prompt: str,
        config: ModelConfig,
    ) -> AsyncGenerator[str, None]:
        """流式生成 — yield 纯文本片段"""
        if not self.is_ready():
            raise RuntimeError("Gemini Provider 未就绪")

        combined = system_prompt + "\n\n" + user_prompt

        response = self.client.models.generate_content_stream(
            model=config.model_name,
            contents=[{"role": "user", "parts": [{"text": combined}]}],
        )

        for chunk in response:
            if chunk.text:
                yield chunk.text

    async def embed(
        self,
        texts: list[str],
        model_name: str = "gemini-embedding-001",
    ) -> list[list[float]]:
        """Gemini Embedding 向量化"""
        if not self.is_ready():
            raise RuntimeError("Gemini Provider 未就绪")

        result = self.client.models.embed_content(
            model=model_name,
            contents=texts,
        )
        return [emb.values for emb in result.embeddings]
