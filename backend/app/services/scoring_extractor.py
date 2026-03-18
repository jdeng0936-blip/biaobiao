"""
评分点提取器 — 从招标文件中提取评审打分依据

流水线 Prompt 策略（借鉴点 #3）：
  Step 1: 读取招标文件 → 提取所有评分点 → 输出结构化 JSON
  Step 2: 评分点 → 驱动目录大纲生成
  Step 3: 逐评分点 → 精准生成正文

支持场景：
  - 服务类采购（物业/安保/IT运维/食堂托管）
  - 轻量级工程（绿化改造/外墙翻新）
"""
import json
import logging
import re
from dataclasses import dataclass, field, asdict
from typing import Optional

from app.llm.llm_selector import get_llm_selector

logger = logging.getLogger("scoring_extractor")


@dataclass
class ScoringPoint:
    """单个评分点"""
    category: str           # 所属大类（技术方案/商务/资信/报价）
    item: str               # 评分项名称
    max_score: float        # 满分分值
    requirements: str       # 评分标准描述
    response_strategy: str = ""  # 建议的响应策略（LLM 生成）


@dataclass
class ScoringExtractResult:
    """评分点提取结果"""
    total_score: float                     # 总分
    categories: dict[str, float] = field(default_factory=dict)  # 大类 → 分值
    points: list[ScoringPoint] = field(default_factory=list)    # 所有评分点
    outline: list[dict] = field(default_factory=list)           # 建议的目录大纲


