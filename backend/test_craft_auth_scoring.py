"""
工艺图谱 / 认证 / 评分 — Pydantic 模型与业务逻辑单元测试
覆盖：
  1. CraftMethod/CraftParameter/CraftDetail 模型校验
  2. CRAFT_DB 内置知识库完整性
  3. 工艺搜索/详情业务逻辑
  4. RegisterRequest/LoginRequest/TokenResponse 模型校验
  5. ExtractRequest/OutlineRequest 模型边界校验
严禁调用真实 LLM 或数据库。
"""
import asyncio
import unittest
from pydantic import ValidationError


# ============================================================
# CraftMethod 模型测试
# ============================================================
class TestCraftMethod(unittest.TestCase):
    """施工工法模型"""

    def test_valid(self):
        from app.api.v1.craft import CraftMethod
        m = CraftMethod(name="换填法", suitability="软弱地基", difficulty="低", cost="中")
        self.assertEqual(m.name, "换填法")
        self.assertEqual(m.difficulty, "低")

    def test_missing_field(self):
        from app.api.v1.craft import CraftMethod
        with self.assertRaises(ValidationError):
            CraftMethod(name="x")  # 缺 suitability/difficulty/cost


# ============================================================
# CraftParameter 模型测试
# ============================================================
class TestCraftParameter(unittest.TestCase):
    """技术参数模型"""

    def test_valid(self):
        from app.api.v1.craft import CraftParameter
        p = CraftParameter(name="压实度", standard="≥93%", source="JTG F10-2006")
        self.assertEqual(p.source, "JTG F10-2006")


# ============================================================
# CRAFT_DB 知识库完整性测试
# ============================================================
class TestCraftDB(unittest.TestCase):
    """内置工艺知识库"""

    def test_has_three_entries(self):
        from app.api.v1.craft import CRAFT_DB
        self.assertEqual(len(CRAFT_DB), 3)

    def test_all_entries_have_methods(self):
        from app.api.v1.craft import CRAFT_DB
        for key, detail in CRAFT_DB.items():
            self.assertGreater(len(detail.methods), 0, f"{key} 缺少 methods")

    def test_all_entries_have_workflow(self):
        from app.api.v1.craft import CRAFT_DB
        for key, detail in CRAFT_DB.items():
            self.assertGreater(len(detail.workflow), 0, f"{key} 缺少 workflow")

    def test_all_entries_have_parameters(self):
        from app.api.v1.craft import CRAFT_DB
        for key, detail in CRAFT_DB.items():
            self.assertGreater(len(detail.parameters), 0, f"{key} 缺少 parameters")

    def test_all_entries_have_risks(self):
        from app.api.v1.craft import CRAFT_DB
        for key, detail in CRAFT_DB.items():
            self.assertGreater(len(detail.risks), 0, f"{key} 缺少 risks")

    def test_all_entries_have_high_score_paragraph(self):
        from app.api.v1.craft import CRAFT_DB
        for key, detail in CRAFT_DB.items():
            self.assertGreater(len(detail.high_score_paragraph), 50, f"{key} 高分范文过短")


# ============================================================
# 工艺搜索/详情业务逻辑测试
# ============================================================
class TestCraftEndpoints(unittest.TestCase):
    """工艺图谱端点逻辑"""

    def test_get_craft_tree(self):
        from app.api.v1.craft import get_craft_tree
        result = asyncio.run(get_craft_tree())
        self.assertIn("tree", result)
        self.assertIn("total_nodes", result)
        self.assertGreater(result["total_nodes"], 0)

    def test_get_craft_detail_existing(self):
        from app.api.v1.craft import get_craft_detail
        result = asyncio.run(get_craft_detail("roadbed"))
        self.assertEqual(result["id"], "roadbed")
        self.assertIn("methods", result)

    def test_get_craft_detail_not_found(self):
        from app.api.v1.craft import get_craft_detail
        result = asyncio.run(get_craft_detail("nonexistent"))
        self.assertIn("error", result)

    def test_search_found(self):
        from app.api.v1.craft import search_craft
        result = asyncio.run(search_craft("路基"))
        self.assertGreater(result["count"], 0)

    def test_search_empty_query(self):
        from app.api.v1.craft import search_craft
        result = asyncio.run(search_craft(""))
        self.assertEqual(len(result["results"]), 0)

    def test_search_no_match(self):
        from app.api.v1.craft import search_craft
        result = asyncio.run(search_craft("不可能匹配的字符串xyz"))
        self.assertEqual(result["count"], 0)


# ============================================================
# Auth Pydantic 模型测试
# ============================================================
class TestAuthModels(unittest.TestCase):
    """认证请求模型"""

    def test_register_valid(self):
        from app.api.v1.auth import RegisterRequest
        req = RegisterRequest(username="test_user", email="test@example.com", password="123456")
        self.assertEqual(req.username, "test_user")
        self.assertIsNone(req.full_name)
        self.assertIsNone(req.company)

    def test_register_with_optional(self):
        from app.api.v1.auth import RegisterRequest
        req = RegisterRequest(
            username="user1",
            email="u1@co.com",
            password="abcdef",
            full_name="张三",
            company="测试公司",
        )
        self.assertEqual(req.full_name, "张三")

    def test_register_username_too_short(self):
        from app.api.v1.auth import RegisterRequest
        with self.assertRaises(ValidationError):
            RegisterRequest(username="a", email="x@y.com", password="123456")

    def test_register_password_too_short(self):
        from app.api.v1.auth import RegisterRequest
        with self.assertRaises(ValidationError):
            RegisterRequest(username="test", email="x@y.com", password="12345")

    def test_login_valid(self):
        from app.api.v1.auth import LoginRequest
        req = LoginRequest(username="admin", password="secret")
        self.assertEqual(req.username, "admin")

    def test_login_missing_password(self):
        from app.api.v1.auth import LoginRequest
        with self.assertRaises(ValidationError):
            LoginRequest(username="admin")

    def test_token_response(self):
        from app.api.v1.auth import TokenResponse
        resp = TokenResponse(
            access_token="aaa.bbb.ccc",
            refresh_token="ddd.eee.fff",
            user={"id": "123", "username": "test"},
        )
        self.assertEqual(resp.token_type, "bearer")

    def test_refresh_request(self):
        from app.api.v1.auth import RefreshRequest
        req = RefreshRequest(refresh_token="xxx.yyy.zzz")
        self.assertEqual(req.refresh_token, "xxx.yyy.zzz")


# ============================================================
# Scoring Pydantic 模型测试
# ============================================================
class TestScoringModels(unittest.TestCase):
    """评分点请求模型"""

    def test_extract_valid(self):
        from app.api.v1.scoring import ExtractRequest
        text = "投标评审标准：" + "一" * 100  # min_length=100
        req = ExtractRequest(bid_document_text=text)
        self.assertGreater(len(req.bid_document_text), 100)

    def test_extract_too_short(self):
        from app.api.v1.scoring import ExtractRequest
        with self.assertRaises(ValidationError):
            ExtractRequest(bid_document_text="太短")

    def test_outline_valid(self):
        from app.api.v1.scoring import OutlineRequest
        text = "招标文件" + "x" * 100
        req = OutlineRequest(bid_document_text=text)
        self.assertEqual(req.bid_type, "service")

    def test_outline_custom_type(self):
        from app.api.v1.scoring import OutlineRequest
        text = "招标文件" + "x" * 100
        req = OutlineRequest(bid_document_text=text, bid_type="construction")
        self.assertEqual(req.bid_type, "construction")


if __name__ == "__main__":
    unittest.main()
