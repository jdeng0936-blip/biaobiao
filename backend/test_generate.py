"""
生成服务 & 知识库 API 模型 — 单元测试
覆盖：
  1. GenerateRequest / ChatRequest Pydantic 模型校验
  2. BidGenerateService Prompt 构建 + RAG 注入 + 行业词库
  3. 知识库 SearchRequest 模型校验
严禁调用真实 Gemini API。
"""
import unittest
from unittest.mock import MagicMock, patch
from pydantic import ValidationError


# ============================================================
# GenerateRequest 模型测试
# ============================================================
class TestGenerateRequestModel(unittest.TestCase):
    """GenerateRequest Pydantic 模型"""

    def test_minimal_valid(self):
        from app.api.v1.generate import GenerateRequest
        req = GenerateRequest(section_title="3.4 质量保证措施")
        self.assertEqual(req.section_title, "3.4 质量保证措施")
        self.assertEqual(req.section_type, "technical")
        self.assertTrue(req.use_rag)
        self.assertEqual(req.rag_top_k, 5)

    def test_full_valid(self):
        from app.api.v1.generate import GenerateRequest
        req = GenerateRequest(
            section_title="安全施工方案",
            section_type="safety",
            project_name="南京奥体中心",
            project_type="building",
            requirements="重点关注高空作业",
            scoring_points=["安全管理体系", "应急预案"],
            use_rag=False,
            rag_top_k=3,
        )
        self.assertEqual(req.section_type, "safety")
        self.assertFalse(req.use_rag)
        self.assertEqual(len(req.scoring_points), 2)

    def test_title_required(self):
        from app.api.v1.generate import GenerateRequest
        with self.assertRaises(ValidationError):
            GenerateRequest()  # type: ignore

    def test_rag_top_k_range(self):
        from app.api.v1.generate import GenerateRequest
        with self.assertRaises(ValidationError):
            GenerateRequest(section_title="test", rag_top_k=0)
        with self.assertRaises(ValidationError):
            GenerateRequest(section_title="test", rag_top_k=11)


# ============================================================
# ChatRequest 模型测试
# ============================================================
class TestChatRequestModel(unittest.TestCase):
    """ChatRequest Pydantic 模型"""

    def test_minimal_valid(self):
        from app.api.v1.generate import ChatRequest
        req = ChatRequest(user_question="如何保证混凝土质量？")
        self.assertEqual(req.user_question, "如何保证混凝土质量？")
        self.assertTrue(req.use_rag)
        self.assertEqual(req.module_content, "")

    def test_full_valid(self):
        from app.api.v1.generate import ChatRequest
        req = ChatRequest(
            module_content="混凝土浇筑应从低处开始...",
            user_question="大体积混凝土如何控温？",
            project_name="测试项目",
            project_type="bridge",
            use_rag=False,
        )
        self.assertEqual(req.project_type, "bridge")
        self.assertFalse(req.use_rag)

    def test_question_required(self):
        from app.api.v1.generate import ChatRequest
        with self.assertRaises(ValidationError):
            ChatRequest()  # type: ignore


# ============================================================
# SearchRequest 模型测试
# ============================================================
class TestSearchRequestModel(unittest.TestCase):
    """SearchRequest Pydantic 模型"""

    def test_minimal_valid(self):
        from app.api.v1.knowledge import SearchRequest
        req = SearchRequest(query="混凝土强度")
        self.assertEqual(req.top_k, 10)
        self.assertIsNone(req.project_type)

    def test_full_valid(self):
        from app.api.v1.knowledge import SearchRequest
        req = SearchRequest(
            query="桥梁预应力张拉",
            top_k=20,
            project_type="bridge",
            doc_section="technical",
            min_density="high",
        )
        self.assertEqual(req.top_k, 20)
        self.assertEqual(req.doc_section, "technical")

    def test_query_min_length(self):
        from app.api.v1.knowledge import SearchRequest
        with self.assertRaises(ValidationError):
            SearchRequest(query="a")  # min_length=2

    def test_top_k_range(self):
        from app.api.v1.knowledge import SearchRequest
        with self.assertRaises(ValidationError):
            SearchRequest(query="test", top_k=0)
        with self.assertRaises(ValidationError):
            SearchRequest(query="test", top_k=51)


