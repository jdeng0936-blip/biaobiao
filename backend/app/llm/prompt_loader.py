"""
Prompt 加载器 — 从 prompts_registry.yaml 读取模板并支持变量插值

用法:
    from app.llm.prompt_loader import get_prompt

    # 获取模板并插入变量
    system = get_prompt("bid_generate_system", industry_section="...")
    user = get_prompt("bid_generate_user", section_title="3.4 质量保证措施", ...)
"""
import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger("llm.prompt_loader")

_REGISTRY_PATH = Path(__file__).parent / "prompts_registry.yaml"
_cache: dict[str, dict] | None = None


def _load_registry() -> dict[str, dict]:
    """加载 Prompt 注册表（带缓存）"""
    global _cache
    if _cache is None:
        with open(_REGISTRY_PATH, "r", encoding="utf-8") as f:
            _cache = yaml.safe_load(f) or {}
        logger.info(f"✅ Prompt 注册表已加载: {len(_cache)} 个模板")
    return _cache


def reload_registry() -> None:
    """强制重新加载注册表（热更新场景）"""
    global _cache
    _cache = None
    _load_registry()


def get_prompt(name: str, **kwargs: Any) -> str:
    """
    获取指定名称的 Prompt 模板并执行变量插值。

    参数:
        name: Prompt 模板名称（对应 prompts_registry.yaml 中的顶级 key）
        **kwargs: 要插值的变量，对应模板中 {variable_name} 占位符。
                  未提供的变量会被替换为空字符串。

    返回:
        插值后的 Prompt 字符串

    示例:
        get_prompt("planner_user",
                   section_title="3.4 质量保证措施",
                   project_context="市政道路工程",
                   user_requirements="重点关注裂缝防治")
    """
    registry = _load_registry()
    entry = registry.get(name)
    if entry is None:
        raise ValueError(
            f"未知的 Prompt 模板: '{name}'，"
            f"请在 prompts_registry.yaml 中注册。"
            f"可用模板: {list(registry.keys())}"
        )

    template = entry.get("template", "")

    # 安全插值：未提供的变量替换为空字符串，避免 KeyError
    class SafeDict(dict):
        def __missing__(self, key):
            logger.debug(f"Prompt '{name}' 中的变量 '{key}' 未提供，使用空字符串")
            return ""

    try:
        return template.format_map(SafeDict(**kwargs))
    except Exception as e:
        logger.error(f"Prompt '{name}' 插值失败: {e}")
        return template


def list_prompts() -> list[dict[str, str]]:
    """列出所有已注册的 Prompt 模板（名称 + 描述）"""
    registry = _load_registry()
    return [
        {"name": name, "description": entry.get("description", "")}
        for name, entry in registry.items()
    ]
