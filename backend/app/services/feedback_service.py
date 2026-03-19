"""
数据飞轮服务 — RLHF / SFT 反馈采集与知识库回灌

当用户对 AI 生成的标书内容进行实质性修改时，
系统将修改前后的对偶数据标记并回灌至 pgvector 知识库，
使后续生成能利用人工校验过的高质量语料，实现越用越聪明的自我进化闭环。
"""
import logging
import asyncio
from datetime import datetime
from typing import Optional

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
        target_section: str,
        original_ai_text: str,
        user_revised_text: str,
        action: str = "edit",
        trace_id: Optional[str] = None,
    ) -> bool:
        """
        核心记录槽 — 返回是否触发了飞轮数据下沉

        :param target_section: 修改的章节标题
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

        return flywheel_triggered

    @staticmethod
    def _calculate_diff_ratio(text_a: str, text_b: str) -> float:
        """
        计算两段文本的差异度

        使用字符级差异比率：编辑距离的近似计算（O(1) 复杂度）。
        生产环境可替换为 Levenshtein Distance 或 difflib.SequenceMatcher。
        """
        if text_a == text_b:
            return 0.0
        if not text_a:
            return 1.0

        len_a = len(text_a)
        len_b = len(text_b)

        # 基于长度变化 + 内容交集的混合度量
        length_diff = abs(len_a - len_b) / max(len_a, 1)

        # 基于字符集合交集的 Jaccard 近似
        set_a = set(text_a.split())
        set_b = set(text_b.split())
        if not set_a and not set_b:
            return length_diff

        jaccard = 1.0 - len(set_a & set_b) / max(len(set_a | set_b), 1)

        # 混合权重：70% Jaccard + 30% 长度差异
        return 0.7 * jaccard + 0.3 * length_diff

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
                    "revised_at": datetime.utcnow().isoformat(),
                },
            )

            logger.info(
                f"[数据飞轮] 人工修撰片段已成功下沉至知识库 | "
                f"section={section[:20]} | len={len(golden_text)}"
            )

        except Exception as e:
            logger.error(f"[数据飞轮] 下沉失败: {e}", exc_info=True)
