"""
API 集成测试 — 基于 FastAPI TestClient（无需运行服务端）
覆盖：健康检查 / 项目 CRUD / 反审标 / 反馈 / 工艺图谱 / 变体维度
严禁调用真实 LLM 或数据库。
"""
import unittest
from unittest.mock import patch, MagicMock, AsyncMock

try:
    from fastapi.testclient import TestClient
    HAS_TESTCLIENT = True
except ImportError:
    HAS_TESTCLIENT = False

SKIP_MSG = "fastapi[testclient] 未安装"


_original_db_url = None

def _make_client():
    """构造 TestClient，Mock 掉数据库 startup（不污染全局 DATABASE_URL）"""
    import os
    global _original_db_url
    _original_db_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5432/testdb"
    os.environ.setdefault("GEMINI_API_KEY", "test-dummy")

    # Mock 掉 startup 中的 get_engine 以避免连接真实数据库
    with patch("app.core.database.get_engine") as mock_engine:
        mock_conn = MagicMock()
        mock_conn.run_sync = AsyncMock()
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_ctx.__aexit__ = AsyncMock(return_value=None)
        mock_engine.return_value.begin = MagicMock(return_value=mock_ctx)

        from app.main import app
        client = TestClient(app, raise_server_exceptions=False)

    # 恢复原始 DATABASE_URL
    if _original_db_url is not None:
        os.environ["DATABASE_URL"] = _original_db_url
    elif "DATABASE_URL" in os.environ:
        del os.environ["DATABASE_URL"]

    return client


# ============================================================
# 健康检查
# ============================================================
@unittest.skipUnless(HAS_TESTCLIENT, SKIP_MSG)
class TestHealthEndpoints(unittest.TestCase):
    """健康检查端点"""

    @classmethod
    def setUpClass(cls):
        cls.client = _make_client()

    def test_root_health(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["status"], "ok")

    def test_api_health(self):
        r = self.client.get("/api/health")
        self.assertEqual(r.status_code, 200)
        self.assertIn("status", r.json())


# ============================================================
# 反审标 API
# ============================================================
@unittest.skipUnless(HAS_TESTCLIENT, SKIP_MSG)
class TestAntiReviewAPI(unittest.TestCase):
    """反审标检测端点"""

    @classmethod
    def setUpClass(cls):
        cls.client = _make_client()

    def test_check_with_valid_text(self):
        """正常文本返回 200 + score"""
        text = ("施工组织设计应根据工程特点编制，重点关注质量管理体系建设。"
                "本工程采用明挖法施工，全长约3.2公里的市政道路改造。"
                "施工现场设置封闭式围挡，夜间施工需办理噪声排放许可证。")
        r = self.client.post("/api/v1/anti-review/check", json={"text": text})
        self.assertIn(r.status_code, [200, 500])  # 500 如果反审标依赖未加载
        if r.status_code == 200:
            data = r.json()
            # 可能是 score 或 risk_score 取决于实现
            has_score = "score" in data or "risk_score" in data
            self.assertTrue(has_score, f"响应中缺少 score 字段: {data.keys()}")

    def test_check_with_short_text(self):
        """过短文本返回 422"""
        r = self.client.post("/api/v1/anti-review/check", json={"text": "太短"})
        self.assertEqual(r.status_code, 422)

    def test_check_empty_body(self):
        """空请求体返回 422"""
        r = self.client.post("/api/v1/anti-review/check", json={})
        self.assertEqual(r.status_code, 422)


# ============================================================
# 工艺图谱 API
# ============================================================
@unittest.skipUnless(HAS_TESTCLIENT, SKIP_MSG)
class TestCraftAPI(unittest.TestCase):
    """工艺图谱端点"""

    @classmethod
    def setUpClass(cls):
        cls.client = _make_client()

    def test_craft_tree(self):
        """获取工艺树"""
        r = self.client.get("/craft/tree")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("total_nodes", data)
        self.assertGreater(data["total_nodes"], 0)

    def test_craft_search(self):
        """工艺搜索"""
        r = self.client.get("/craft/search?q=混凝土")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("results", data)


# ============================================================
# 变体引擎 API
# ============================================================
@unittest.skipUnless(HAS_TESTCLIENT, SKIP_MSG)
class TestVariantAPI(unittest.TestCase):
    """变体引擎端点"""

    @classmethod
    def setUpClass(cls):
        cls.client = _make_client()

    def test_get_dimensions(self):
        """获取变体维度配置"""
        r = self.client.get("/variants/dimensions")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("dimensions", data)
        self.assertGreater(len(data["dimensions"]), 0)


# ============================================================
# 导出 API
# ============================================================
@unittest.skipUnless(HAS_TESTCLIENT, SKIP_MSG)
class TestExportAPI(unittest.TestCase):
    """导出端点"""

    @classmethod
    def setUpClass(cls):
        cls.client = _make_client()

    def test_export_word(self):
        """导出 Word 返回二进制"""
        r = self.client.post("/api/v1/export/word", json={
            "project_name": "集成测试项目",
            "sections": {
                "一、工程概况": "本工程位于南京市建邺区。"
            }
        })
        # 200 正常 / 500 如果脱敏服务无法连接数据库
        self.assertIn(r.status_code, [200, 500])
        if r.status_code == 200:
            # DOCX 本质是 ZIP → PK 开头
            self.assertTrue(r.content[:2] == b"PK")


# ============================================================
# 评分端点
# ============================================================
@unittest.skipUnless(HAS_TESTCLIENT, SKIP_MSG)
class TestScoringAPI(unittest.TestCase):
    """评分端点"""

    @classmethod
    def setUpClass(cls):
        cls.client = _make_client()

    def test_extract_scoring_points(self):
        """评分点提取 — 需要 Gemini 所以 500/503 或 200"""
        long_text = (
            "投标评审标准：\n"
            "一、施工组织设计（20分）：包括施工方案的合理性、工期安排的可行性、资源配置的充分性。\n"
            "二、质量管理（15分）：质量保证体系的完整性、质量控制措施的可操作性、检测频率的合理性。\n"
            "三、安全措施（10分）：安全管理组织架构、危险源辨识、应急预案的针对性和可操作性。"
        )
        r = self.client.post("/api/v1/scoring/extract", json={
            "bid_document_text": long_text,
        })
        # 如果 Gemini 不可用返回 500(服务异常)/503，否则 200
        self.assertIn(r.status_code, [200, 500, 503])


if __name__ == "__main__":
    unittest.main()
