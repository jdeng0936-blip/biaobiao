"""
合规审查服务 — 三级检查引擎

L1 格式规范检查（纯规则引擎，不调 LLM）
L2 内容合规检查（LLM 语义审查）
L3 废标风险预警（关键项硬判断）
"""
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from app.llm.llm_selector import get_llm_selector
from app.llm.prompt_loader import get_prompt

logger = logging.getLogger("compliance_service")


# ============================================================
# 数据模型
# ============================================================
class Severity(str, Enum):
    """问题严重级别"""
    INFO = "info"          # 建议改进
    WARNING = "warning"    # 需要修改
    CRITICAL = "critical"  # 必须修复（可能导致废标）


class IssueCategory(str, Enum):
    """问题分类"""
    NUMBERING = "numbering"            # 编号连续性
    WORD_COUNT = "word_count"          # 字数不达标
    STANDARD_REF = "standard_ref"      # 规范引用格式
    COLLOQUIAL = "colloquial"          # 口语化表达
    TABLE_FORMAT = "table_format"      # 表格格式
    SCORING_COVERAGE = "scoring_coverage"  # 评分点覆盖
    KEYWORD_COVERAGE = "keyword_coverage"  # 关键词覆盖
    DATA_CONSISTENCY = "data_consistency"  # 数据一致性
    COMPANY_NAME = "company_name"      # 投标人名称一致
    PROHIBITED = "prohibited"          # 禁止条款
    TIMELINE = "timeline"              # 工期/造价超范围


@dataclass
class ComplianceIssue:
    """合规问题条目"""
    severity: Severity
    category: IssueCategory
    message: str
    location: str = ""      # 问题位置（段落/行号）
    suggestion: str = ""     # 修复建议


@dataclass
class ComplianceContext:
    """合规审查上下文"""
    project_name: str = ""
    company_name: str = ""
    project_type: str = ""
    scoring_points: list[str] = field(default_factory=list)
    requirements: list[str] = field(default_factory=list)
    min_word_count: int = 500          # 单章节最低字数
    timeline_days: Optional[int] = None  # 招标要求工期（天）
    budget_max: Optional[float] = None   # 招标最高限价


@dataclass
class ComplianceResult:
    """合规检查结果"""
    passed: bool
    issues: list[ComplianceIssue] = field(default_factory=list)
    score: float = 100.0   # 0-100 合规分数
    summary: str = ""

    @property
    def has_critical(self) -> bool:
        return any(i.severity == Severity.CRITICAL for i in self.issues)

    @property
    def critical_issues(self) -> list[ComplianceIssue]:
        return [i for i in self.issues if i.severity == Severity.CRITICAL]

    @property
    def warning_issues(self) -> list[ComplianceIssue]:
        return [i for i in self.issues if i.severity == Severity.WARNING]

    def to_feedback_list(self) -> list[str]:
        """转换为 generate_service 可用的反馈列表"""
        return [
            f"[{i.severity.value.upper()}] {i.category.value}: {i.message}"
            + (f" 建议: {i.suggestion}" if i.suggestion else "")
            for i in self.issues
            if i.severity in (Severity.CRITICAL, Severity.WARNING)
        ]


