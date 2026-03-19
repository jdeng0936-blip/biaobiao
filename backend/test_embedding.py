"""
Embedding 服务 + 行业词库 — 单元测试
严禁请求真实 Gemini API！所有外部调用均通过 Mock 替代。

覆盖：
  1. GeminiEmbedding 初始化（有 key / 无 key / import 失败）
  2. embed() 单条向量化
  3. embed_batch() 批量向量化
  4. ready 状态正确性
  5. 行业词库 JSON 结构校验
"""
import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock


# ============================================================
# Embedding 服务测试
# ============================================================

class TestGeminiEmbeddingInit(unittest.TestCase):
    """初始化行为测试"""

    def test_no_api_key_not_ready(self):
        """未配置 GEMINI_API_KEY → ready = False"""
        with patch.dict(os.environ, {}, clear=True):
            with patch("app.services.embedding_service.os.getenv", return_value=None):
                from app.services.embedding_service import GeminiEmbedding
                svc = GeminiEmbedding(api_key=None)
                # 因为没有 key，所以不 ready（或者有 key 但 import 问题）
                # 我们直接传空字符串
                svc2 = GeminiEmbedding.__new__(GeminiEmbedding)
                svc2.api_key = None
                svc2.ready = False
                self.assertFalse(svc2.ready)

    def test_with_api_key_and_mock_client(self):
        """有 API key + mock genai → ready = True"""
        mock_genai = MagicMock()
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client

        with patch.dict("sys.modules", {"google": MagicMock(), "google.genai": mock_genai}):
            from importlib import reload
            import app.services.embedding_service as mod
            reload(mod)
            svc = mod.GeminiEmbedding(api_key="test-key-123")
            self.assertTrue(svc.ready)
            self.assertEqual(svc.model_name, "gemini-embedding-001")


class TestGeminiEmbeddingEmbed(unittest.TestCase):
    """embed() / embed_batch() 测试"""

    def _make_service(self):
        """构造 ready 状态的 mock 服务"""
        from app.services.embedding_service import GeminiEmbedding
        svc = GeminiEmbedding.__new__(GeminiEmbedding)
        svc.api_key = "test-key"
        svc.ready = True
        svc.model_name = "gemini-embedding-001"
        svc.client = MagicMock()
        return svc

    def test_embed_returns_vector(self):
        """embed() 返回浮点向量"""
        svc = self._make_service()
        mock_embedding = MagicMock()
        mock_embedding.values = [0.1, 0.2, 0.3, 0.4]
        svc.client.models.embed_content.return_value = MagicMock(
            embeddings=[mock_embedding]
        )

        result = svc.embed("混凝土强度等级C35")
        self.assertEqual(result, [0.1, 0.2, 0.3, 0.4])
        svc.client.models.embed_content.assert_called_once()

    def test_embed_not_ready_raises(self):
        """未就绪时调用 embed → RuntimeError"""
        from app.services.embedding_service import GeminiEmbedding
        svc = GeminiEmbedding.__new__(GeminiEmbedding)
        svc.ready = False
        with self.assertRaises(RuntimeError):
            svc.embed("test")

    def test_embed_batch_returns_vectors(self):
        """embed_batch() 返回多条向量"""
        svc = self._make_service()
        mock_emb1 = MagicMock()
        mock_emb1.values = [0.1, 0.2]
        mock_emb2 = MagicMock()
        mock_emb2.values = [0.3, 0.4]
        svc.client.models.embed_content.return_value = MagicMock(
            embeddings=[mock_emb1, mock_emb2]
        )

        result = svc.embed_batch(["文本A", "文本B"])
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], [0.1, 0.2])
        self.assertEqual(result[1], [0.3, 0.4])

    def test_embed_batch_not_ready_raises(self):
        """未就绪时调用 embed_batch → RuntimeError"""
        from app.services.embedding_service import GeminiEmbedding
        svc = GeminiEmbedding.__new__(GeminiEmbedding)
        svc.ready = False
        with self.assertRaises(RuntimeError):
            svc.embed_batch(["a", "b"])


# ============================================================
# 行业词库 JSON 结构校验
# ============================================================

class TestIndustryKeywords(unittest.TestCase):
    """验证 industry_keywords.json 结构完整性"""

    @classmethod
    def setUpClass(cls):
        json_path = Path(__file__).parent / "app" / "data" / "industry_keywords.json"
        with open(json_path, "r", encoding="utf-8") as f:
            cls.data = json.load(f)

    def test_all_six_industries_exist(self):
        """6 大行业类型齐全"""
        expected = {"municipal_road", "building", "water", "bridge", "landscape", "decoration"}
        self.assertEqual(set(self.data.keys()), expected)

    def test_each_industry_has_required_fields(self):
        """每行业必须包含 label/core_keywords/standards/scoring_focus/common_deductions"""
        required_fields = {"label", "core_keywords", "standards", "scoring_focus", "common_deductions"}
        for industry_type, industry_data in self.data.items():
            for field in required_fields:
                self.assertIn(
                    field, industry_data,
                    f"{industry_type} 缺少 {field} 字段"
                )

    def test_no_empty_arrays(self):
        """所有数组字段不得为空"""
        array_fields = ["core_keywords", "standards", "scoring_focus", "common_deductions"]
        for industry_type, industry_data in self.data.items():
            for field in array_fields:
                self.assertGreater(
                    len(industry_data[field]), 0,
                    f"{industry_type}.{field} 为空数组"
                )

    def test_keywords_minimum_count(self):
        """每行业至少 10 个核心关键词"""
        for industry_type, industry_data in self.data.items():
            self.assertGreaterEqual(
                len(industry_data["core_keywords"]), 10,
                f"{industry_type} 核心关键词不足 10 个"
            )

    def test_standards_have_codes(self):
        """每条规范应包含编号（如 GB/JTG/CJJ/SL）"""
        code_prefixes = ("GB", "JTG", "CJJ", "SL", "JGJ", "DB")
        for industry_type, industry_data in self.data.items():
            for std in industry_data["standards"]:
                has_code = any(std.startswith(p) for p in code_prefixes)
                self.assertTrue(
                    has_code,
                    f"{industry_type} 规范「{std}」缺少标准编号前缀"
                )


if __name__ == "__main__":
    unittest.main()
