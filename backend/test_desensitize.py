"""
统一脱敏网关 — 单元测试
严禁连接真实数据库！所有外部 I/O 均通过 Mock 替代。

覆盖：
  1. mask() 正则自动发现（项目名、金额、电话）
  2. unmask() 回填还原
  3. 手动实体优先级
  4. mask-unmask 双向对称性
  5. 词典统计
"""
import unittest
from unittest.mock import patch, MagicMock
import psycopg2.extras


class TestDesensitizeMask(unittest.TestCase):
    """mask() 脱敏测试"""

    def _make_gateway(self):
        """构造不连接数据库的 DesensitizeGateway"""
        with patch("app.services.desensitize_service.psycopg2") as mock_pg:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
            mock_cursor.__exit__ = MagicMock(return_value=False)
            mock_cursor.fetchall.return_value = []  # 空词典
            mock_conn.cursor.return_value = mock_cursor
            mock_pg.connect.return_value = mock_conn
            mock_pg.extras = psycopg2.extras

            from app.services.desensitize_service import DesensitizeGateway
            gw = DesensitizeGateway(tenant_id="test")
            gw._conn = mock_conn
            return gw

    def test_mask_phone_number(self):
        """手动指定手机号实体并脱敏"""
        gw = self._make_gateway()
        text = "项目经理联系方式：13812345678"
        masked, mapping = gw.mask(text, extra_entities={"13812345678": "phone"})
        self.assertNotIn("13812345678", masked)
        self.assertIn("[PHONE_", masked)
        # mapping 中有回填信息
        found = [v for v in mapping.values() if "138" in v]
        self.assertTrue(len(found) > 0)

    def test_mask_amount(self):
        """自动发现金额并脱敏"""
        gw = self._make_gateway()
        text = "合同总价为1234.56万元，预算不超过2000万元"
        masked, mapping = gw.mask(text)
        self.assertIn("[AMOUNT_", masked)

    def test_mask_project_name(self):
        """自动发现项目名称并脱敏"""
        gw = self._make_gateway()
        text = "南京市江宁区滨江大道改造工程"
        masked, mapping = gw.mask(text)
        self.assertIn("[PROJECT_", masked)

    def test_mask_extra_entities_priority(self):
        """手动指定的实体优先于正则发现"""
        gw = self._make_gateway()
        text = "张三负责合肥市蜀山区道路改造工程的管理"
        masked, mapping = gw.mask(
            text,
            extra_entities={"张三": "person"},
        )
        self.assertIn("[PERSON_", masked)
        self.assertNotIn("张三", masked)

    def test_mask_no_sensitive_info(self):
        """无敏感信息 → 文本不变"""
        gw = self._make_gateway()
        text = "混凝土强度等级采用C35"
        masked, mapping = gw.mask(text)
        self.assertEqual(masked, text)
        self.assertEqual(len(mapping), 0)


class TestDesensitizeUnmask(unittest.TestCase):
    """unmask() 回填测试"""

    def _make_gateway(self):
        with patch("app.services.desensitize_service.psycopg2") as mock_pg:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
            mock_cursor.__exit__ = MagicMock(return_value=False)
            mock_cursor.fetchall.return_value = []
            mock_conn.cursor.return_value = mock_cursor
            mock_pg.connect.return_value = mock_conn
            mock_pg.extras = psycopg2.extras

            from app.services.desensitize_service import DesensitizeGateway
            gw = DesensitizeGateway(tenant_id="test")
            gw._conn = mock_conn
            return gw

    def test_unmask_with_mapping(self):
        """使用 mapping 回填占位符"""
        gw = self._make_gateway()
        masked_text = "联系方式：[PHONE_1]"
        mapping = {"[PHONE_1]": "13812345678"}
        result = gw.unmask(masked_text, mapping)
        self.assertEqual(result, "联系方式：13812345678")

    def test_unmask_no_mapping(self):
        """无 mapping 且无全局词典 → 文本不变"""
        gw = self._make_gateway()
        text = "普通文本内容"
        result = gw.unmask(text)
        self.assertEqual(result, text)

    def test_mask_unmask_roundtrip(self):
        """mask → unmask 双向对称性：原始文本应完全还原"""
        gw = self._make_gateway()
        original = "项目经理联系方式：13812345678"
        masked, mapping = gw.mask(original)
        restored = gw.unmask(masked, mapping)
        self.assertEqual(restored, original)


class TestDesensitizeStats(unittest.TestCase):
    """词典统计测试"""

    def _make_gateway_with_dict(self):
        with patch("app.services.desensitize_service.psycopg2") as mock_pg:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
            mock_cursor.__exit__ = MagicMock(return_value=False)
            mock_cursor.fetchall.return_value = [
                {"original_text": "张三", "placeholder": "[PERSON_1]", "entity_type": "person"},
                {"original_text": "13800000000", "placeholder": "[PHONE_1]", "entity_type": "phone"},
                {"original_text": "南京市建设工程", "placeholder": "[PROJECT_1]", "entity_type": "project"},
            ]
            mock_conn.cursor.return_value = mock_cursor
            mock_pg.connect.return_value = mock_conn
            mock_pg.extras = psycopg2.extras

            from app.services.desensitize_service import DesensitizeGateway
            gw = DesensitizeGateway(tenant_id="test")
            gw._conn = mock_conn
            return gw

    def test_dict_stats(self):
        """词典统计返回正确数量和分类"""
        gw = self._make_gateway_with_dict()
        stats = gw.get_dict_stats()
        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["tenant_id"], "test")
        self.assertIn("person", stats["by_type"])
        self.assertIn("phone", stats["by_type"])
        self.assertIn("project", stats["by_type"])

    def test_unmask_from_preloaded_dict(self):
        """回填使用预加载的全局词典"""
        gw = self._make_gateway_with_dict()
        text = "联系[PERSON_1]，电话[PHONE_1]，关于[PROJECT_1]"
        result = gw.unmask(text)
        self.assertIn("张三", result)
        self.assertIn("13800000000", result)
        self.assertIn("南京市建设工程", result)


if __name__ == "__main__":
    unittest.main()
