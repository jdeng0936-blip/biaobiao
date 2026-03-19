"""
单元测试 — FeedbackFlywheelService

覆盖：
  1. diff 计算（difflib.SequenceMatcher）
  2. accept / edit / reject 各分支
  3. 飞轮触发阈值判断
  4. DB 持久化写入验证
  5. 统计查询

所有外部依赖（DB、KnowledgeService）全量 Mock，严禁真实请求。
"""
import uuid
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.feedback_service import FeedbackFlywheelService
from app.models.feedback_log import FeedbackLog


# ============================================================
# 1. diff 计算测试
# ============================================================


class TestDiffRatio:
    """difflib.SequenceMatcher 差异比率计算"""

    def test_identical_texts(self):
        """完全相同文本 → diff=0"""
        ratio = FeedbackFlywheelService._calculate_diff_ratio("hello world", "hello world")
        assert ratio == 0.0

    def test_empty_original(self):
        """空原文 → diff=1"""
        ratio = FeedbackFlywheelService._calculate_diff_ratio("", "hello")
        assert ratio == 1.0

    def test_small_change(self):
        """微小修改 → diff 较低"""
        original = "本项目采用综合评估法进行评标，技术标占比60%"
        revised = "本项目采用综合评估法进行评标，技术标占比65%"
        ratio = FeedbackFlywheelService._calculate_diff_ratio(original, revised)
        assert 0 < ratio < 0.10  # 仅修改了一个数字

    def test_significant_change(self):
        """大幅修改 → diff > 阈值"""
        original = "施工组织设计方案"
        revised = "本工程位于安徽省合肥市蜀山区，总长度8.5公里，采用双向四车道设计标准"
        ratio = FeedbackFlywheelService._calculate_diff_ratio(original, revised)
        assert ratio > FeedbackFlywheelService.DIFF_THRESHOLD

    def test_completely_different(self):
        """完全不同文本 → diff接近1"""
        ratio = FeedbackFlywheelService._calculate_diff_ratio(
            "AAAAAAAAAA", "ZZZZZZZZZZ"
        )
        assert ratio > 0.8


# ============================================================
# 2. ingest_feedback 各分支测试
# ============================================================


