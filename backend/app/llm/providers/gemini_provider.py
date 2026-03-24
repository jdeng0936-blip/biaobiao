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

        import asyncio

        # 合并 system + user prompt（Gemini 有专用的 system_instruction config）
        from google.genai import types
        config_obj = types.GenerateContentConfig()
        if system_prompt:
            config_obj.system_instruction = system_prompt

        def _do_gen():
            return self.client.models.generate_content(
                model=config.model_name,
                contents=user_prompt,
                config=config_obj
            )

        response = await asyncio.to_thread(_do_gen)

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

        from google.genai import types
        import asyncio

        config_obj = types.GenerateContentConfig()
        if system_prompt:
            config_obj.system_instruction = system_prompt

        def _do_stream():
            return self.client.models.generate_content_stream(
                model=config.model_name,
                contents=user_prompt,
                config=config_obj
            )

        stream_iter = await asyncio.to_thread(_do_stream)

        def get_next(i):
            try:
                return next(i)
            except StopIteration:
                return None

        while True:
            chunk = await asyncio.to_thread(get_next, stream_iter)
            if chunk is None:
                break
            if chunk.text:
                yield chunk.text

    async def embed(
        self,
        texts: list[str],
        model_name: str = "gemini-embedding-001",
    ) -> list[list[float]]:
        """Gemini Embedding 向量化（异步包装，避免阻塞事件循环）"""
        if not self.is_ready():
            raise RuntimeError("Gemini Provider 未就绪")

        import asyncio

        def _do_embed():
            return self.client.models.embed_content(
                model=model_name,
                contents=texts,
            )

        result = await asyncio.to_thread(_do_embed)
        return [emb.values for emb in result.embeddings]

