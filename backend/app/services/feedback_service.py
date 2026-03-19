"""
数据飞轮服务 — RLHF / SFT 反馈采集与知识库回灌

当用户对 AI 生成的标书内容进行实质性修改时，
系统将修改前后的对偶数据标记并回灌至 pgvector 知识库，
使后续生成能利用人工校验过的高质量语料，实现越用越聪明的自我进化闭环。
"""
import logging
import asyncio
import difflib
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.feedback_log import FeedbackLog

logger = logging.getLogger("feedback_service")


class FeedbackFlywheelService:
    """人类反馈强化学习 (RLHF) / 数据飞轮网关"""

    # 实质性修改阈值：修改超过 10% 才触发飞轮下沉
    DIFF_THRESHOLD = 0.10
    # 最小文本长度：过短的文本不值得作为训练语料
    MIN_TEXT_LENGTH = 50

    def __init__(self, tenant_id: str = "default"):
        self.tenant_id = tenant_id

    async def ingest_feedback(
        self,
        db: AsyncSession,
        target_section: str,
        section_id: str,
        original_ai_text: str,
        user_revised_text: str,
        action: str = "edit",
        trace_id: Optional[str] = None,
    ) -> bool:
        """
        核心记录槽 — 返回是否触发了飞轮数据下沉

        :param db: 异步数据库 session（从 FastAPI 依赖注入传入）
        :param target_section: 修改的章节标题
        :param section_id: 章节 ID
        :param original_ai_text: 大模型初稿
        :param user_revised_text: 招投标专家手动修改的高质量终稿
        :param action: accept / edit / reject
        :param trace_id: LangFuse 链路跟踪 ID
        :return: True 表示飞轮数据已下沉
        """
        logger.info(
            f"[数据飞轮] tenant={self.tenant_id} | action={action} | "
            f"section={target_section[:30]} | trace={trace_id}"
        )

        flywheel_triggered = False
        diff_ratio = None

        if action == "edit" and len(user_revised_text) > self.MIN_TEXT_LENGTH:
            diff_ratio = self._calculate_diff_ratio(original_ai_text, user_revised_text)

            if diff_ratio > self.DIFF_THRESHOLD:
                logger.info(
                    f"[数据飞轮] 检测到实质性修改 (diff={diff_ratio:.1%})，"
                    f"触发异步下沉到 pgvector 专属语料库"
                )
                asyncio.create_task(
                    self._async_sink_to_knowledge_base(
                        section=target_section,
                        golden_text=user_revised_text,
                        original_text=original_ai_text,
                        diff_ratio=diff_ratio,
                    )
                )
                flywheel_triggered = True
            else:
                logger.info(f"[数据飞轮] 修改幅度不足 (diff={diff_ratio:.1%})，跳过下沉")

        elif action == "accept":
            logger.info("[数据飞轮] 正向反馈 — 当前暂不触发下沉（后续可用于偏好排序）")

        elif action == "reject":
            logger.info("[数据飞轮] 负向反馈 — 记录供后续 DPO 对齐使用")

        # ========== 持久化到 feedback_logs 表 ==========
        feedback_log = FeedbackLog(
            section_id=section_id,
            section_title=target_section,
            action=action,
            original_text=original_ai_text,
            revised_text=user_revised_text if action == "edit" else None,
            diff_ratio=diff_ratio,
            flywheel_triggered=flywheel_triggered,
            trace_id=trace_id,
            tenant_id=self.tenant_id,
        )
        db.add(feedback_log)
        # 注意：commit 由 get_db() 上下文管理器统一处理

        return flywheel_triggered

    @staticmethod
    def _calculate_diff_ratio(text_a: str, text_b: str) -> float:
        """
        计算两段文本的差异度 — 使用 difflib.SequenceMatcher

        返回值范围 [0.0, 1.0]，0 表示完全相同，1 表示完全不同。
        """
        if text_a == text_b:
            return 0.0
        if not text_a:
            return 1.0

        # 使用 SequenceMatcher 的 ratio() 方法计算相似度
        # ratio() 返回 [0, 1] 的相似度，我们取 1 - ratio 得到差异度
        sm = difflib.SequenceMatcher(None, text_a, text_b)
        similarity = sm.ratio()
        return round(1.0 - similarity, 4)

    async def _async_sink_to_knowledge_base(
        self,
        section: str,
        golden_text: str,
        original_text: str,
        diff_ratio: float,
    ):
        """将人类校验过的优质语料下沉至底层知识库供后续生成参考"""
        try:
            from app.services.knowledge_service import KnowledgeService

            ks = KnowledgeService()

            # 将修订后的文本作为高质量训练片段插入 training_chunks
            ks.insert_feedback_chunk(
                content=golden_text,
                section=section,
                tenant_id=self.tenant_id,
                source_tag="human_revised",
                metadata={
                    "diff_ratio": round(diff_ratio, 4),
                    "original_length": len(original_text),
                    "revised_length": len(golden_text),
                    "revised_at": datetime.now(timezone.utc).isoformat(),
                },
            )

            logger.info(
                f"[数据飞轮] 人工修撰片段已成功下沉至知识库 | "
                f"section={section[:20]} | len={len(golden_text)}"
            )

        except Exception as e:
            logger.error(f"[数据飞轮] 下沉失败: {e}", exc_info=True)

    # ============================================================
    # 统计查询（供 Dashboard 飞轮面板使用）
    # ============================================================

    @staticmethod
    async def get_stats(db: AsyncSession, tenant_id: str = "default") -> dict:
        """
        获取反馈统计数据 — 供 Dashboard 数据飞轮面板渲染

        返回格式：
        {
            "total": 42,
            "accept_count": 20,
            "edit_count": 15,
            "reject_count": 7,
            "accept_rate": 0.476,
            "edit_rate": 0.357,
            "reject_rate": 0.167,
            "flywheel_sunk": 8
        }
        """
        # 按 action 分组统计
        stmt = (
            select(
                FeedbackLog.action,
                func.count().label("cnt"),
            )
            .where(FeedbackLog.tenant_id == tenant_id)
            .group_by(FeedbackLog.action)
        )
        result = await db.execute(stmt)
        rows = result.all()

        counts = {"accept": 0, "edit": 0, "reject": 0}
        for action, cnt in rows:
            if action in counts:
                counts[action] = cnt

        total = sum(counts.values())

        # 飞轮下沉数量
        flywheel_stmt = (
            select(func.count())
            .select_from(FeedbackLog)
            .where(
                FeedbackLog.tenant_id == tenant_id,
                FeedbackLog.flywheel_triggered.is_(True),
            )
        )
        flywheel_result = await db.execute(flywheel_stmt)
        flywheel_sunk = flywheel_result.scalar() or 0

        return {
            "total": total,
            "accept_count": counts["accept"],
            "edit_count": counts["edit"],
            "reject_count": counts["reject"],
            "accept_rate": round(counts["accept"] / total, 3) if total else 0,
            "edit_rate": round(counts["edit"] / total, 3) if total else 0,
            "reject_rate": round(counts["reject"] / total, 3) if total else 0,
            "flywheel_sunk": flywheel_sunk,
        }
