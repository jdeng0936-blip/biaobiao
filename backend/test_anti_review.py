"""
反 AI 阅标引擎 — 单元测试
严禁连接真实数据库！所有外部 I/O 均通过 Mock 替代。

覆盖：
  1. L1 统计特征（分句、句长、词汇丰富度、重复率、连接词密度）
  2. L1 异常检测（均匀句长、高丰富度、连接词过多、低重复率）
  3. L2 n-gram 基线对比（Mock 知识库返回）
  4. 综合 review() 评分和风险等级
"""
import unittest
from unittest.mock import patch, MagicMock


class TestL1Analysis(unittest.TestCase):
    """L1 统计特征检测"""

    def _make_service(self):
        """构造不连接数据库的 AntiReviewService"""
        with patch("app.services.anti_review_service.psycopg2"):
            from app.services.anti_review_service import AntiReviewService
            svc = AntiReviewService()
            svc._conn = MagicMock()
            return svc

    def test_split_sentences_basic(self):
        """中文分句：以句号/叹号/问号/分号分割"""
        svc = self._make_service()
        text = "施工方案应科学合理。安全措施必须到位！质量第一。"
        sentences = svc._split_sentences(text)
        self.assertEqual(len(sentences), 3)

    def test_split_sentences_newline(self):
        """换行符也触发分句"""
        svc = self._make_service()
        text = "第一段内容\n第二段内容\n第三段内容"
        sentences = svc._split_sentences(text)
        self.assertEqual(len(sentences), 3)

    def test_sentence_stats(self):
        """句长统计计算"""
        svc = self._make_service()
        sentences = ["短句子", "这是一个稍微长一些的句子", "中等长度的句子"]
        stats = svc._calc_sentence_stats(sentences)
        self.assertIn("avg", stats)
        self.assertIn("std", stats)
        self.assertEqual(stats["count"], 3)
        self.assertGreater(stats["avg"], 0)

    def test_sentence_stats_empty(self):
        """空输入返回全零"""
        svc = self._make_service()
        stats = svc._calc_sentence_stats([])
        self.assertEqual(stats["avg"], 0)
        self.assertEqual(stats["count"], 0)

    def test_vocab_richness_chinese(self):
        """中文词汇丰富度：唯一字 / 总字数"""
        svc = self._make_service()
        # 全部不同
        richness_high = svc._calc_vocab_richness("天地人和通达安顺")
        self.assertGreater(richness_high, 0.8)

        # 大量重复
        richness_low = svc._calc_vocab_richness("的的的的的的的的的的")
        self.assertAlmostEqual(richness_low, 0.1, places=1)

    def test_vocab_richness_no_chinese(self):
        """纯英文/数字 → 丰富度 = 0"""
        svc = self._make_service()
        richness = svc._calc_vocab_richness("Hello World 12345")
        self.assertEqual(richness, 0.0)

    def test_repeat_rate_identical_sentences(self):
        """完全重复的句子 → 重复率高"""
        svc = self._make_service()
        sentences = ["本工程采用混凝土结构"] * 5
        rate = svc._calc_repeat_rate(sentences)
        self.assertGreater(rate, 0.5)

    def test_repeat_rate_unique_sentences(self):
        """完全不同的句子 → 重复率低"""
        svc = self._make_service()
        sentences = [
            "采用预应力混凝土技术",
            "钢筋焊接需符合规范要求",
            "防水卷材厚度不低于四毫米",
            "基坑围护采用钻孔灌注桩",
        ]
        rate = svc._calc_repeat_rate(sentences)
        self.assertLess(rate, 0.3)

    def test_connector_density_high(self):
        """高连接词密度"""
        svc = self._make_service()
        text = "此外，同时还需要注意。因此，所以要做好准备。另外，综上所述，总之需要强调。"
        density = svc._calc_connector_density(text)
        self.assertGreater(density, 2.0)

    def test_connector_density_low(self):
        """无连接词 → 密度趋零"""
        svc = self._make_service()
        text = "混凝土强度等级采用C35。路面宽度12米。设计速度60公里每小时。"
        density = svc._calc_connector_density(text)
        self.assertLess(density, 1.0)

    def test_analyze_l1_returns_score(self):
        """L1 分析返回完整结构"""
        svc = self._make_service()
        text = "本工程位于合肥市蜀山区。总长度约为3.2公里。采用沥青混凝土路面。设计速度60公里每小时。" * 3
        result = svc.analyze_l1(text)
        self.assertIn("sentence_stats", result)
        self.assertIn("vocab_richness", result)
        self.assertIn("repeat_rate", result)
        self.assertIn("connector_density", result)
        self.assertIn("l1_score", result)
        self.assertIsInstance(result["l1_score"], int)


