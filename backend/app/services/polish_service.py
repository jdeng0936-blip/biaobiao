"""
多轮递进式润色引擎

五级润色管道：
  L1: 术语规范化 — 统一专业用词
  L2: 文风一致性 — 第三人称/陈述语气/书面化
  L3: 逻辑连贯性 — 补充过渡句/因果论述
  L4: 专业深化   — 增加数据支撑/规范引用
  L5: 亮点提炼   — 针对评分点强化创新/差异化

设计理念：每一轮专注一个维度，逐层叠加质量提升。
至少 3 轮自动迭代，每轮生成 diff 记录供追溯。
"""
import json
import logging
from dataclasses import dataclass, field
from typing import Optional

from app.llm.llm_selector import get_llm_selector
from app.llm.prompt_loader import get_prompt

logger = logging.getLogger("polish_service")


# ============================================================
# 数据模型
# ============================================================
@dataclass
class PolishChange:
    """单个修改点"""
    level: str           # 润色级别 L1~L5
    original: str        # 原文片段
    polished: str        # 润色后片段
    reason: str          # 修改原因


@dataclass
class PolishRoundResult:
    """单轮润色结果"""
    round_num: int
    level: str
    content: str                    # 润色后全文
    changes: list[PolishChange] = field(default_factory=list)
    quality_score: float = 0.0      # 本轮质量分 0-100


@dataclass
class PolishContext:
    """润色上下文"""
    project_type: str = ""
    section_title: str = ""
    section_type: str = "technical"
    scoring_points: list[str] = field(default_factory=list)
    glossary: dict[str, str] = field(default_factory=dict)  # 术语表
    style_guide: str = ""           # 文风指南


@dataclass
class PolishResult:
    """完整润色结果"""
    original_content: str
    final_content: str
    rounds: list[PolishRoundResult] = field(default_factory=list)
    total_changes: int = 0
    quality_improvement: float = 0.0  # 质量提升百分比
    summary: str = ""

    @property
    def round_count(self) -> int:
        return len(self.rounds)


