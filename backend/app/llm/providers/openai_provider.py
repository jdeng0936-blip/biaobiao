"""
OpenAI Provider — OpenAI / GPT API 适配器
兼容 OpenAI 官方 API 及代理（base_url 可配置）
"""
import os
import logging
from typing import AsyncGenerator, Optional

from app.llm.providers.base import BaseLLMProvider, ModelConfig, LLMResponse

logger = logging.getLogger("llm.openai")


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API Provider"""

    def __init__(self, base_url: Optional[str] = None):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = base_url
        self.client = None
        self.async_client = None

        if not self.api_key:
            logger.warning("⚠️ OPENAI_API_KEY 未配置")
            return

        try:
            from openai import OpenAI, AsyncOpenAI

            client_kwargs = {"api_key": self.api_key}
            if self.base_url:
                client_kwargs["base_url"] = self.base_url

            self.client = OpenAI(**client_kwargs)
            self.async_client = AsyncOpenAI(**client_kwargs)
            logger.info("✅ OpenAI Provider 就绪")
        except ImportError:
            logger.error("❌ 请安装: pip install openai")

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
            raise RuntimeError("OpenAI Provider 未就绪")

        response = await self.async_client.chat.completions.create(
            model=config.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=config.temperature,
            max_tokens=config.max_output_tokens,
        )

        text = response.choices[0].message.content or ""
        usage = None
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        return LLMResponse(text=text, model=config.model_name, usage=usage)

    async def generate_stream(
        self,
        system_prompt: str,
        user_prompt: str,
        config: ModelConfig,
    ) -> AsyncGenerator[str, None]:
        """流式生成 — yield 纯文本片段"""
        if not self.is_ready():
            raise RuntimeError("OpenAI Provider 未就绪")

        stream = await self.async_client.chat.completions.create(
            model=config.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=config.temperature,
            max_tokens=config.max_output_tokens,
            stream=True,
        )

        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield delta.content

    async def embed(
        self,
        texts: list[str],
        model_name: str = "text-embedding-3-small",
    ) -> list[list[float]]:
        """OpenAI Embedding 向量化"""
        if not self.is_ready():
            raise RuntimeError("OpenAI Provider 未就绪")

        response = await self.async_client.embeddings.create(
            model=model_name,
            input=texts,
        )
        return [item.embedding for item in response.data]