class ScoringExtractor:
    """评分点提取器 — 流水线 Prompt"""

    def __init__(self):
        self._selector = None

    @property
    def selector(self):
        if self._selector is None:
            self._selector = get_llm_selector()
        return self._selector

    async def extract_scoring_points(self, bid_document_text: str) -> ScoringExtractResult:
        """
        Step 1: 从招标文件文本中提取所有评分点

        输入: 招标文件的评分标准部分（或全文，LLM 会自动定位）
        输出: 结构化的评分点 JSON
        """
        system_prompt = """你是一位资深的招标文件分析专家。你的唯一任务是从招标文件中精确提取评分标准和评分细则。

输出规则：
1. 只输出一个 JSON 对象，不要输出其他任何文字
2. JSON 格式必须严格遵守下方 Schema
3. 如果文档中没有明确的评分标准，根据标书类型推断常见评分维度"""

        user_prompt = f"""请从以下招标文件内容中提取所有评分点。

## 招标文件内容
{bid_document_text[:8000]}

## 输出 JSON Schema
{{
  "total_score": 100,
  "categories": {{
    "技术方案": 50,
    "商务部分": 30,
    "报价部分": 20
  }},
  "points": [
    {{
      "category": "技术方案",
      "item": "施工组织方案",
      "max_score": 15,
      "requirements": "方案科学合理、措施可行，工期安排合理"
    }}
  ]
}}

请严格按上述 Schema 输出 JSON："""

        try:
            response = await self.selector.generate("bid_extract", system_prompt, user_prompt)
            raw = response.text.strip()

            # 清理可能的 markdown 代码块
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

            data = json.loads(raw)

            result = ScoringExtractResult(
                total_score=data.get("total_score", 100),
                categories=data.get("categories", {}),
            )

            for p in data.get("points", []):
                result.points.append(ScoringPoint(
                    category=p.get("category", ""),
                    item=p.get("item", ""),
                    max_score=p.get("max_score", 0),
                    requirements=p.get("requirements", ""),
                ))

            logger.info(f"✅ 提取评分点: {len(result.points)} 个, 总分 {result.total_score}")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"评分点 JSON 解析失败: {e}")
            # 返回默认结构
            return self._get_default_scoring()
        except Exception as e:
            logger.error(f"评分点提取失败: {e}")
            return self._get_default_scoring()

    async def generate_outline(
        self,
        scoring_result: ScoringExtractResult,
        project_context: str = "",
        bid_type: str = "service",
    ) -> list[dict]:
        """
        Step 2: 评分点驱动目录大纲生成

        根据提取的评分点，智能生成投标文件目录大纲，确保每个评分点都有对应章节。
        """
        # 构建评分点摘要
        points_summary = ""
        for p in scoring_result.points:
            points_summary += f"- [{p.category}] {p.item}（{p.max_score}分）: {p.requirements}\n"

        system_prompt = """你是一位资深的标书结构设计专家。你的任务是根据评分标准设计投标文件的目录大纲。

核心原则：
1. 每个评分点都必须在目录中有明确对应的章节
2. 高分值评分点要分配更多篇幅和更深层级
3. 目录层级不超过 3 级
4. 只输出 JSON 数组"""

        user_prompt = f"""## 项目背景
{project_context}

## 标书类型
{bid_type}

## 评分点清单
{points_summary}

## 输出格式
请输出 JSON 数组，每项格式如下：
[
  {{
    "id": "sec_1",
    "title": "一、项目理解与需求分析",
    "scoring_points": ["项目理解", "需求分析"],
    "suggested_words": 1500,
    "children": [
      {{
        "id": "sec_1_1",
        "title": "（一）项目背景分析",
        "scoring_points": ["项目理解"],
        "suggested_words": 800
      }}
    ]
  }}
]

请严格按格式输出 JSON 数组："""

        try:
            response = await self.selector.generate("bid_outline", system_prompt, user_prompt)
            raw = response.text.strip()

            if raw.startswith("```"):
                raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

            outline = json.loads(raw)
            scoring_result.outline = outline

            logger.info(f"✅ 生成目录大纲: {len(outline)} 个一级章节")
            return outline

        except Exception as e:
            logger.error(f"目录大纲生成失败: {e}")
            return self._get_default_outline(scoring_result)

    def _get_default_scoring(self) -> ScoringExtractResult:
        """服务类采购的默认评分结构"""
        return ScoringExtractResult(
            total_score=100,
            categories={
                "技术方案": 55,
                "商务部分": 25,
                "报价部分": 20,
            },
            points=[
                ScoringPoint("技术方案", "项目理解与需求分析", 10, "对项目背景、服务范围、工作内容的理解深度"),
                ScoringPoint("技术方案", "服务实施方案", 15, "方案完整性、可行性、创新性"),
                ScoringPoint("技术方案", "人员配置方案", 10, "人员数量、资质、排班合理性"),
                ScoringPoint("技术方案", "质量保障措施", 10, "质量标准、检查机制、考核制度"),
                ScoringPoint("技术方案", "应急预案", 10, "突发事件应急处置方案的完备性"),
                ScoringPoint("商务部分", "企业资质与业绩", 15, "企业规模、相关业绩、获奖情况"),
                ScoringPoint("商务部分", "拟投入设备与工具", 10, "设备清单、数量、技术参数"),
                ScoringPoint("报价部分", "投标报价", 20, "合理低价法或综合评分法"),
            ],
        )

    def _get_default_outline(self, scoring_result: ScoringExtractResult) -> list[dict]:
        """根据评分点生成默认目录"""
        outline = []
        # 按 category 分组
        categories: dict[str, list[ScoringPoint]] = {}
        for p in scoring_result.points:
            categories.setdefault(p.category, []).append(p)

        chapter_num = 1
        for category, points in categories.items():
            children = []
            for i, p in enumerate(points, 1):
                children.append({
                    "id": f"sec_{chapter_num}_{i}",
                    "title": f"（{self._cn_num(i)}）{p.item}",
                    "scoring_points": [p.item],
                    "suggested_words": max(500, int(p.max_score * 100)),
                })

            outline.append({
                "id": f"sec_{chapter_num}",
                "title": f"{self._cn_chapter(chapter_num)}、{category}",
                "scoring_points": [p.item for p in points],
                "suggested_words": sum(c.get("suggested_words", 500) for c in children),
                "children": children,
            })
            chapter_num += 1

        return outline

    @staticmethod
    def _cn_num(n: int) -> str:
        nums = "一二三四五六七八九十"
        return nums[n - 1] if 0 < n <= 10 else str(n)

    @staticmethod
    def _cn_chapter(n: int) -> str:
        nums = "一二三四五六七八九十"
        return nums[n - 1] if 0 < n <= 10 else str(n)