# ============================================================
# 合规审查引擎
# ============================================================
class ComplianceService:
    """
    三级合规审查引擎

    L1: 格式规范检查（纯规则，毫秒级）
    L2: 内容合规检查（LLM 语义审查，秒级）
    L3: 废标风险预警（硬规则，毫秒级）
    """

    # 常见口语化表达黑名单
    COLLOQUIAL_PATTERNS = [
        r"我们?觉得", r"大概", r"差不多", r"可能吧",
        r"比较好", r"还行", r"挺好的", r"没什么问题",
        r"OK", r"ok", r"然后呢", r"其实",
        r"说实话", r"老实说", r"搞定", r"搞好",
        r"弄一下", r"做一下", r"看看再说",
    ]

    # 中文编号层级正则
    CN_NUMBERING = {
        1: re.compile(r"^[一二三四五六七八九十]+、"),
        2: re.compile(r"^（[一二三四五六七八九十]+）"),
        3: re.compile(r"^\d+\."),
        4: re.compile(r"^（\d+）"),
        5: re.compile(r"^[①②③④⑤⑥⑦⑧⑨⑩]"),
    }

    # 规范编号格式
    STANDARD_PATTERN = re.compile(
        r"(GB/?T?\s*\d{4,5}[-—]\d{4}|"
        r"JTG\s*[A-Z]?\d{2,3}[-—]\d{4}|"
        r"JGJ\s*\d{2,3}[-—]\d{4}|"
        r"CJJ\s*\d{2,3}[-—]\d{4}|"
        r"SL\s*\d{2,3}[-—]\d{4})"
    )

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
    async def check(
        self, content: str, context: ComplianceContext
    ) -> ComplianceResult:
        """
        完整合规审查管道

        参数:
            content: 章节文本内容
            context: 合规审查上下文（项目名/公司名/评分点等）

        返回:
            ComplianceResult: 包含所有问题和总评分
        """
        all_issues: list[ComplianceIssue] = []

        # L1: 格式规范（纯规则，快速）
        l1_issues = self._check_format(content, context)
        all_issues.extend(l1_issues)
        logger.info(f"L1 格式检查完成: {len(l1_issues)} 个问题")

        # L2: 内容合规（LLM 语义审查）
        try:
            l2_issues = await self._check_content(content, context)
            all_issues.extend(l2_issues)
            logger.info(f"L2 内容检查完成: {len(l2_issues)} 个问题")
        except Exception as e:
            logger.warning(f"L2 内容合规检查异常（降级跳过）: {e}")

        # L3: 废标风险（硬规则）
        l3_issues = self._check_disqualification(content, context)
        all_issues.extend(l3_issues)
        logger.info(f"L3 废标风险检查完成: {len(l3_issues)} 个问题")

        # 计算总分
        score = self._calculate_score(all_issues)
        has_critical = any(i.severity == Severity.CRITICAL for i in all_issues)
        passed = not has_critical and score >= 70

        summary_parts = []
        if has_critical:
            summary_parts.append(f"🚨 发现 {len([i for i in all_issues if i.severity == Severity.CRITICAL])} 个致命问题")
        warnings = [i for i in all_issues if i.severity == Severity.WARNING]
        if warnings:
            summary_parts.append(f"⚠️ {len(warnings)} 个警告")
        infos = [i for i in all_issues if i.severity == Severity.INFO]
        if infos:
            summary_parts.append(f"💡 {len(infos)} 个建议")
        if not all_issues:
            summary_parts.append("✅ 全部通过")

        return ComplianceResult(
            passed=passed,
            issues=all_issues,
            score=score,
            summary=" | ".join(summary_parts),
        )

    # ============================================================
    # L1: 格式规范检查（纯规则引擎）
    # ============================================================
    def _check_format(
        self, content: str, context: ComplianceContext
    ) -> list[ComplianceIssue]:
        """L1 格式规范检查 — 纯正则/规则，不调 LLM"""
        issues: list[ComplianceIssue] = []

        # 1. 字数统计
        char_count = len(content.replace(" ", "").replace("\n", ""))
        if char_count < context.min_word_count:
            issues.append(ComplianceIssue(
                severity=Severity.WARNING,
                category=IssueCategory.WORD_COUNT,
                message=f"章节字数 {char_count} 字，低于最低要求 {context.min_word_count} 字",
                suggestion=f"建议补充至 {context.min_word_count} 字以上，增加技术细节和规范引用",
            ))

        # 2. 编号连续性检查
        self._check_numbering(content, issues)

        # 3. 规范引用格式校验
        self._check_standard_refs(content, issues)

        # 4. 口语化表达检测
        self._check_colloquial(content, issues)

        # 5. 空段落/过短段落
        self._check_paragraph_quality(content, issues)

        return issues

    def _check_numbering(self, content: str, issues: list[ComplianceIssue]):
        """检查中文编号连续性"""
        cn_nums = "一二三四五六七八九十"
        lines = content.split("\n")
        found_numbers = []

        for line_no, line in enumerate(lines, 1):
            stripped = line.strip()
            match = self.CN_NUMBERING[1].match(stripped)
            if match:
                num_char = stripped[0]
                if num_char in cn_nums:
                    found_numbers.append((line_no, cn_nums.index(num_char)))

        # 检查是否跳号
        for i in range(1, len(found_numbers)):
            prev_idx = found_numbers[i - 1][1]
            curr_idx = found_numbers[i][1]
            if curr_idx != prev_idx + 1:
                expected = cn_nums[prev_idx + 1] if prev_idx + 1 < len(cn_nums) else "?"
                issues.append(ComplianceIssue(
                    severity=Severity.WARNING,
                    category=IssueCategory.NUMBERING,
                    message=f"一级编号跳号: 第 {found_numbers[i][0]} 行「{cn_nums[curr_idx]}」前应为「{expected}」",
                    location=f"第 {found_numbers[i][0]} 行",
                    suggestion="修正编号使其连续，确保一、二、三...不跳号不重号",
                ))

    def _check_standard_refs(self, content: str, issues: list[ComplianceIssue]):
        """检查规范引用格式"""
        matches = self.STANDARD_PATTERN.findall(content)
        for ref in matches:
            # 检查年份是否合理（不应早于 1990 或晚于当年）
            year_match = re.search(r"(\d{4})$", ref)
            if year_match:
                year = int(year_match.group(1))
                if year < 1990:
                    issues.append(ComplianceIssue(
                        severity=Severity.WARNING,
                        category=IssueCategory.STANDARD_REF,
                        message=f"规范「{ref}」年份 {year} 过早，可能已作废",
                        suggestion="请查证该规范是否为现行有效版本",
                    ))
                elif year > 2026:
                    issues.append(ComplianceIssue(
                        severity=Severity.WARNING,
                        category=IssueCategory.STANDARD_REF,
                        message=f"规范「{ref}」年份 {year} 异常（超过当前年份）",
                        suggestion="请核实规范编号和年份",
                    ))

    def _check_colloquial(self, content: str, issues: list[ComplianceIssue]):
        """检测口语化表达"""
        found = []
        for pattern in self.COLLOQUIAL_PATTERNS:
            matches = re.findall(pattern, content)
            if matches:
                found.extend(matches)

        if found:
            examples = "、".join(f"「{w}」" for w in found[:5])
            issues.append(ComplianceIssue(
                severity=Severity.WARNING,
                category=IssueCategory.COLLOQUIAL,
                message=f"检测到 {len(found)} 处口语化表达: {examples}",
                suggestion="标书应使用正式书面语，避免口语化/随意用词",
            ))

    def _check_paragraph_quality(self, content: str, issues: list[ComplianceIssue]):
        """检查段落质量"""
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        short_paras = [p for p in paragraphs if 0 < len(p) < 20 and not any(
            self.CN_NUMBERING[lv].match(p) for lv in self.CN_NUMBERING
        )]
        if len(short_paras) > 3:
            issues.append(ComplianceIssue(
                severity=Severity.INFO,
                category=IssueCategory.WORD_COUNT,
                message=f"发现 {len(short_paras)} 个过短段落（少于 20 字），可能影响阅读体验",
                suggestion="合并过短段落或扩充内容",
            ))

    # ============================================================
    # L2: 内容合规检查（LLM 语义审查）
    # ============================================================
    async def _check_content(
        self, content: str, context: ComplianceContext
    ) -> list[ComplianceIssue]:
        """L2 内容合规 — LLM 语义审查"""
        issues: list[ComplianceIssue] = []

        if not context.scoring_points:
            return issues  # 没有评分点则跳过

        try:
            system_prompt = get_prompt("compliance_content_system")
            scoring_text = "\n".join(
                f"  {i}. {p}" for i, p in enumerate(context.scoring_points, 1)
            )
            user_prompt = get_prompt(
                "compliance_content_user",
                scoring_points_text=scoring_text,
                content_preview=content[:3000],
                project_type=context.project_type,
            )

            import json
            result = await self.selector.generate(
                "compliance_check", system_prompt, user_prompt
            )

            # 解析 LLM 返回的 JSON
            text = result.text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            parsed = json.loads(text)

            # 未覆盖的评分点
            uncovered = parsed.get("uncovered_points", [])
            for point in uncovered:
                issues.append(ComplianceIssue(
                    severity=Severity.CRITICAL,
                    category=IssueCategory.SCORING_COVERAGE,
                    message=f"评分点未覆盖: {point}",
                    suggestion="请在章节中增加对该评分点的响应内容",
                ))

            # 关键技术要求缺失
            missing_keywords = parsed.get("missing_keywords", [])
            for kw in missing_keywords:
                issues.append(ComplianceIssue(
                    severity=Severity.WARNING,
                    category=IssueCategory.KEYWORD_COVERAGE,
                    message=f"关键技术要求未提及: {kw}",
                    suggestion=f"建议在正文中体现「{kw}」相关内容",
                ))

            # 数据一致性问题
            data_issues = parsed.get("data_issues", [])
            for di in data_issues:
                issues.append(ComplianceIssue(
                    severity=Severity.WARNING,
                    category=IssueCategory.DATA_CONSISTENCY,
                    message=f"数据一致性: {di}",
                    suggestion="请核实并统一全文数据",
                ))

        except Exception as e:
            logger.warning(f"LLM 合规审查解析失败: {e}")

        return issues

    # ============================================================
    # L3: 废标风险预警（硬规则）
    # ============================================================
    def _check_disqualification(
        self, content: str, context: ComplianceContext
    ) -> list[ComplianceIssue]:
        """L3 废标风险 — 硬规则检查"""
        issues: list[ComplianceIssue] = []

        # 1. 投标人名称一致性
        if context.company_name:
            name = context.company_name
            # 检查是否出现其他公司名（可能是从其他标书复制粘贴）
            common_mistakes = ["XX公司", "某某公司", "投标人名称"]
            for mistake in common_mistakes:
                if mistake in content:
                    issues.append(ComplianceIssue(
                        severity=Severity.CRITICAL,
                        category=IssueCategory.COMPANY_NAME,
                        message=f"发现未替换的公司名占位符: 「{mistake}」",
                        location="全文搜索",
                        suggestion=f"请全部替换为「{name}」",
                    ))

        # 2. 禁止条款检测
        prohibited_phrases = [
            "不承担任何责任",
            "概不负责",
            "免除一切责任",
            "仅供参考",
            "以实际为准",
        ]
        for phrase in prohibited_phrases:
            if phrase in content:
                issues.append(ComplianceIssue(
                    severity=Severity.CRITICAL,
                    category=IssueCategory.PROHIBITED,
                    message=f"包含禁止条款: 「{phrase}」，可能导致废标",
                    suggestion="删除该表述，改用正面承诺语句",
                ))

        # 3. 工期/造价合理性
        if context.timeline_days:
            # 提取文中提到的工期天数
            timeline_matches = re.findall(r"(\d+)\s*(?:个日历天|天|日历天|工日)", content)
            for m in timeline_matches:
                days = int(m)
                if days > context.timeline_days * 1.2:
                    issues.append(ComplianceIssue(
                        severity=Severity.CRITICAL,
                        category=IssueCategory.TIMELINE,
                        message=f"文中工期 {days} 天超出招标要求 {context.timeline_days} 天的 120%",
                        suggestion=f"请将工期调整至 {context.timeline_days} 天以内",
                    ))

        return issues

    # ============================================================
    # 辅助方法
    # ============================================================
    @staticmethod
    def _calculate_score(issues: list[ComplianceIssue]) -> float:
        """根据问题数量和严重度计算合规分数"""
        score = 100.0
        for issue in issues:
            if issue.severity == Severity.CRITICAL:
                score -= 15
            elif issue.severity == Severity.WARNING:
                score -= 5
            elif issue.severity == Severity.INFO:
                score -= 1
        return max(0.0, score)
