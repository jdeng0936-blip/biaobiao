"""
标标 AI — LLM 生成服务 Mock 测试
严禁调用真实大模型 API！所有外部通信均通过 Mock 替代。
"""
import json
import asyncio
import unittest
from unittest.mock import AsyncMock, patch, MagicMock


class TestBidGenerateService(unittest.IsolatedAsyncioTestCase):
    """BidGenerateService 基础功能测试（全 Mock）"""

    def setUp(self):
        """构造 Mock LLM Selector"""
        self.mock_response = MagicMock()
        self.mock_response.text = json.dumps({
            "outline": "一、工程概况 二、施工方案 三、质量措施",
            "queries": ["混凝土配合比", "钢筋绑扎规范"]
        })

        self.mock_selector = MagicMock()
        self.mock_selector.generate = AsyncMock(return_value=self.mock_response)

    @patch("app.services.generate_service.get_llm_selector")
    async def test_build_system_prompt(self, mock_get_selector):
        """系统 Prompt 构建测试"""
        mock_get_selector.return_value = self.mock_selector
        from app.services.generate_service import BidGenerateService

        service = BidGenerateService(tenant_id="test_tenant")
        prompt = service.build_system_prompt()

        self.assertIn("标书编写专家", prompt)
        self.assertIn("Markdown", prompt)
        self.assertIn("中文编号", prompt)

    @patch("app.services.generate_service.get_llm_selector")
    async def test_build_rag_prompt(self, mock_get_selector):
        """RAG Prompt 构建测试"""
        mock_get_selector.return_value = self.mock_selector
        from app.services.generate_service import BidGenerateService

        service = BidGenerateService(tenant_id="test_tenant")
        prompt = service.build_rag_prompt(
            section_title="3.1 工程概况",
            section_type="overview",
            project_context="市政道路改造",
            rag_chunks=[
                {"content": "测试知识片段", "source_file": "test.pdf", "similarity": 0.92}
            ],
            scoring_points=["施工进度计划合理性", "安全文明施工措施"],
        )

        self.assertIn("工程概况", prompt)
        self.assertIn("测试知识片段", prompt)
        self.assertIn("REF:1", prompt)
        self.assertIn("施工进度计划合理性", prompt)

    @patch("app.services.generate_service.get_llm_selector")
    async def test_planner_returns_valid_json(self, mock_get_selector):
        """Planner 节点返回有效 JSON（Mock LLM 返回）"""
        mock_get_selector.return_value = self.mock_selector
        from app.services.generate_service import BidGenerateService

        service = BidGenerateService(tenant_id="test_tenant")
        result = await service._run_planner(
            section_title="施工组织设计",
            project_context="桥梁工程",
            user_requirements="重点关注安全",
        )

        self.assertIn("outline", result)
        self.assertIn("queries", result)
        self.assertIsInstance(result["queries"], list)

    @patch("app.services.generate_service.get_llm_selector")
    async def test_reviewer_pass(self, mock_get_selector):
        """Reviewer 节点通过审核（Mock 返回 passed=True）"""
        pass_response = MagicMock()
        pass_response.text = json.dumps({"passed": True, "feedbacks": []})
        self.mock_selector.generate = AsyncMock(return_value=pass_response)
        mock_get_selector.return_value = self.mock_selector

        from app.services.generate_service import BidGenerateService

        service = BidGenerateService(tenant_id="test_tenant")
        result = await service._run_reviewer(
            draft="本工程为市政道路改造项目，采用沥青混凝土路面...",
            scoring_points=["施工方案详细", "安全措施到位"],
        )

        self.assertTrue(result["passed"])


class TestChatService(unittest.IsolatedAsyncioTestCase):
    """Chat 对话服务 Mock 测试"""

    @patch("app.services.generate_service.get_llm_selector")
    async def test_build_chat_prompt(self, mock_get_selector):
        """Chat Prompt 构建测试"""
        mock_selector = MagicMock()
        mock_get_selector.return_value = mock_selector

        from app.services.generate_service import BidGenerateService

        service = BidGenerateService(tenant_id="test_tenant")
        prompt = service.build_chat_prompt(
            module_content="本工程采用 C35 混凝土",
            user_question="C35 混凝土的抗压强度是多少？",
            project_context="桥梁工程",
        )

        self.assertIn("C35 混凝土", prompt)
        self.assertIn("抗压强度", prompt)
        self.assertIn("引用内容", prompt)


if __name__ == "__main__":
    unittest.main()
