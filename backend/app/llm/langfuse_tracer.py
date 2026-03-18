"""
LangFuse 观测埋点
统一记录 LLM 调用的输入输出、模型、耗时、质量标签
"""
import logging
import time
from typing import Optional

logger = logging.getLogger("llm.langfuse")

# LangFuse 客户端（可选依赖）
_langfuse = None


def _get_langfuse():
    """懒加载 LangFuse 客户端"""
    global _langfuse
    if _langfuse is not None:
        return _langfuse

    try:
        from langfuse import Langfuse
        _langfuse = Langfuse()
        logger.info("✅ LangFuse 埋点就绪")
    except Exception as e:
        logger.warning(f"⚠️ LangFuse 未配置（不影响核心功能）: {e}")
        _langfuse = False  # 标记为不可用，避免重复尝试

    return _langfuse


def trace_llm_call(
    task_type: str,
    model_name: str,
    system_prompt: str,
    user_prompt: str,
    output: str,
    duration_ms: float,
    quality: Optional[str] = None,
    metadata: Optional[dict] = None,
):
    """
    记录一次 LLM 调用

    参数:
        task_type: 业务场景（bid_generate / bid_chat / ...）
        model_name: 实际使用的模型名
        system_prompt: 系统提示词
        user_prompt: 用户提示词
        output: LLM 输出文本
        duration_ms: 耗时（毫秒）
        quality: 质量标签（high/medium/low），用于数据飞轮
        metadata: 额外元数据
    """
    lf = _get_langfuse()
    if not lf or lf is False:
        return

    try:
        trace = lf.trace(
            name=task_type,
            metadata={
                "model": model_name,
                "duration_ms": duration_ms,
                **(metadata or {}),
            },
        )

        trace.generation(
            name=f"{task_type}_generation",
            model=model_name,
            input={"system": system_prompt, "user": user_prompt},
            output=output,
            metadata={"quality": quality} if quality else None,
        )

        # 数据飞轮：高质量输出打标签（为后续微调积累语料）
        if quality == "high":
            trace.score(name="quality", value=1.0, comment="用户采纳的高质量输出")

    except Exception as e:
        logger.warning(f"LangFuse 记录失败（不影响核心功能）: {e}")