# ============================================================
# 润色引擎
# ============================================================
class PolishService:
    """
    多轮递进式润色引擎

    每一轮使用专门的 Prompt 处理一个维度，
    最少执行 3 轮，可按质量分数决定是否追加。
    """

    # 润色级别定义
    LEVELS = [
        {
            "key": "terminology",
            "name": "L1 术语规范化",
            "prompt_key": "polish_terminology",
            "description": "统一专业术语用词，消除不规范表达",
        },
        {
            "key": "style",
            "name": "L2 文风一致性",
            "prompt_key": "polish_style",
            "description": "统一为第三人称、陈述语气、正式书面语",
        },
        {
            "key": "logic",
            "name": "L3 逻辑连贯性",
            "prompt_key": "polish_logic",
            "description": "补充段落过渡、因果论述、数据支撑",
        },
        {
            "key": "professional",
            "name": "L4 专业深化",
            "prompt_key": "polish_professional",
            "description": "增加规范引用、技术参数、工艺细节",
        },
        {
            "key": "highlight",
            "name": "L5 亮点提炼",
            "prompt_key": "polish_highlight",
            "description": "针对高分值评分点强化创新和差异化论述",
        },
    ]

    # 润色轮次配置（至少 3 轮，每轮执行哪些级别）
    ROUND_CONFIG = [
        ["terminology", "style"],          # Round 1: 基础规范化
        ["logic", "professional"],         # Round 2: 内容深化
        ["highlight"],                     # Round 3: 亮点提炼
    ]

    def __init__(self, tenant_id: str = "default"):
        self._tenant_id = tenant_id
        self._selector = None

    @property
    def selector(self):
        if self._selector is None:
            self._selector = get_llm_selector()
        return self._selector

    # ============================================================
    # 主入口
    # ============================================================
    async def polish_pipeline(
        self,
        content: str,
        context: PolishContext,
        min_rounds: int = 3,
        max_rounds: int = 5,
        quality_threshold: float = 90.0,
        status_callback=None,
    ) -> PolishResult:
        """
        完整润色管道 — 至少 min_rounds 轮，最多 max_rounds 轮

        参数:
            content: 待润色的文本内容
            context: 润色上下文
            min_rounds: 最少迭代轮数（默认 3）
            max_rounds: 最多迭代轮数（默认 5）
            quality_threshold: 质量达标分数（达到后可提前结束）
            status_callback: 可选的状态回调函数（用于 SSE 推送进度）

        返回:
            PolishResult: 包含所有轮次的详细结果
        """
        result = PolishResult(
            original_content=content,
            final_content=content,
        )

        current_content = content
        total_changes = 0

        for round_num in range(max_rounds):
            # 确定本轮要执行的润色级别
            if round_num < len(self.ROUND_CONFIG):
                levels_this_round = self.ROUND_CONFIG[round_num]
            else:
                # 超过预设轮次配置，全级别扫描
                levels_this_round = ["terminology", "style", "logic", "professional", "highlight"]

            for level_key in levels_this_round:
                level_config = self._get_level_config(level_key)
                if not level_config:
                    continue

                # 状态回调
                if status_callback:
                    await status_callback(
                        f"🔄 第 {round_num + 1} 轮润色 — {level_config['name']}: {level_config['description']}"
                    )

                # 执行单轮润色
                try:
                    round_result = await self._polish_round(
                        content=current_content,
                        level_config=level_config,
                        context=context,
                        round_num=round_num + 1,
                    )

                    if round_result.content and round_result.content != current_content:
                        current_content = round_result.content
                        total_changes += len(round_result.changes)
                        result.rounds.append(round_result)
                        logger.info(
                            f"Round {round_num + 1} {level_config['name']}: "
                            f"{len(round_result.changes)} 处修改, "
                            f"质量分: {round_result.quality_score}"
                        )
                    else:
                        logger.info(f"Round {round_num + 1} {level_config['name']}: 无修改")

                except Exception as e:
                    logger.warning(f"Round {round_num + 1} {level_config['name']} 异常: {e}")
                    continue

            # 最少轮次保障
            if round_num < min_rounds - 1:
                continue

            # 质量达标可以提前结束
            if result.rounds and result.rounds[-1].quality_score >= quality_threshold:
                if status_callback:
                    await status_callback(
                        f"✅ 质量分 {result.rounds[-1].quality_score:.0f} 达到阈值 {quality_threshold:.0f}，润色完成"
                    )
                break

        # 汇总结果
        result.final_content = current_content
        result.total_changes = total_changes

        # 质量提升评估
        original_len = len(content)
        final_len = len(current_content)
        result.quality_improvement = (
            ((final_len - original_len) / original_len * 100)
            if original_len > 0 else 0.0
        )

        result.summary = (
            f"共 {result.round_count} 轮迭代, "
            f"{total_changes} 处修改, "
            f"内容量变化 {result.quality_improvement:+.1f}%"
        )

        return result

    # ============================================================
    # 单轮润色
    # ============================================================
    async def _polish_round(
        self,
        content: str,
        level_config: dict,
        context: PolishContext,
        round_num: int,
    ) -> PolishRoundResult:
        """
        单轮润色 — 调用 LLM 执行特定维度的润色

        LLM 返回 JSON 格式：
        {
            "polished_content": "润色后的完整文本",
            "changes": [
                {"original": "原文", "polished": "修改后", "reason": "原因"},
                ...
            ],
            "quality_score": 85
        }
        """
        prompt_key = level_config["prompt_key"]

        # 构建评分点上下文
        scoring_text = ""
        if context.scoring_points:
            scoring_text = "\n".join(
                f"  {i}. {p}" for i, p in enumerate(context.scoring_points, 1)
            )

        # 构建术语表上下文
        glossary_text = ""
        if context.glossary:
            glossary_text = "\n".join(
                f"  ✗ {k} → ✓ {v}" for k, v in context.glossary.items()
            )

        system_prompt = get_prompt(f"{prompt_key}_system")
        user_prompt = get_prompt(
            f"{prompt_key}_user",
            content=content[:6000],  # 限制输入长度，避免超 token
            section_title=context.section_title,
            project_type=context.project_type,
            scoring_points_text=scoring_text,
            glossary_text=glossary_text,
            round_num=str(round_num),
        )

        result = await self.selector.generate(
            "polish", system_prompt, user_prompt
        )

        # 解析 LLM 返回
        parsed = self._parse_polish_response(result.text)

        polished_content = parsed.get("polished_content", content)
        raw_changes = parsed.get("changes", [])
        quality_score = float(parsed.get("quality_score", 75))

        changes = [
            PolishChange(
                level=level_config["key"],
                original=c.get("original", ""),
                polished=c.get("polished", ""),
                reason=c.get("reason", ""),
            )
            for c in raw_changes
            if isinstance(c, dict)
        ]

        return PolishRoundResult(
            round_num=round_num,
            level=level_config["key"],
            content=polished_content,
            changes=changes,
            quality_score=quality_score,
        )

    # ============================================================
    # 辅助方法
    # ============================================================
    def _get_level_config(self, level_key: str) -> Optional[dict]:
        """获取润色级别配置"""
        for level in self.LEVELS:
            if level["key"] == level_key:
                return level
        return None

    @staticmethod
    def _parse_polish_response(text: str) -> dict:
        """解析 LLM 润色响应（容错处理）"""
        try:
            cleaned = text.strip()
            # 移除 Markdown 代码块包裹
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

            import re
            match = re.search(r'\{.*\}', cleaned, re.S)
            if match:
                return json.loads(match.group())
            return json.loads(cleaned)
        except Exception as e:
            logger.warning(f"润色响应解析失败: {e}")
            # 降级：如果 LLM 直接返回润色后文本
            if len(text) > 100:
                return {
                    "polished_content": text,
                    "changes": [],
                    "quality_score": 75,
                }
            return {}
