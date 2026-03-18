"""
反 AI 阅标引擎 — 双轨自校验（共识 #3）

轨道A：自建语料基线（L1 统计特征 + L2 语义指纹）
轨道B：实测反馈驱动（L3 外部 API，后期扩展）

检测维度：
  L1 — 困惑度近似、重复率、句长方差、词汇丰富度、连接词密度
  L2 — n-gram 分布对比人工标书基线
  L3 — 外部 AI 检测 API（GPTZero 等，后期对接）
"""
import math
import re
import logging
from collections import Counter
from dataclasses import dataclass, field
from typing import Optional

import psycopg2
import psycopg2.extras
import os

logger = logging.getLogger("anti_review_service")


@dataclass
class ReviewResult:
    """单个章节的审查结果"""
    section_title: str
    risk_score: int              # AI 痕迹风险分 0-100
    risk_level: str              # low / medium / high / critical
    details: dict                # 各维度得分明细
    suggestions: list[str]       # 改写建议


@dataclass
class BaselineStats:
    """人工标书语料基线统计"""
    avg_sentence_length: float = 28.0
    sentence_length_std: float = 12.0
    avg_vocab_richness: float = 0.65
    avg_repeat_rate: float = 0.08
    avg_connector_density: float = 0.04
    bigram_freq: dict = field(default_factory=dict)


