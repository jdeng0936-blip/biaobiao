"""
标书内容生成服务
RAG 检索知识库 → 行业词库注入 → 构建 Prompt → LLM Selector 动态路由 → 流式生成
"""
import logging
import json
import os
from pathlib import Path
from typing import Optional, AsyncGenerator

from app.llm.llm_selector import get_llm_selector
from app.llm.prompt_loader import get_prompt
from app.services.desensitize_service import DesensitizeGateway

logger = logging.getLogger("generate_service")

# 行业数据目录
_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class BidGenerateService:
    """标书内容生成核心服务 — 通过 LLMSelector 动态路由"""

    def __init__(self, tenant_id: str = "default"):
        self._selector = None
        self._desensitizer = None
        self._tenant_id = tenant_id

    @property
    def desensitizer(self):
        """懒加载脱敏网关"""
        if self._desensitizer is None:
            self._desensitizer = DesensitizeGateway(tenant_id=self._tenant_id)
        return self._desensitizer

    @property
    def selector(self):
        """懒加载 LLMSelector"""
        if self._selector is None:
            self._selector = get_llm_selector()
        return self._selector

    @property
    def ready(self) -> bool:
        """服务是否就绪（至少一个 Provider 可用）"""
        try:
            return self.selector is not None
        except Exception:
            return False

    # ============================================================
    # 行业词库加载（懒加载 + 缓存）
    # ============================================================
    _industry_cache: dict = None
    _insights_cache: list = None

    @classmethod
    def _load_industry_data(cls) -> dict:
        """加载行业词库配置（仅首次访问时读盘）"""
        if cls._industry_cache is None:
            fp = _DATA_DIR / "industry_keywords.json"
            if fp.exists():
                cls._industry_cache = json.loads(fp.read_text(encoding="utf-8"))
                logger.info(f"行业词库已加载: {len(cls._industry_cache)} 个行业")
            else:
                cls._industry_cache = {}
                logger.warning(f"行业词库文件不存在: {fp}")
        return cls._industry_cache

    @classmethod
    def _load_insights(cls) -> list:
        """加载高分标书评审洞察种子数据"""
        if cls._insights_cache is None:
            fp = _DATA_DIR / "seed_high_score_insights.json"
            if fp.exists():
                cls._insights_cache = json.loads(fp.read_text(encoding="utf-8"))
                logger.info(f"评审洞察已加载: {len(cls._insights_cache)} 条")
            else:
                cls._insights_cache = []
        return cls._insights_cache

    def get_industry_context(self, project_type: str) -> dict:
        """获取特定行业的完整上下文"""
        data = self._load_industry_data()
        return data.get(project_type, {})

    def build_system_prompt(self, project_type: str = "") -> str:
        """构建系统 Prompt — 标书专家角色 + 行业词库注入"""
        # 行业词库注入
        industry = self.get_industry_context(project_type)
        industry_section = ""
        if industry:
            keywords = "、".join(industry.get("core_keywords", [])[:10])
            standards = "\n".join(f"  - {s}" for s in industry.get("standards", [])[:3])
            industry_section = (
                f"\n\n## 本项目行业领域：{industry.get('label', project_type)}\n"
                f"### 你必须熟练运用的行业核心术语\n{keywords}\n"
                f"### 本项目适用的关键规范标准\n{standards}"
            )

        return get_prompt("bid_generate_system", industry_section=industry_section)

    @staticmethod
    def _parse_json(text: str) -> dict:
        try:
            import re
            cleaned = text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            match = re.search(r'\{.*\}', cleaned, re.S)
            if match:
                return json.loads(match.group())
            return json.loads(cleaned)
        except Exception:
            return {}

    async def _run_planner(self, section_title: str, project_context: str, user_requirements: str) -> dict:
        sys_prompt = get_prompt("planner")
        prompt = get_prompt(
            "planner_user",
            section_title=section_title,
            project_context=project_context,
            user_requirements=user_requirements,
        )
        try:
            res = await self.selector.generate("bid_generate", sys_prompt, prompt)
            return self._parse_json(res.text)
        except Exception as e:
            logger.warning(f"Planner 执行异常: {e}")
            return {"outline": "", "queries": []}

    async def _run_reviewer(self, draft: str, scoring_points: list[str]) -> dict:
        if not scoring_points:
            # 没提供打分表，直接让过
            return {"passed": True, "feedbacks": []}

        sys_prompt = get_prompt("reviewer")
        scoring_points_text = ""
        for i, p in enumerate(scoring_points, 1):
            scoring_points_text += f"{i}. {p}\n"
        prompt = get_prompt(
            "reviewer_user",
            scoring_points_text=scoring_points_text,
            draft_preview=draft[:1500],
        )
        try:
            res = await self.selector.generate("bid_generate", sys_prompt, prompt)
            return self._parse_json(res.text)
        except Exception as e:
            logger.warning(f"Reviewer 执行异常: {e}")
            return {"passed": True, "feedbacks": []}
            
    def build_rag_prompt(
        self,
        section_title: str,
        section_type: str,
        project_context: str,
        rag_chunks: list[dict],
        user_requirements: Optional[str] = None,
        scoring_points: list[str] = None,
        planner_outline: str = None,
        review_feedbacks: list[str] = None,
        project_type: str = "",
    ) -> str:
        """构建 RAG 增强的生成 Prompt — 融入行业词库 + 评审洞察 + 多节点状态信息"""
        knowledge_context = ""
        if rag_chunks:
            knowledge_context = "\n\n## 参考知识库（引用时请标注 [REF:编号]）\n"
            for i, chunk in enumerate(rag_chunks[:5], 1):
                source = chunk.get("source_file", "未知来源")
                similarity = chunk.get("similarity", 0)
                content = chunk.get("content", "")[:800]
                knowledge_context += f"\n### [REF:{i}]（来源: {source}，相似度 {similarity:.0%}）\n{content}\n"

        user_req_section = ""
        if user_requirements:
            user_req_section = f"\n\n## 用户额外要求\n{user_requirements}"
            
        planner_section = ""
        if planner_outline:
            planner_section = f"\n\n## (参考) 机器智能规划的大纲方向\n{planner_outline}"

        scoring_section = ""
        if scoring_points:
            scoring_section = "\n\n## 本章节对应的评分点（打分项：必须逐点覆盖）\n"
            for i, point in enumerate(scoring_points, 1):
                scoring_section += f"  {i}. {point}\n"

        review_section = ""
        if review_feedbacks:
            review_section = "\n\n## 【重大指令！】前一次生成被评标审查退回，原因如下（本次你必须重点修补以下缺陷）：\n"
            for i, fb in enumerate(review_feedbacks, 1):
                review_section += f" - 批评意见 {i}: {fb}\n"

        # 行业评审洞察注入
        industry_hints = ""
        industry = self.get_industry_context(project_type)
        if industry:
            focus_items = industry.get("scoring_focus", [])
            deduction_items = industry.get("common_deductions", [])
            if focus_items:
                focus_text = "\n".join(f"  - {f}" for f in focus_items[:4])
                industry_hints += f"\n\n## 行业评审关注点（必须在内容中体现）\n{focus_text}"
            if deduction_items:
                deduction_text = "\n".join(f"  - ⚠️ {d}" for d in deduction_items[:3])
                industry_hints += f"\n\n## 常见扣分陷阱（必须主动规避）\n{deduction_text}"

        # 高分标书评审洞察种子注入
        insights = self._load_insights()
        insight_section = ""
        if insights:
            # 根据章节类型匹配最相关的洞察
            type_map = {
                "technical": "施工组织设计",
                "quality": "质量管理",
                "safety": "安全文明施工",
                "schedule": "进度管理",
                "overview": "施工组织设计",
            }
            target_cat = type_map.get(section_type, "")
            matched = [i for i in insights if i.get("category") == target_cat]
            if matched:
                insight_section = f"\n\n## 专家得分策略（来源: {matched[0].get('source', '行业数据')}\uff09\n{matched[0]['insight']}"

        return get_prompt(
            "bid_generate_user",
            section_title=section_title,
            section_type=section_type,
            project_context=project_context,
            knowledge_context=knowledge_context,
            industry_hints=industry_hints,
            insight_section=insight_section,
            scoring_section=scoring_section,
            user_req_section=user_req_section,
            planner_section=planner_section,
            review_section=review_section,
        )


    async def generate_stream(
        self,
        section_title: str,
        section_type: str = "technical",
        project_context: str = "",
        project_type: str = "",
        rag_chunks: list[dict] = None,
        user_requirements: str = None,
        scoring_points: list[str] = None,
    ) -> AsyncGenerator[str, None]:
        """流式生成标书内容 — 七节点智能管线（企业级）

        Node 1: Planner     — 大纲规划
        Node 2: Retriever   — RAG 检索增强
        Node 3: Writer      — 初稿生成/重写
        Node 4: ComplianceGate — 合规审查（格式+内容+废标预警）
        Node 5: PolishPipeline — 多轮润色（术语→文风→逻辑→专业→亮点）
        Node 6: Reviewer    — 终审评分
        Node 7: Formatter   — 格式化输出
        """
        if not self.ready:
            yield "data: " + json.dumps({"error": "LLM 服务未就绪"}, ensure_ascii=False) + "\n\n"
            return
            
        import asyncio
        from app.services.compliance_service import ComplianceService, ComplianceContext
        from app.services.polish_service import PolishService, PolishContext

        state = {
            "iteration": 0,
            "max_iter": 3,          # 升级为 3 轮最大迭代
            "draft": "",
            "review_feedbacks": [],
            "compliance_feedbacks": [],
            "chunks": rag_chunks or [],
            "outline": "",
        }

        # 初始化合规审查和润色服务
        compliance_service = ComplianceService(tenant_id=self._tenant_id)
        polish_service = PolishService(tenant_id=self._tenant_id)

        try:
            # === Node 1: Planner（大纲规划）===
            yield "data: " + json.dumps({"type": "status", "text": "📝 [七节点管线 · 启动] Node 1/7: 专家构思文档结构规划..."}, ensure_ascii=False) + "\n\n"
            plan_res = await self._run_planner(section_title, project_context, str(user_requirements))
            state["outline"] = plan_res.get("outline", "")
            queries = plan_res.get("queries", [])
            
            # === Node 2: Retriever（RAG 检索增强）===
            if queries:
                yield "data: " + json.dumps({"type": "status", "text": f"🔍 [七节点管线] Node 2/7: 知识探针追检 {len(queries)} 项补充知识..."}, ensure_ascii=False) + "\n\n"
                from app.services.knowledge_service import KnowledgeService
                try:
                    ks = KnowledgeService(self._tenant_id)
                    for q in queries:
                        extra_struc = ks.search_structured(query_text=q, tenant_id=self._tenant_id, top_k=1)
                        state["chunks"].extend(extra_struc)
                except Exception as e:
                    logger.warning(f"Retriever 补充查询跳过: {e}")

            # === Loop: Writer → ComplianceGate → PolishPipeline → Reviewer ===
            while state["iteration"] < state["max_iter"]:
                iter_num = state["iteration"] + 1
                is_retry = state["iteration"] > 0

                # --- Node 3: Writer（生成/重写）---
                retry_text = f"（第 {iter_num} 轮修撰重试）" if is_retry else "初稿撰写"
                yield "data: " + json.dumps({"type": "status", "text": f"✍️ [七节点管线] Node 3/7: {retry_text}..."}, ensure_ascii=False) + "\n\n"
                
                # 合并合规反馈和审查反馈
                combined_feedbacks = state.get("compliance_feedbacks", []) + state.get("review_feedbacks", [])
                
                system_prompt = self.build_system_prompt(project_type=project_type)
                user_prompt = self.build_rag_prompt(
                    section_title=section_title,
                    section_type=section_type,
                    project_context=project_context,
                    rag_chunks=state["chunks"],
                    user_requirements=user_requirements,
                    scoring_points=scoring_points,
                    planner_outline=state["outline"],
                    review_feedbacks=combined_feedbacks if is_retry else None,
                    project_type=project_type,
                )
                
                masked_prompt, mapping = self.desensitizer.mask(user_prompt)
                writer_res = await self.selector.generate("bid_generate", system_prompt, masked_prompt)
                unmasked_draft = self.desensitizer.unmask(writer_res.text, mapping)
                state["draft"] = unmasked_draft

                # --- Node 4: ComplianceGate（合规审查）---
                yield "data: " + json.dumps({"type": "status", "text": f"🛡️ [七节点管线] Node 4/7: 三级合规审查（格式+内容+废标预警）..."}, ensure_ascii=False) + "\n\n"
                
                compliance_ctx = ComplianceContext(
                    project_type=project_type,
                    scoring_points=scoring_points or [],
                )
                compliance_result = await compliance_service.check(state["draft"], compliance_ctx)
                
                if compliance_result.has_critical and state["iteration"] < state["max_iter"] - 1:
                    # 存在致命合规问题 → 带反馈重写
                    state["compliance_feedbacks"] = compliance_result.to_feedback_list()
                    state["review_feedbacks"] = []
                    crit_count = len(compliance_result.critical_issues)
                    yield "data: " + json.dumps({
                        "type": "status", 
                        "text": f"🚨 [合规审查] 发现 {crit_count} 个致命问题，触发退档重写！"
                    }, ensure_ascii=False) + "\n\n"
                    state["iteration"] += 1
                    continue
                elif compliance_result.issues:
                    warn_count = len(compliance_result.warning_issues)
                    yield "data: " + json.dumps({
                        "type": "status",
                        "text": f"⚠️ [合规审查] 合规分 {compliance_result.score:.0f}/100 | {compliance_result.summary}"
                    }, ensure_ascii=False) + "\n\n"

                # --- Node 5: PolishPipeline（多轮润色 — 至少 3 轮）---
                yield "data: " + json.dumps({"type": "status", "text": "✨ [七节点管线] Node 5/7: 三轮递进式精修润色启动..."}, ensure_ascii=False) + "\n\n"

                polish_ctx = PolishContext(
                    project_type=project_type,
                    section_title=section_title,
                    section_type=section_type,
                    scoring_points=scoring_points or [],
                )

                async def polish_status_cb(msg: str):
                    """润色进度回调（非阻塞式记录）"""
                    pass  # 润色管道内部日志，主流式由外层管控

                try:
                    polish_result = await polish_service.polish_pipeline(
                        content=state["draft"],
                        context=polish_ctx,
                        min_rounds=3,
                        max_rounds=5,
                        status_callback=polish_status_cb,
                    )

                    if polish_result.final_content:
                        state["draft"] = polish_result.final_content
                        yield "data: " + json.dumps({
                            "type": "status",
                            "text": f"✅ [润色完成] {polish_result.summary}"
                        }, ensure_ascii=False) + "\n\n"
                    else:
                        yield "data: " + json.dumps({
                            "type": "status",
                            "text": "⚠️ [润色] 润色管道未产生有效输出，使用原稿"
                        }, ensure_ascii=False) + "\n\n"

                except Exception as e:
                    logger.warning(f"润色管道异常（降级使用原稿）: {e}")
                    yield "data: " + json.dumps({
                        "type": "status",
                        "text": f"⚠️ [润色] 降级跳过: {str(e)[:50]}"
                    }, ensure_ascii=False) + "\n\n"

                # --- Node 6: Reviewer（终审评分）---
                yield "data: " + json.dumps({"type": "status", "text": "⚖️ [七节点管线] Node 6/7: 评标专家终审质量巡检..."}, ensure_ascii=False) + "\n\n"
                review_out = await self._run_reviewer(state["draft"], scoring_points or [])
                passed = review_out.get("passed", True)
                
                if passed or state["iteration"] == state["max_iter"] - 1:
                    # Node 7: Formatter（格式化输出）
                    if passed:
                        yield "data: " + json.dumps({"type": "status", "text": "✅ [七节点管线] Node 7/7: 终审通过 ✓ 开始数据推流..."}, ensure_ascii=False) + "\n\n"
                    else:
                        yield "data: " + json.dumps({"type": "status", "text": f"⚠️ [七节点管线] Node 7/7: 第 {state['max_iter']} 轮已满，强制释出..."}, ensure_ascii=False) + "\n\n"

                    # 流式推送（打字机效果）
                    for i in range(0, len(state["draft"]), 6):
                        chunk = state["draft"][i:i+6]
                        yield "data: " + json.dumps({"type": "content", "text": chunk}, ensure_ascii=False) + "\n\n"
                        await asyncio.sleep(0.01)
                    break
                else:
                    # 被打回重造
                    feedbacks = review_out.get("feedbacks", ["未知格式或违规错误"])
                    state["review_feedbacks"] = feedbacks
                    state["compliance_feedbacks"] = []
                    fault_text = feedbacks[0] if feedbacks else "格式越界"
                    yield "data: " + json.dumps({
                        "type": "status", 
                        "text": f"❌ [终审退回] 专家意见[{fault_text[:20]}...] 触发第 {iter_num + 1} 轮修撰！"
                    }, ensure_ascii=False) + "\n\n"
                    state["iteration"] += 1

            yield "data: " + json.dumps({"type": "done"}, ensure_ascii=False) + "\n\n"

        except Exception as e:
            logger.error(f"七节点管线核心失败: {e}")
            yield "data: " + json.dumps({
                "type": "error",
                "message": str(e),
            }, ensure_ascii=False) + "\n\n"

    # ============================================================
    # Chat 对话专用（与标书生成分离）
    # ============================================================

    def build_chat_system_prompt(self) -> str:
        """Chat 对话专用 System Prompt — 标书咨询顾问角色"""
        return get_prompt("bid_chat_system")

    def build_chat_prompt(
        self,
        module_content: str,
        user_question: str,
        rag_chunks: list[dict] = None,
        project_context: str = "",
    ) -> str:
        """构建 Chat 对话的 User Prompt"""
        # RAG 参考（精简）
        rag_section = ""
        if rag_chunks:
            rag_texts = []
            for chunk in rag_chunks[:2]:
                content = chunk.get("content", "")[:200]
                rag_texts.append(content)
            if rag_texts:
                rag_section = "\n\n【相关参考】\n" + "\n".join(rag_texts)

        return get_prompt(
            "bid_chat_user",
            module_content=module_content[:500],
            user_question=user_question,
            project_context=project_context,
            rag_section=rag_section,
        )

    async def generate_chat_stream(
        self,
        module_content: str,
        user_question: str,
        project_context: str = "",
        rag_chunks: list[dict] = None,
    ) -> AsyncGenerator[str, None]:
        """Chat 对话流式生成 — 通过 LLMSelector 路由到 bid_chat 任务"""
        if not self.ready:
            yield "data: " + json.dumps({"error": "LLM 服务未就绪"}, ensure_ascii=False) + "\n\n"
            return

        system_prompt = self.build_chat_system_prompt()
        user_prompt = self.build_chat_prompt(
            module_content=module_content,
            user_question=user_question,
            rag_chunks=rag_chunks or [],
            project_context=project_context,
        )

        try:
            # 脱敏：发送 LLM 前 mask
            masked_prompt, mapping = self.desensitizer.mask(user_prompt)

            # 通过 LLMSelector 动态路由（task_type = bid_chat）
            full_text = ""
            async for text in self.selector.stream("bid_chat", system_prompt, masked_prompt):
                # 实时回填脱敏占位符
                unmasked_text = self.desensitizer.unmask(text, mapping)
                full_text += unmasked_text
                yield "data: " + json.dumps({
                    "type": "content",
                    "text": unmasked_text,
                }, ensure_ascii=False) + "\n\n"

            # 引申提问（task_type = suggestions）
            suggestions = []
            try:
                sug_prompt = get_prompt(
                    "suggestions",
                    user_question=user_question,
                    answer_summary=full_text[:300],
                )

                sug_response = await self.selector.generate("suggestions", "", sug_prompt)
                if sug_response.text:
                    sug_text = sug_response.text.strip()
                    if sug_text.startswith("```"):
                        sug_text = sug_text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
                    suggestions = json.loads(sug_text)
            except Exception as e:
                logger.warning(f"引申提问生成失败（不影响主回答）: {e}")

            yield "data: " + json.dumps({
                "type": "done",
                "suggestions": suggestions,
            }, ensure_ascii=False) + "\n\n"

        except Exception as e:
            logger.error(f"Chat 生成失败: {e}")
            yield "data: " + json.dumps({
                "type": "error",
                "message": str(e),
            }, ensure_ascii=False) + "\n\n"