class TestL1Anomalies(unittest.TestCase):
    """L1 异常检测"""

    def _make_service(self):
        with patch("app.services.anti_review_service.psycopg2"):
            from app.services.anti_review_service import AntiReviewService
            svc = AntiReviewService()
            svc._conn = MagicMock()
            return svc

    def test_uniform_sentence_length_detected(self):
        """句长过于均匀 → 触发 sentence_uniformity 异常"""
        svc = self._make_service()
        # 构造句长极其均匀的文本（AI 典型特征）
        uniform_text = "。".join(["本工程采用先进的施工工艺和技术方案"] * 15) + "。"
        result = svc.analyze_l1(uniform_text)
        # 句长标准差应很低
        self.assertLess(result["sentence_stats"]["std"], 5.0)

    def test_high_connector_density_detected(self):
        """连接词过多 → 触发 connector_overuse 异常"""
        svc = self._make_service()
        text = (
            "首先需要做好准备工作。其次要编制施工方案。此外还需要考虑安全因素。"
            "同时要注意环保要求。并且要控制施工进度。因此必须加强管理。"
            "另外需要做好质量控制。总之要确保工程顺利。综上所述需要尽快落实。"
            "不仅要注重质量而且要注重安全。换言之需要全面把控。值得注意的是细节问题。"
        ) * 2
        result = svc.analyze_l1(text)
        self.assertGreater(result["connector_density"], 2.0)


class TestL2Analysis(unittest.TestCase):
    """L2 n-gram 基线对比"""

    def _make_service_with_baseline(self):
        with patch("app.services.anti_review_service.psycopg2") as mock_pg:
            from app.services.anti_review_service import AntiReviewService, BaselineStats
            svc = AntiReviewService()
            svc._conn = MagicMock()
            # 预设基线（跳过 DB 查询）
            svc._baseline = BaselineStats(
                avg_sentence_length=28.0,
                sentence_length_std=12.0,
                avg_vocab_richness=0.65,
                bigram_freq={"施工": 0.05, "工程": 0.04, "混凝": 0.03, "凝土": 0.03, "方案": 0.02},
            )
            return svc

    def test_l2_similar_to_baseline(self):
        """与基线相似的文本 → L2 分低"""
        svc = self._make_service_with_baseline()
        text = "施工工程混凝土方案" * 10
        result = svc.analyze_l2(text)
        self.assertIn("l2_score", result)
        self.assertIn("similarity", result)

    def test_l2_empty_text(self):
        """空文本 → 无法分析"""
        svc = self._make_service_with_baseline()
        result = svc.analyze_l2("Hello 123")
        self.assertEqual(result["l2_score"], 0)

    def test_l2_no_common_bigrams(self):
        """与基线无共同 bigram → 异常"""
        svc = self._make_service_with_baseline()
        # 使用完全不同的字符
        text = "蝴蝶翅膀彩虹星辰" * 5
        result = svc.analyze_l2(text)
        self.assertGreater(result["l2_score"], 0)


class TestReviewIntegration(unittest.TestCase):
    """综合审查 review()"""

    def _make_service(self):
        with patch("app.services.anti_review_service.psycopg2"):
            from app.services.anti_review_service import AntiReviewService, BaselineStats
            svc = AntiReviewService()
            svc._conn = MagicMock()
            svc._baseline = BaselineStats(
                bigram_freq={"施工": 0.05, "工程": 0.04, "方案": 0.02},
            )
            return svc

    def test_review_returns_result(self):
        """review() 返回完整 ReviewResult 对象"""
        svc = self._make_service()
        text = "本工程位于合肥市蜀山区，总长度约为3.2公里。" * 5
        result = svc.review(text, section_title="3.1 工程概况")
        self.assertEqual(result.section_title, "3.1 工程概况")
        self.assertIsInstance(result.risk_score, int)
        self.assertIn(result.risk_level, ["low", "medium", "high", "critical"])
        self.assertIsInstance(result.suggestions, list)
        self.assertIn("l1_statistics", result.details)
        self.assertIn("l2_baseline", result.details)

    def test_review_risk_levels(self):
        """不同分数对应不同风险等级"""
        svc = self._make_service()
        # 低风险文本（自然混合句式）
        natural_text = (
            "路基施工采用分层填筑碾压法。每层虚铺厚度不超过30厘米。"
            "压实度检测采用灌砂法，合格率应达到95%以上。"
            "沥青面层铺设前应进行基层验收确认！"
            "混凝土养护期不少于14天...具体视气温情况调整。"
        ) * 2
        result = svc.review(natural_text)
        self.assertIn(result.risk_level, ["low", "medium"])


if __name__ == "__main__":
    unittest.main()
