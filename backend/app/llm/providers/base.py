"""
LLM Provider 抽象基类
所有 Provider（Gemini/OpenAI/Ollama）必须实现此接口
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncGenerator, Optional


@dataclass
class ModelConfig:
    """模型配置（从 llm_registry.yaml 解析）"""
    provider: str           # gemini / openai / ollama
    model_name: str         # 具体模型名
    temperature: float = 0.3
    max_output_tokens: int = 4096
    timeout_seconds: int = 60
    task_type: str = ""     # 业务场景标识


@dataclass
class LLMResponse:
    """LLM 统一响应"""
    text: str
    model: str              # 实际使用的模型名
    usage: dict = None      # token 用量（如有）


class BaseLLMProvider(ABC):
    """LLM Provider 抽象接口"""

    @abstractmethod
    def is_ready(self) -> bool:
        """检查 Provider 是否就绪"""
        ...

    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        config: ModelConfig,
    ) -> LLMResponse:
        """非流式生成"""
        ...

    @abstractmethod
    async def generate_stream(
        self,
        system_prompt: str,
        user_prompt: str,
        config: ModelConfig,
    ) -> AsyncGenerator[str, None]:
        """流式生成 — yield 纯文本片段"""
        ...

    async def embed(
        self,
        texts: list[str],
        model_name: str,
    ) -> list[list[float]]:
        """向量化（部分 Provider 支持）"""
        raise NotImplementedError(f"{self.__class__.__name__} 不支持 embedding")