class AntiReviewService:
    """反 AI 阅标引擎"""

    def __init__(self):
        self.db_url = os.getenv(
            "DATABASE_URL",
            "postgresql://mac111@localhost:5432/biaobiao"
        )
        self._conn = None
        self._baseline: Optional[BaselineStats] = None

    @property
    def conn(self):
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(self.db_url)
        return self._conn

    # ============================================================
    # L1：统计特征检测
    # ============================================================

    def _split_sentences(self, text: str) -> list[str]:
        """中文分句"""
        sentences = re.split(r'[。！？；\n]+', text)
        return [s.strip() for s in sentences if len(s.strip()) > 2]

    def _calc_sentence_stats(self, sentences: list[str]) -> dict:
        """句长分布分析"""
        if not sentences:
            return {"avg": 0, "std": 0, "min": 0, "max": 0, "count": 0}

        lengths = [len(s) for s in sentences]
        avg = sum(lengths) / len(lengths)
        variance = sum((l - avg) ** 2 for l in lengths) / len(lengths)
        std = math.sqrt(variance) if variance > 0 else 0

        return {
            "avg": round(avg, 1),
            "std": round(std, 1),
            "min": min(lengths),
            "max": max(lengths),
            "count": len(lengths),
        }

    def _calc_vocab_richness(self, text: str) -> float:
        """词汇丰富度（TTR = 唯一字符数 / 总字符数）"""
        chars = [c for c in text if '\u4e00' <= c <= '\u9fff']
        if not chars:
            return 0.0
        return len(set(chars)) / len(chars)

    def _calc_repeat_rate(self, sentences: list[str]) -> float:
        """段落级重复率（相似句子占比）"""
        if len(sentences) < 2:
            return 0.0

        repeat_count = 0
        for i in range(len(sentences)):
            for j in range(i + 1, len(sentences)):
                # 简单的 Jaccard 相似度
                set_i = set(sentences[i])
                set_j = set(sentences[j])
                if not set_i or not set_j:
                    continue
                similarity = len(set_i & set_j) / len(set_i | set_j)
                if similarity > 0.6:
                    repeat_count += 1

        total_pairs = len(sentences) * (len(sentences) - 1) / 2
        return repeat_count / total_pairs if total_pairs > 0 else 0.0

    def _calc_connector_density(self, text: str) -> float:
        """连接词密度（AI 文本常用过多连接词）"""
        connectors = [
            "此外", "另外", "同时", "并且", "而且", "因此", "所以",
            "然而", "但是", "不过", "尽管", "虽然", "总之", "综上",
            "首先", "其次", "最后", "一方面", "另一方面",
            "不仅", "而且", "既", "又", "总而言之",
            "值得注意的是", "需要指出的是", "具体而言", "换言之",
        ]
        total_chars = len(text)
        if total_chars == 0:
            return 0.0

        connector_count = sum(text.count(c) for c in connectors)
        return connector_count / (total_chars / 100)  # 每百字连接词数

    def analyze_l1(self, text: str) -> dict:
        """
        L1 统计特征分析

        返回各维度得分和异常标记
        """
        sentences = self._split_sentences(text)
        sent_stats = self._calc_sentence_stats(sentences)
        vocab_richness = self._calc_vocab_richness(text)
        repeat_rate = self._calc_repeat_rate(sentences[:50])  # 限制前50句避免 O(n²) 爆炸
        connector_density = self._calc_connector_density(text)

        # 异常检测（与典型 AI 文本特征对比）
        anomalies = {}

        # AI 文本特征1: 句长方差极低（过于均匀）
        if sent_stats["std"] < 5.0 and sent_stats["count"] > 5:
            anomalies["sentence_uniformity"] = {
                "score": min(30, int((5.0 - sent_stats["std"]) * 10)),
                "detail": f"句长标准差仅 {sent_stats['std']}，AI 生成文本通常句长过于均匀",
            }

        # AI 文本特征2: 词汇丰富度过高（AI倾向使用多样化词汇）
        if vocab_richness > 0.78:
            anomalies["high_vocab_diversity"] = {
                "score": min(20, int((vocab_richness - 0.78) * 200)),
                "detail": f"词汇丰富度 {vocab_richness:.2f}，高于人工标书常见范围 (0.55-0.75)",
            }

        # AI 文本特征3: 连接词密度过高
        if connector_density > 2.5:
            anomalies["connector_overuse"] = {
                "score": min(25, int((connector_density - 2.5) * 15)),
                "detail": f"每百字连接词 {connector_density:.1f} 个，AI 文本常过度使用过渡词",
            }

        # AI 文本特征4: 重复率过低（AI 很少重复，人工标书常有固定用语重复）
        if repeat_rate < 0.02 and len(sentences) > 10:
            anomalies["low_repetition"] = {
                "score": 10,
                "detail": f"重复率 {repeat_rate:.3f}，低于人工标书典型值 (0.05-0.15)",
            }

        return {
            "sentence_stats": sent_stats,
            "vocab_richness": round(vocab_richness, 4),
            "repeat_rate": round(repeat_rate, 4),
            "connector_density": round(connector_density, 2),
            "anomalies": anomalies,
            "l1_score": sum(a["score"] for a in anomalies.values()),
        }

    # ============================================================
    # L2：n-gram 语料基线对比
    # ============================================================

    def _get_baseline(self) -> BaselineStats:
        """从知识库获取人工标书基线统计"""
        if self._baseline is not None:
            return self._baseline

        # 从 training_chunks 中高密度人工标书片段计算基线
        try:
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT content FROM training_chunks
                    WHERE data_density IN ('high', 'medium')
                    LIMIT 200
                """)
                rows = cur.fetchall()

            if not rows:
                logger.warning("⚠️ 知识库为空，使用默认基线")
                self._baseline = BaselineStats()
                return self._baseline

            # 计算基线统计
            all_sentences = []
            all_richness = []
            bigram_counter = Counter()

            for row in rows:
                content = row["content"]
                sents = self._split_sentences(content)
                all_sentences.extend(sents)
                all_richness.append(self._calc_vocab_richness(content))

                # bigram 频率
                chars = [c for c in content if '\u4e00' <= c <= '\u9fff']
                for i in range(len(chars) - 1):
                    bigram_counter[chars[i] + chars[i + 1]] += 1

            # 句长统计
            lengths = [len(s) for s in all_sentences]
            avg_sl = sum(lengths) / len(lengths) if lengths else 28.0
            var_sl = sum((l - avg_sl) ** 2 for l in lengths) / len(lengths) if lengths else 144.0

            # 归一化 bigram 频率（取 top 500）
            total_bigrams = sum(bigram_counter.values())
            top_bigrams = {
                k: v / total_bigrams
                for k, v in bigram_counter.most_common(500)
            }

            self._baseline = BaselineStats(
                avg_sentence_length=avg_sl,
                sentence_length_std=math.sqrt(var_sl),
                avg_vocab_richness=sum(all_richness) / len(all_richness) if all_richness else 0.65,
                bigram_freq=top_bigrams,
            )

            logger.info(f"📊 基线统计完成: {len(rows)} 片段, {len(all_sentences)} 句")

        except Exception as e:
            logger.warning(f"基线计算失败: {e}")
            self._baseline = BaselineStats()

        return self._baseline

    def analyze_l2(self, text: str) -> dict:
        """
        L2 n-gram 语料基线对比

        将待检文本的 bigram 分布与人工标书基线对比
        """
        baseline = self._get_baseline()

        # 计算待检文本的 bigram 分布
        chars = [c for c in text if '\u4e00' <= c <= '\u9fff']
        text_bigrams = Counter()
        for i in range(len(chars) - 1):
            text_bigrams[chars[i] + chars[i + 1]] += 1

        total = sum(text_bigrams.values())
        if total == 0:
            return {"l2_score": 0, "similarity": 0, "detail": "文本过短，无法分析"}

        text_freq = {k: v / total for k, v in text_bigrams.items()}

        # 计算与基线的 KL 散度（简化版：只比较共同 bigram）
        if not baseline.bigram_freq:
            return {"l2_score": 0, "similarity": 0, "detail": "基线数据不足"}

        common_keys = set(text_freq.keys()) & set(baseline.bigram_freq.keys())
        if not common_keys:
            return {"l2_score": 15, "similarity": 0, "detail": "与基线无共同 bigram，可能为异常文本"}

        # 余弦相似度
        dot_product = sum(text_freq.get(k, 0) * baseline.bigram_freq.get(k, 0) for k in common_keys)
        norm_text = math.sqrt(sum(v ** 2 for v in text_freq.values()))
        norm_base = math.sqrt(sum(v ** 2 for v in baseline.bigram_freq.values()))

        similarity = dot_product / (norm_text * norm_base) if norm_text * norm_base > 0 else 0

        # 相似度越低 → AI 风险越高
        l2_score = 0
        if similarity < 0.3:
            l2_score = 25
        elif similarity < 0.5:
            l2_score = 15
        elif similarity < 0.7:
            l2_score = 5

        return {
            "l2_score": l2_score,
            "similarity": round(similarity, 4),
            "common_bigrams": len(common_keys),
            "detail": f"与人工标书基线相似度 {similarity:.2%}",
        }

    # ============================================================
    # 综合审查
    # ============================================================

    def review(self, text: str, section_title: str = "未知章节") -> ReviewResult:
        """
        综合审查一段文本的 AI 痕迹风险

        返回:
            ReviewResult 含风险分数、等级、明细和改写建议
        """
        l1 = self.analyze_l1(text)
        l2 = self.analyze_l2(text)

        # 综合评分（L1 权重 60%，L2 权重 40%）
        total_score = min(100, int(l1["l1_score"] * 0.6 + l2["l2_score"] * 0.4 + 0.5))

        # 风险等级
        if total_score >= 60:
            risk_level = "critical"
        elif total_score >= 40:
            risk_level = "high"
        elif total_score >= 20:
            risk_level = "medium"
        else:
            risk_level = "low"

        # 生成改写建议
        suggestions = []
        anomalies = l1.get("anomalies", {})

        if "sentence_uniformity" in anomalies:
            suggestions.append("建议打散句式结构：混合使用长句（40+字）和短句（10-字），模拟人工写作的自然节奏")

        if "high_vocab_diversity" in anomalies:
            suggestions.append("建议适当重复使用领域专业术语（如「施工缝处理」「混凝土养护」），降低刻意多样化的痕迹")

        if "connector_overuse" in anomalies:
            suggestions.append("建议减少过渡词使用：用编号（1.2.3.）或分段替代「此外」「同时」「另外」等连接词")

        if "low_repetition" in anomalies:
            suggestions.append("建议在关键要求处重复引用规范编号（如 GB50300-2013），增加人工标书的典型特征")

        if l2["l2_score"] > 10:
            suggestions.append("建议注入地方住建系统惯用语和项目实测数据引用，增强文本的「人味」")

        return ReviewResult(
            section_title=section_title,
            risk_score=total_score,
            risk_level=risk_level,
            details={
                "l1_statistics": l1,
                "l2_baseline": l2,
            },
            suggestions=suggestions,
        )

    def review_sections(self, sections: dict[str, str]) -> list[ReviewResult]:
        """批量审查多个章节"""
        return [
            self.review(text, title)
            for title, text in sections.items()
        ]

    def close(self):
        if self._conn and not self._conn.closed:
            self._conn.close()