# ============================================================
# BidGenerateService Prompt 构建测试 (Mock LLMSelector)
# ============================================================
class TestGenerateServicePrompt(unittest.TestCase):
    """BidGenerateService Prompt 构建 + 行业词库注入"""

    def _make_service(self):
        from app.services.generate_service import BidGenerateService
        svc = BidGenerateService.__new__(BidGenerateService)
        svc._tenant_id = "test"
        svc._selector = MagicMock()
        svc._desensitizer = MagicMock()
        return svc

    def test_system_prompt_contains_expert_role(self):
        """System Prompt 包含专家角色定义"""
        svc = self._make_service()
        prompt = svc.build_system_prompt(project_type="municipal_road")
        self.assertIn("标书", prompt)
        self.assertIn("专家", prompt)

    def test_system_prompt_injects_industry(self):
        """System Prompt 注入行业核心术语"""
        svc = self._make_service()
        prompt = svc.build_system_prompt(project_type="municipal_road")
        self.assertIn("市政道路", prompt)

    def test_system_prompt_unknown_type(self):
        """未知行业类型不崩溃"""
        svc = self._make_service()
        prompt = svc.build_system_prompt(project_type="unknown_type")
        self.assertIn("标书", prompt)

    def test_rag_prompt_includes_chunks(self):
        """RAG 检索结果注入到生成 Prompt"""
        svc = self._make_service()
        rag_data = [
            {"content": "沥青摊铺温度不低于120°C", "similarity": 0.85, "source_file": "test.pdf"},
            {"content": "压实度需达到96%以上", "similarity": 0.80, "source_file": "spec.pdf"},
        ]
        prompt = svc.build_rag_prompt(
            section_title="路面施工",
            section_type="technical",
            project_context="测试",
            rag_chunks=rag_data,
            project_type="municipal_road",
        )
        self.assertIn("沥青摊铺", prompt)
        self.assertIn("压实度", prompt)
        self.assertIn("REF:", prompt)

    def test_rag_prompt_empty_chunks(self):
        """无 RAG 数据时仍产生有效 Prompt"""
        svc = self._make_service()
        prompt = svc.build_rag_prompt(
            section_title="质量管理",
            section_type="quality",
            project_context="",
            rag_chunks=[],
        )
        self.assertIn("质量管理", prompt)
        # 空 chunks 时不应有编号引用（模板本身含格式说明是正常的）
        self.assertNotIn("[REF:1]", prompt)

    def test_rag_prompt_with_scoring_points(self):
        """评分点注入 Prompt"""
        svc = self._make_service()
        prompt = svc.build_rag_prompt(
            section_title="安全方案",
            section_type="safety",
            project_context="",
            rag_chunks=[],
            scoring_points=["安全管理体系", "应急预案"],
        )
        self.assertIn("安全管理体系", prompt)
        self.assertIn("评分点", prompt)

    def test_chat_prompt_includes_question(self):
        """Chat Prompt 包含用户问题"""
        svc = self._make_service()
        prompt = svc.build_chat_prompt(
            module_content="混凝土浇筑方案...",
            user_question="大体积混凝土如何控温？",
        )
        self.assertIn("大体积混凝土", prompt)
        self.assertIn("引用内容", prompt)

    def test_industry_context_loaded(self):
        """行业上下文加载正确"""
        svc = self._make_service()
        ctx = svc.get_industry_context("building")
        self.assertIn("label", ctx)
        self.assertEqual(ctx["label"], "房屋建筑工程")


if __name__ == "__main__":
    unittest.main()