class TestIngestFeedback:
    """反馈入库 + 飞轮决策测试"""

    @pytest.fixture
    def mock_db(self):
        """Mock AsyncSession — 拦截 add/commit"""
        db = AsyncMock()
        db.add = MagicMock()
        return db

    @pytest.fixture
    def service(self):
        return FeedbackFlywheelService(tenant_id="test_tenant")

    @pytest.mark.asyncio
    async def test_accept_feedback(self, service, mock_db):
        """accept 动作 → 不触发飞轮，但入库"""
        result = await service.ingest_feedback(
            db=mock_db,
            target_section="3.1 工程概况",
            section_id="3-1",
            original_ai_text="AI 生成的工程概况内容",
            user_revised_text="AI 生成的工程概况内容",
            action="accept",
        )
        assert result is False
        # 验证 DB 写入被调用
        mock_db.add.assert_called_once()
        log: FeedbackLog = mock_db.add.call_args[0][0]
        assert log.action == "accept"
        assert log.tenant_id == "test_tenant"
        assert log.flywheel_triggered is False
        assert log.revised_text is None

    @pytest.mark.asyncio
    async def test_reject_feedback(self, service, mock_db):
        """reject 动作 → 不触发飞轮，但入库"""
        result = await service.ingest_feedback(
            db=mock_db,
            target_section="3.2 施工组织设计",
            section_id="3-2",
            original_ai_text="AI 写的内容被拒绝",
            user_revised_text="AI 写的内容被拒绝",
            action="reject",
        )
        assert result is False
        log: FeedbackLog = mock_db.add.call_args[0][0]
        assert log.action == "reject"

    @pytest.mark.asyncio
    @patch.object(FeedbackFlywheelService, "_async_sink_to_knowledge_base", new_callable=AsyncMock)
    async def test_edit_triggers_flywheel(self, mock_sink, service, mock_db):
        """edit + 大幅修改 → 触发飞轮 + 入库"""
        original = "简单的施工方案描述" * 5
        revised = "本工程位于安徽省合肥市蜀山区，总长度8.5公里，采用双向四车道设计标准，路基宽度24.5米，设计速度60km/h。" * 3

        result = await service.ingest_feedback(
            db=mock_db,
            target_section="3.1 工程概况",
            section_id="3-1",
            original_ai_text=original,
            user_revised_text=revised,
            action="edit",
        )
        assert result is True
        log: FeedbackLog = mock_db.add.call_args[0][0]
        assert log.action == "edit"
        assert log.flywheel_triggered is True
        assert log.diff_ratio is not None
        assert log.diff_ratio > 0.10
        assert log.revised_text == revised

    @pytest.mark.asyncio
    async def test_edit_below_threshold_no_flywheel(self, service, mock_db):
        """edit + 微小修改 → 不触发飞轮，但仍入库"""
        original = "本项目采用综合评估法进行评标，技术标占比60%，投标价格占比40%" * 3
        revised = "本项目采用综合评估法进行评标，技术标占比65%，投标价格占比35%" * 3

        result = await service.ingest_feedback(
            db=mock_db,
            target_section="3.1 工程概况",
            section_id="3-1",
            original_ai_text=original,
            user_revised_text=revised,
            action="edit",
        )
        assert result is False
        log: FeedbackLog = mock_db.add.call_args[0][0]
        assert log.flywheel_triggered is False

    @pytest.mark.asyncio
    async def test_edit_short_text_no_flywheel(self, service, mock_db):
        """edit + 文本过短 → 不触发飞轮"""
        result = await service.ingest_feedback(
            db=mock_db,
            target_section="标题",
            section_id="header",
            original_ai_text="短文本",
            user_revised_text="改了",  # < MIN_TEXT_LENGTH
            action="edit",
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_tenant_id_always_bound(self, service, mock_db):
        """验证所有写入均强制绑定 tenant_id"""
        await service.ingest_feedback(
            db=mock_db,
            target_section="test",
            section_id="t1",
            original_ai_text="content",
            user_revised_text="content",
            action="accept",
        )
        log: FeedbackLog = mock_db.add.call_args[0][0]
        assert log.tenant_id == "test_tenant"


# ============================================================
# 3. get_stats 测试
# ============================================================


class TestGetStats:
    """统计查询测试"""

    @pytest.mark.asyncio
    async def test_empty_stats(self):
        """无数据时返回全零"""
        mock_db = AsyncMock()

        # Mock 分组查询结果为空
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_db.execute.return_value = mock_result

        # Mock 飞轮计数也为空
        mock_flywheel_result = MagicMock()
        mock_flywheel_result.scalar.return_value = 0
        mock_db.execute.side_effect = [mock_result, mock_flywheel_result]

        stats = await FeedbackFlywheelService.get_stats(db=mock_db, tenant_id="test")
        assert stats["total"] == 0
        assert stats["accept_count"] == 0
        assert stats["flywheel_sunk"] == 0

    @pytest.mark.asyncio
    async def test_stats_with_data(self):
        """有数据时正确计算占比"""
        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.all.return_value = [
            ("accept", 10),
            ("edit", 5),
            ("reject", 2),
        ]

        mock_flywheel_result = MagicMock()
        mock_flywheel_result.scalar.return_value = 3

        mock_db.execute.side_effect = [mock_result, mock_flywheel_result]

        stats = await FeedbackFlywheelService.get_stats(db=mock_db, tenant_id="test")
        assert stats["total"] == 17
        assert stats["accept_count"] == 10
        assert stats["edit_count"] == 5
        assert stats["reject_count"] == 2
        assert stats["flywheel_sunk"] == 3
        assert abs(stats["accept_rate"] - 0.588) < 0.01
