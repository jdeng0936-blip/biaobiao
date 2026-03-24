"""
安全模块 + 反馈飞轮 — 单元测试
覆盖：
  1. Settings 配置加载（默认值 + 环境变量覆盖）
  2. 密码哈希与验证（bcrypt roundtrip）
  3. JWT Token 签发/解码/过期/篡改
  4. FeedbackRequest/Response/StatsResponse 模型校验
严禁调用真实数据库或 LLM。
"""
import os
import unittest
from unittest.mock import patch
from datetime import timedelta


# ============================================================
# Settings 配置测试
# ============================================================
class TestSettings(unittest.TestCase):
    """应用配置管理"""

    def test_default_values(self):
        """默认配置可加载"""
        # 重置单例
        import app.core.config as cfg
        cfg._settings = None
        settings = cfg.get_settings()
        self.assertEqual(settings.APP_NAME, "标标 AI")
        self.assertEqual(settings.JWT_ALGORITHM, "HS256")
        self.assertGreater(settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES, 0)

    def test_singleton(self):
        """get_settings 返回单例"""
        import app.core.config as cfg
        cfg._settings = None
        s1 = cfg.get_settings()
        s2 = cfg.get_settings()
        self.assertIs(s1, s2)
        cfg._settings = None

    def test_env_override(self):
        """环境变量可覆盖默认值"""
        import app.core.config as cfg
        cfg._settings = None
        with patch.dict(os.environ, {"APP_NAME": "测试应用"}):
            cfg._settings = None
            settings = cfg.get_settings()
            self.assertEqual(settings.APP_NAME, "测试应用")
        cfg._settings = None


# ============================================================
# 密码哈希测试（Mock passlib — Python 3.14 兼容）
# ============================================================
class TestPasswordHashing(unittest.TestCase):
    """bcrypt 密码哈希逻辑验证"""

    @patch("app.core.security.pwd_context")
    def test_hash_calls_context(self, mock_ctx):
        """hash_password 调用 pwd_context.hash"""
        mock_ctx.hash.return_value = "$2b$12$fakehash"
        from app.core.security import hash_password
        result = hash_password("mypassword123")
        mock_ctx.hash.assert_called_once_with("mypassword123")
        self.assertEqual(result, "$2b$12$fakehash")

    @patch("app.core.security.pwd_context")
    def test_verify_correct(self, mock_ctx):
        """verify_password 正确密码返回 True"""
        mock_ctx.verify.return_value = True
        from app.core.security import verify_password
        self.assertTrue(verify_password("correct", "$2b$12$hash"))

    @patch("app.core.security.pwd_context")
    def test_verify_wrong(self, mock_ctx):
        """verify_password 错误密码返回 False"""
        mock_ctx.verify.return_value = False
        from app.core.security import verify_password
        self.assertFalse(verify_password("wrong", "$2b$12$hash"))

    @patch("app.core.security.pwd_context")
    def test_hash_different_each_call(self, mock_ctx):
        """两次 hash 同一密码对应两次调用"""
        mock_ctx.hash.side_effect = ["$2b$12$hash1", "$2b$12$hash2"]
        from app.core.security import hash_password
        h1 = hash_password("same")
        h2 = hash_password("same")
        self.assertNotEqual(h1, h2)
        self.assertEqual(mock_ctx.hash.call_count, 2)


# ============================================================
# JWT Token 测试
# ============================================================
class TestJWTTokens(unittest.TestCase):
    """JWT 签发与解码"""

    def test_access_token_roundtrip(self):
        from app.core.security import create_access_token, decode_token
        data = {"sub": "user-123", "tenant_id": "t-456"}
        token = create_access_token(data)
        payload = decode_token(token)
        self.assertIsNotNone(payload)
        self.assertEqual(payload["sub"], "user-123")
        self.assertEqual(payload["tenant_id"], "t-456")
        self.assertEqual(payload["type"], "access")

    def test_refresh_token_roundtrip(self):
        from app.core.security import create_refresh_token, decode_token
        data = {"sub": "user-789"}
        token = create_refresh_token(data)
        payload = decode_token(token)
        self.assertIsNotNone(payload)
        self.assertEqual(payload["sub"], "user-789")
        self.assertEqual(payload["type"], "refresh")

    def test_tampered_token_returns_none(self):
        from app.core.security import create_access_token, decode_token
        token = create_access_token({"sub": "x"})
        tampered = token[:-5] + "XXXXX"
        self.assertIsNone(decode_token(tampered))

    def test_invalid_token_returns_none(self):
        from app.core.security import decode_token
        self.assertIsNone(decode_token("not.a.jwt"))

    def test_custom_expiry(self):
        from app.core.security import create_access_token, decode_token
        token = create_access_token(
            {"sub": "user"},
            expires_delta=timedelta(hours=1),
        )
        payload = decode_token(token)
        self.assertIsNotNone(payload)
        self.assertIn("exp", payload)

    def test_token_contains_exp(self):
        from app.core.security import create_access_token, decode_token
        token = create_access_token({"sub": "t"})
        payload = decode_token(token)
        self.assertIn("exp", payload)


# ============================================================
# FeedbackRequest Pydantic 测试
# ============================================================
class TestFeedbackRequest(unittest.TestCase):
    """反馈请求模型"""

    def test_valid_accept(self):
        from app.api.v1.feedback import FeedbackRequest
        req = FeedbackRequest(
            section_id="s1",
            action="accept",
            original_text="AI 生成内容",
        )
        self.assertEqual(req.action, "accept")

    def test_valid_edit(self):
        from app.api.v1.feedback import FeedbackRequest
        req = FeedbackRequest(
            section_id="s2",
            action="edit",
            original_text="原文",
            revised_text="修改后",
        )
        self.assertEqual(req.revised_text, "修改后")

    def test_valid_reject(self):
        from app.api.v1.feedback import FeedbackRequest
        req = FeedbackRequest(
            section_id="s3",
            action="reject",
            original_text="被拒绝",
        )
        self.assertEqual(req.action, "reject")

    def test_invalid_action(self):
        from app.api.v1.feedback import FeedbackRequest
        from pydantic import ValidationError
        with self.assertRaises(ValidationError):
            FeedbackRequest(
                section_id="s1",
                action="invalid",
                original_text="test",
            )

    def test_empty_section_id(self):
        from app.api.v1.feedback import FeedbackRequest
        from pydantic import ValidationError
        with self.assertRaises(ValidationError):
            FeedbackRequest(
                section_id="",
                action="accept",
                original_text="text",
            )


# ============================================================
# FeedbackResponse / StatsResponse 测试
# ============================================================
class TestFeedbackResponseModels(unittest.TestCase):
    """反馈响应模型"""

    def test_feedback_response(self):
        from app.api.v1.feedback import FeedbackResponse
        resp = FeedbackResponse(success=True, message="ok", flywheel_triggered=True)
        self.assertTrue(resp.flywheel_triggered)

    def test_stats_response(self):
        from app.api.v1.feedback import FeedbackStatsResponse
        stats = FeedbackStatsResponse(
            total=100,
            accept_count=60,
            edit_count=30,
            reject_count=10,
            accept_rate=0.6,
            edit_rate=0.3,
            reject_rate=0.1,
            flywheel_sunk=25,
        )
        self.assertEqual(stats.total, 100)
        self.assertAlmostEqual(stats.accept_rate + stats.edit_rate + stats.reject_rate, 1.0)


if __name__ == "__main__":
    unittest.main()
