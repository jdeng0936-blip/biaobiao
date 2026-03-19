"""
标标 AI — RAG 知识库服务 Mock 测试
严禁连接真实数据库或上传真实文件！所有外部 I/O 均通过 Mock 替代。
"""
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime


class TestKnowledgeService(unittest.TestCase):
    """KnowledgeService 三层检索 Mock 测试"""

    def _mock_cursor_factory(self, results):
        """构造 Mock 数据库游标"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = results
        mock_cursor.fetchone.return_value = results[0] if results else None
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        return mock_cursor

    @patch("app.services.knowledge_service.psycopg2.connect")
    def test_search_semantic(self, mock_connect):
        """Layer 1 — pgvector 语义检索（Mock 数据库返回）"""
        mock_rows = [
            {
                "id": 1, "content": "C35抗渗混凝土施工方案",
                "source_file": "高分标书.pdf", "chapter": "第三章",
                "section": "3.1", "project_type": ["municipal_road"],
                "doc_section": "technical", "craft_tags": [],
                "char_count": 500, "has_params": True,
                "data_density": "high", "similarity": 0.92,
            },
        ]
        mock_conn = MagicMock()
        mock_conn.closed = False
        mock_conn.cursor.return_value = self._mock_cursor_factory(mock_rows)
        mock_connect.return_value = mock_conn

        from app.services.knowledge_service import KnowledgeService
        ks = KnowledgeService(db_url="postgresql://mock@localhost/mock")
        ks._conn = mock_conn

        results = ks.search_semantic(
            query_embedding=[0.0] * 768,
            top_k=3,
            tenant_id="test_tenant",
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["content"], "C35抗渗混凝土施工方案")
        self.assertEqual(results[0]["retrieval_layer"], "L1_semantic")

    @patch("app.services.knowledge_service.psycopg2.connect")
    def test_search_structured(self, mock_connect):
        """Layer 2 — 结构化表格查询（Mock 数据库返回）"""
        mock_rows = [
            {
                "id": 10, "source_file": "工程量清单.xlsx",
                "table_type": "bill_of_quantities",
                "table_title": "分部分项工程量清单",
                "row_index": 1,
                "row_data": {"项目名称": "沥青路面", "单位": "m²", "数量": "15000"},
                "raw_text": "沥青路面 15000 m²",
                "numeric_value_1": 15000.0, "numeric_label_1": "数量",
                "numeric_value_2": None, "numeric_label_2": None,
            },
        ]
        mock_conn = MagicMock()
        mock_conn.closed = False
        mock_conn.cursor.return_value = self._mock_cursor_factory(mock_rows)
        mock_connect.return_value = mock_conn

        from app.services.knowledge_service import KnowledgeService
        ks = KnowledgeService(db_url="postgresql://mock@localhost/mock")
        ks._conn = mock_conn

        results = ks.search_structured(
            query_text="沥青路面",
            tenant_id="test_tenant",
            top_k=3,
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["retrieval_layer"], "L2_structured")

    def test_merge_results_dedup(self):
        """Layer 3 — 融合去重逻辑"""
        from app.services.knowledge_service import KnowledgeService

        semantic = [
            {"id": "1", "content": "A", "similarity": 0.95},
            {"id": "2", "content": "B", "similarity": 0.85},
        ]
        structured = [
            {"id": "2", "content": "B-dup", "similarity": 0.85},
            {"id": "3", "content": "C", "similarity": 0.80},
        ]

        merged = KnowledgeService._merge_results(semantic, structured, top_k=5)

        ids = [m["id"] for m in merged]
        # id=2 不应重复
        self.assertEqual(len(ids), len(set(ids)), "融合结果不应出现重复 ID")
        self.assertEqual(len(merged), 3)

    @patch("app.services.knowledge_service.psycopg2.connect")
    def test_insert_feedback_chunk(self, mock_connect):
        """Feedback Flywheel — 飞轮语料入库（Mock 数据库写入）"""
        mock_conn = MagicMock()
        mock_conn.closed = False
        mock_cursor = MagicMock()
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        from app.services.knowledge_service import KnowledgeService
        ks = KnowledgeService(db_url="postgresql://mock@localhost/mock")
        ks._conn = mock_conn

        result = ks.insert_feedback_chunk(
            content="人工修订的高质量施工方案文本，包含详细的混凝土配合比参数...",
            section="3.1 工程概况",
            tenant_id="test_tenant",
            source_tag="human_revised",
            metadata={"diff_ratio": 0.35},
        )

        self.assertTrue(result)
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()


class TestFeedbackService(unittest.IsolatedAsyncioTestCase):
    """FeedbackFlywheelService Mock 测试"""

    async def test_diff_calculation(self):
        """差异度计算测试"""
        from app.services.feedback_service import FeedbackFlywheelService

        svc = FeedbackFlywheelService(tenant_id="test")

        # 完全相同
        self.assertEqual(svc._calculate_diff_ratio("hello", "hello"), 0.0)

        # 完全不同
        ratio = svc._calculate_diff_ratio("apple banana cherry", "x y z w")
        self.assertGreater(ratio, 0.5)

        # 空文本
        self.assertEqual(svc._calculate_diff_ratio("", "something"), 1.0)

    async def test_accept_no_flywheel(self):
        """采纳动作不触发飞轮"""
        from app.services.feedback_service import FeedbackFlywheelService

        svc = FeedbackFlywheelService(tenant_id="test")
        result = await svc.ingest_feedback(
            target_section="3.1 工程概况",
            original_ai_text="原始文本",
            user_revised_text="原始文本",
            action="accept",
        )

        self.assertFalse(result)

    async def test_edit_below_threshold_no_flywheel(self):
        """编辑幅度不足不触发飞轮"""
        from app.services.feedback_service import FeedbackFlywheelService

        svc = FeedbackFlywheelService(tenant_id="test")
        result = await svc.ingest_feedback(
            target_section="3.1 工程概况",
            original_ai_text="这是一段很长很长的标书原始文本，大约需要超过五十个字才有意义",
            user_revised_text="这是一段很长很长的标书修改文本，大约需要超过五十个字才有意义",
            action="edit",
        )

        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
