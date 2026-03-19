"""
LLM 动态路由选择器
根据 llm_registry.yaml 配置，按 task_type 分发请求到对应 Provider
"""
import logging
from pathlib import Path
from typing import AsyncGenerator, Optional

import yaml

from app.llm.providers.base import BaseLLMProvider, ModelConfig, LLMResponse
from app.llm.providers.gemini_provider import GeminiProvider
from app.llm.providers.openai_provider import OpenAIProvider

logger = logging.getLogger("llm.selector")

# Provider 名称 → 模型名前缀映射
_MODEL_PROVIDER_MAP = {
    "gemini": ["gemini-"],
    "openai": ["gpt-", "text-embedding-"],
    # 后期扩展:
    # "ollama": ["qwen", "glm", "llama"],
}

# 终极降级静态模板（当所有 LLM 均不可用时返回）
_STATIC_FALLBACK = (
    "【系统提示】AI 生成服务暂时不可用，请稍后重试。\n\n"
    "您可以先手动编写此章节内容，系统恢复后可重新使用 AI 生成功能。\n\n"
    "建议包含：施工方案概述、工序安排、质量保证措施、安全文明施工要求。"
)


class LLMSelector:
    """
    LLM 动态路由选择器

    用法:
        selector = LLMSelector()
        # 流式生成
        async for text in selector.stream("bid_generate", system_prompt, user_prompt):
            print(text)
        # 非流式生成
        response = await selector.generate("bid_chat", system_prompt, user_prompt)
    """

    def __init__(self):
        # 加载配置
        config_path = Path(__file__).parent / "llm_registry.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            self._config = yaml.safe_load(f)

        self._defaults = self._config.get("defaults", {})
        self._tasks = self._config.get("tasks", {})

        # 初始化 Provider 实例（懒加载单例）
        self._providers: dict[str, BaseLLMProvider] = {}
        self._init_providers()

        logger.info(
            f"✅ LLMSelector 就绪 — "
            f"{len(self._tasks)} 个任务场景, "
            f"{len([p for p in self._providers.values() if p.is_ready()])} 个 Provider 可用"
        )

    def _init_providers(self):
        """初始化所有配置的 Provider"""
        provider_configs = self._config.get("providers", {})

        if "gemini" in provider_configs:
            self._providers["gemini"] = GeminiProvider()

        if "openai" in provider_configs:
            openai_conf = provider_configs["openai"]
            self._providers["openai"] = OpenAIProvider(
                base_url=openai_conf.get("base_url")
            )

        # 后期扩展:
        # if "ollama" in provider_configs:
        #     from app.llm.providers.ollama_provider import OllamaProvider
        #     self._providers["ollama"] = OllamaProvider(...)

    def _resolve_provider(self, model_name: str) -> Optional[str]:
        """根据模型名推断 Provider"""
        for provider, prefixes in _MODEL_PROVIDER_MAP.items():
            for prefix in prefixes:
                if model_name.startswith(prefix):
                    return provider
        return None

    def _get_model_config(self, task_type: str) -> ModelConfig:
        """获取任务对应的模型配置"""
        task_conf = self._tasks.get(task_type)
        if not task_conf:
            raise ValueError(f"未知的任务类型: {task_type}，请在 llm_registry.yaml 中注册")

        model_name = task_conf["primary"]
        provider_name = self._resolve_provider(model_name)

        if not provider_name:
            raise ValueError(f"无法推断模型 {model_name} 的 Provider")

        return ModelConfig(
            provider=provider_name,
            model_name=model_name,
            temperature=task_conf.get("temperature", self._defaults.get("temperature", 0.3)),
            max_output_tokens=task_conf.get("max_output_tokens", self._defaults.get("max_output_tokens", 4096)),
            timeout_seconds=self._defaults.get("timeout_seconds", 60),
            task_type=task_type,
        )

    def _get_fallback_config(self, task_type: str) -> Optional[ModelConfig]:
        """获取降级模型配置"""
        task_conf = self._tasks.get(task_type, {})
        fallback = task_conf.get("fallback")
        if not fallback:
            return None

        provider_name = self._resolve_provider(fallback)
        if not provider_name:
            return None

        return ModelConfig(
            provider=provider_name,
            model_name=fallback,
            temperature=task_conf.get("temperature", self._defaults.get("temperature", 0.3)),
            max_output_tokens=task_conf.get("max_output_tokens", self._defaults.get("max_output_tokens", 4096)),
            timeout_seconds=self._defaults.get("timeout_seconds", 60),
            task_type=task_type,
        )

    def _get_provider(self, config: ModelConfig) -> BaseLLMProvider:
        """获取 Provider 实例"""
        provider = self._providers.get(config.provider)
        if not provider or not provider.is_ready():
            raise RuntimeError(f"Provider {config.provider} 不可用")
        return provider

    async def generate(
        self,
        task_type: str,
        system_prompt: str,
        user_prompt: str,
    ) -> LLMResponse:
        """非流式生成 — 自动路由 + 降级"""
        config = self._get_model_config(task_type)

        # 尝试主模型
        try:
            provider = self._get_provider(config)
            logger.info(f"📤 [{task_type}] → {config.provider}/{config.model_name}")
            return await provider.generate(system_prompt, user_prompt, config)
        except Exception as e:
            logger.warning(f"⚠️ [{task_type}] 主模型失败: {e}")

        # 降级到 fallback
        fallback_config = self._get_fallback_config(task_type)
        if fallback_config:
            try:
                provider = self._get_provider(fallback_config)
                logger.info(f"🔄 [{task_type}] fallback → {fallback_config.provider}/{fallback_config.model_name}")
                return await provider.generate(system_prompt, user_prompt, fallback_config)
            except Exception as e:
                logger.error(f"❌ [{task_type}] fallback 也失败: {e}")

        # 终极降级：返回静态模板（不崩溃）
        logger.critical(f"\ud83d\udeab [{task_type}] 所有模型均不可用，返回静态模板")
        return LLMResponse(text=_STATIC_FALLBACK, model="static_fallback")

    async def stream(
        self,
        task_type: str,
        system_prompt: str,
        user_prompt: str,
    ) -> AsyncGenerator[str, None]:
        """流式生成 — 自动路由 + 降级"""
        config = self._get_model_config(task_type)

        # 尝试主模型
        try:
            provider = self._get_provider(config)
            logger.info(f"📤 [{task_type}] stream → {config.provider}/{config.model_name}")
            async for text in provider.generate_stream(system_prompt, user_prompt, config):
                yield text
            return
        except Exception as e:
            logger.warning(f"⚠️ [{task_type}] 主模型流式失败: {e}")

        # 降级到 fallback
        fallback_config = self._get_fallback_config(task_type)
        if fallback_config:
            try:
                provider = self._get_provider(fallback_config)
                logger.info(f"🔄 [{task_type}] fallback stream → {fallback_config.provider}/{fallback_config.model_name}")
                async for text in provider.generate_stream(system_prompt, user_prompt, fallback_config):
                    yield text
                return
            except Exception as e:
                logger.error(f"❌ [{task_type}] fallback stream 也失败: {e}")

        # 终极降级：逐字 yield 静态模板（前端不白屏）
        logger.critical(f"\ud83d\udeab [{task_type}] 所有模型流式均不可用，返回静态模板")
        yield _STATIC_FALLBACK

    async def embed(
        self,
        texts: list[str],
        task_type: str = "embedding",
    ) -> list[list[float]]:
        """向量化 — 自动路由"""
        config = self._get_model_config(task_type)
        provider = self._get_provider(config)
        return await provider.embed(texts, config.model_name)


# 全局单例
_selector: LLMSelector | None = None


def get_llm_selector() -> LLMSelector:
    """获取 LLMSelector 全局单例"""
    global _selector
    if _selector is None:
        _selector = LLMSelector()
    return _selector
