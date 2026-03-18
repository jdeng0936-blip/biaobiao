import os
import asyncio
from typing import AsyncGenerator
import logging

# 尝试导入双轨 SDK
try:
    import openai
    from openai import AsyncOpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    from google import genai
    from google.genai import types
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

logger = logging.getLogger(__name__)

class LLMService:
    """
    大模型统一服务封装层 (兼容 OpenAI / Gemini 双轨)
    优先使用 GEMINI_API_KEY，其次使用 OPENAI_API_KEY
    """
    def __init__(self):
        self.provider = "none"
        self.gemini_client = None
        self.openai_client = None

        gemini_key = os.getenv("GEMINI_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")

        if gemini_key and HAS_GEMINI:
            self.provider = "gemini"
            # google-genai 默认会在内部读取 GEMINI_API_KEY，也可以显式传入
            self.gemini_client = genai.Client(api_key=gemini_key)
            logger.info("LLM Provider 初始化: Google Gemini V1.0 SDK 准备就绪")
        elif openai_key and HAS_OPENAI:
            self.provider = "openai"
            self.openai_client = AsyncOpenAI(api_key=openai_key)
            logger.info("LLM Provider 初始化: OpenAI 准备就绪")
        else:
            logger.warning("未检测到有效的 GEMINI_API_KEY 或 OPENAI_API_KEY 环境配置！LLM 服务降级为 Mock。")

    async def generate_text(self, prompt: str, system_instruction: str = None) -> str:
        """同步（阻塞式）文本生成，返回全量文本"""
        if self.provider == "gemini":
            # Gemini 暂不支持纯粹原生 Async 的非流式，用 asyncio.to_thread 包装
            def _gen():
                config = types.GenerateContentConfig()
                if system_instruction:
                    config.system_instruction = system_instruction
                res = self.gemini_client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                    config=config
                )
                return res.text
            return await asyncio.to_thread(_gen)

        elif self.provider == "openai":
            messages = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            messages.append({"role": "user", "content": prompt})

            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7
            )
            return response.choices[0].message.content

        else:
            # Fallback Mock
            await asyncio.sleep(1)
            return "[Mock] 真实大模型凭证缺失，这是模拟生成的专业标书内容片段..."

    async def generate_stream(self, prompt: str, system_instruction: str = None) -> AsyncGenerator[str, None]:
        """流式文本生成 (SSE)，返回 AsyncGenerator"""
        if self.provider == "gemini":
            # Gemini 使用 generate_content_stream
            def _stream_gen():
                config = types.GenerateContentConfig()
                if system_instruction:
                    config.system_instruction = system_instruction
                return self.gemini_client.models.generate_content_stream(
                    model='gemini-2.5-flash',
                    contents=prompt,
                    config=config
                )
            
            # 因为 google-genai v1.0 的流默认是同步 generator，需要包装在异步循环里
            # 为了防止阻塞主事件循环，使用 asyncio.to_thread 进行异步迭代拉取
            stream_iter = await asyncio.to_thread(_stream_gen)
            
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

        elif self.provider == "openai":
            messages = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            messages.append({"role": "user", "content": prompt})

            stream = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7,
                stream=True
            )
            async for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    yield content

        else:
            # Fallback Mock Stream
            mock_text = "[Mock模式] 系统未能识别到有效的 API KEY。标书要求极其严格，包括专业工艺说明、数据参数把控。AI 加持下，中标率有显著提升。"
            for char in mock_text:
                await asyncio.sleep(0.05)
                yield char

# 全局单例
llm_service = LLMService()
