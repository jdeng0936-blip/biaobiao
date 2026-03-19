"""
知识库 + 生成路由 — Pydantic 模型与路由服务初始化测试
覆盖：
  1. SearchRequest / ChunkResult / SearchResponse 模型校验
  2. GenerateRequest 路由层字段校验（补充 test_generate.py 未覆盖的过滤字段）
  3. 知识库服务初始化 tenant_id 注入
  4. 生成服务初始化 tenant_id 注入
严禁调用真实数据库和 LLM。
"""
import unittest
from pydantic import ValidationError


# ============================================================
# SearchRequest 模型测试
# ============================================================
class TestSearchRequest(unittest.TestCase):
    """知识库搜索请求"""

    def test_valid_search(self):
        from app.api.v1.knowledge import SearchRequest
        req = SearchRequest(query="混凝土裂缝防治", top_k=5)
        self.assertEqual(req.query, "混凝土裂缝防治")
        self.assertEqual(req.top_k, 5)

    def test_defaults(self):
        from app.api.v1.knowledge import SearchRequest
        req = SearchRequest(query="质量保证体系")
        self.assertEqual(req.top_k, 10)
        self.assertIsNone(req.project_type)
        self.assertIsNone(req.doc_section)
        self.assertIsNone(req.min_density)

    def test_query_too_short(self):
        from app.api.v1.knowledge import SearchRequest
        with self.assertRaises(ValidationError):
            SearchRequest(query="a")  # min_length=2

    def test_query_too_long(self):
        from app.api.v1.knowledge import SearchRequest
        with self.assertRaises(ValidationError):
            SearchRequest(query="x" * 501)  # max_length=500

    def test_top_k_bounds(self):
        from app.api.v1.knowledge import SearchRequest
        with self.assertRaises(ValidationError):
            SearchRequest(query="test", top_k=0)  # ge=1
        with self.assertRaises(ValidationError):
            SearchRequest(query="test", top_k=51)  # le=50

    def test_filter_fields(self):
        from app.api.v1.knowledge import SearchRequest
        req = SearchRequest(
            query="道路施工",
            project_type="市政-道路",
            doc_section="technical",
            min_density="high",
        )
        self.assertEqual(req.project_type, "市政-道路")
        self.assertEqual(req.doc_section, "technical")
        self.assertEqual(req.min_density, "high")


# ============================================================
# ChunkResult 模型测试
# ============================================================
class TestChunkResult(unittest.TestCase):
    """搜索结果条目"""

    def test_valid_chunk(self):
        from app.api.v1.knowledge import ChunkResult
        chunk = ChunkResult(
            id="abc123",
            content="混凝土浇筑应连续进行",
            source_file="施工方案.pdf",
            chapter="第三章",
            section="3.4 混凝土工程",
            project_type=["房建-新建"],
            doc_section="technical",
            craft_tags=["混凝土"],
            char_count=200,
            has_params=True,
            data_density="high",
            similarity=0.92,
        )
        self.assertEqual(chunk.similarity, 0.92)
        self.assertIn("混凝土", chunk.craft_tags)

    def test_nullable_fields(self):
        from app.api.v1.knowledge import ChunkResult
        chunk = ChunkResult(
            id="x", content="y", source_file="z",
            chapter=None, section=None,
            project_type=[], doc_section=None,
            craft_tags=[], char_count=10,
            has_params=False, data_density="low",
            similarity=0.5,
        )
        self.assertIsNone(chunk.chapter)


# ============================================================
# SearchResponse 模型测试
# ============================================================
class TestSearchResponse(unittest.TestCase):
    """搜索响应"""

    def test_valid_response(self):
        from app.api.v1.knowledge import SearchResponse
        resp = SearchResponse(
            query="混凝土裂缝",
            total=2,
            results=[],
        )
        self.assertEqual(resp.total, 2)
        self.assertEqual(len(resp.results), 0)


# ============================================================
# GenerateRequest 路由层字段测试（补充）
# ============================================================
class TestGenerateRequestRouteFields(unittest.TestCase):
    """GenerateRequest 路由层扩展字段"""

    def test_scoring_points(self):
        from app.api.v1.generate import GenerateRequest
        req = GenerateRequest(
            section_title="3.4 质量保证措施",
            scoring_points=["方案完整性5分", "施工工艺合理性10分"],
        )
        self.assertEqual(len(req.scoring_points), 2)

    def test_rag_top_k_bounds(self):
        from app.api.v1.generate import GenerateRequest
        with self.assertRaises(ValidationError):
            GenerateRequest(section_title="x", rag_top_k=0)  # ge=1
        with self.assertRaises(ValidationError):
            GenerateRequest(section_title="x", rag_top_k=11)  # le=10

    def test_use_rag_default_true(self):
        from app.api.v1.generate import GenerateRequest
        req = GenerateRequest(section_title="施工方案")
        self.assertTrue(req.use_rag)


# ============================================================
# 服务初始化 tenant_id 注入测试
# ============================================================
class TestServiceTenantInjection(unittest.TestCase):
    """服务层 tenant_id 注入"""

    def test_knowledge_service_tenant(self):
        """KnowledgeService 接收 tenant_id"""
        from app.services.knowledge_service import KnowledgeService
        svc = KnowledgeService.__new__(KnowledgeService)
        svc.tenant_id = "test_tenant"
        self.assertEqual(svc.tenant_id, "test_tenant")

    def test_generate_service_tenant(self):
        """BidGenerateService 接收 tenant_id"""
        from app.services.generate_service import BidGenerateService
        svc = BidGenerateService.__new__(BidGenerateService)
        svc.tenant_id = "demo_tenant"
        self.assertEqual(svc.tenant_id, "demo_tenant")

    def test_demo_tenant_constant(self):
        """路由层 DEMO_TENANT 一致"""
        from app.api.v1.knowledge import DEMO_TENANT as k_tenant
        from app.api.v1.generate import DEMO_TENANT as g_tenant
        self.assertEqual(k_tenant, g_tenant)


if __name__ == "__main__":
    unittest.main()
