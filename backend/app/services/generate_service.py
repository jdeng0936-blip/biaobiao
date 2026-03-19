"""
标书内容生成服务
RAG 检索知识库 → 构建 Prompt → LLM Selector 动态路由 → 流式生成
"""
import logging
import json
from typing import Optional, AsyncGenerator

from app.llm.llm_selector import get_llm_selector
from app.services.desensitize_service import DesensitizeGateway

logger = logging.getLogger("generate_service")


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

    def build_system_prompt(self) -> str:
        """构建系统 Prompt — 标书专家角色"""
        return """你是一位资深的标书编写专家，拥有 15 年中国市政/房建工程招投标经验。

## 核心能力
- 精通施工组织设计、技术方案、质量管理、安全文明施工等全部标书模块
- 熟悉最新国标、行标和地方标准
- 擅长将技术细节转化为评审加分亮点

## 写作规范
1. 使用专业工程术语，确保符合行业规范
2. 内容必须具体、量化（如"每 50m 设一处"），拒绝空话套话
3. 引用规范时注明规范编号（如 GB50300-2013）
4. 针对不同工程类型自动适配专业表达
5. 文段之间保持逻辑递进关系
6. 适当使用分项、分点，便于评审阅读

## 输出格式（极其重要，必须严格遵守）
- 直接输出标书正文
- 绝对禁止使用 Markdown 语法：不允许出现 #、##、###、*、**、```、> 等任何Markdown标记
- 章节标题使用中文编号格式，例如："一、""二、""（一）""（二）""1.""2.""（1）""（2）"
- 段落之间用空行分隔
- 段落开头空两格（缩进两个汉字）
- 列举项目使用中文序号：（1）（2）（3）或 ① ② ③
- 重要数据直接写入正文，不要加任何装饰符号
- 整体风格必须像正式打印的标书文档，而非网络文章"""

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
        sys_prompt = "你是一个高级标书规划规划师。必须且只能输出合法的 JSON 对象。格式限制：{\"outline\": \"大纲建议文字\", \"queries\": [\"如果需要补充知识库可以填入一些工程短语作为搜素关键词\"]}"
        prompt = f"针对即将编写的【{section_title}】章节制定计划纲要。\n项目背景：{project_context}\n特殊要求：{user_requirements}\n请规划内容大纲并提取可能需要额外查阅的知识点（不超过2个关键词）。"
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
            
        sys_prompt = "你是一个铁面无私的评标专家考官。必须且只能输出纯 JSON 对象。格式边界：{\"passed\": true或false, \"feedbacks\": [\"如果不通过，列出缺失漏写的评分点批评或Markdown滥用问题\"]}"
        punkte = ""
        for i, p in enumerate(scoring_points, 1):
            punkte += f"{i}. {p}\n"
        prompt = f"【本章节需要遵守的评标专家打分硬指标】：\n{punkte}\n\n【被审核初稿（部分）】：\n{draft[:1500]}\n\n请审核初稿是否精确且全面地覆盖了所有评分点并且没有使用Markdown。如果缺少任何一项则判定为未通过(passed:false)。"
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
    ) -> str:
        """构建 RAG 增强的生成 Prompt — 融入多节点状态信息"""
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

        return f"""## 任务
为你提供以下标书的资料，写出专业、完整的标书内容。

## 章节与环境信息
- 章节标题: {section_title}
- 内容类型: {section_type}
- 项目要求背景: {project_context}
{knowledge_context}{scoring_section}{user_req_section}{planner_section}{review_section}

## 格式基座纪律要求（严禁逾越）：
1. 绝对禁止使用任何 Markdown 语法（#、*、**、```、-、> 等全部禁止），保持公文平滑感。
2. 章节标题用中文编号：一、二、三、（一）（二）、1. 2. 3.
3. 每个段落首行不空两格（让前端或后期docx工具去做），但段间可以适度留空行。
4. 如需溯源标注（引用知识库时），在段落末尾附加上 [REF:x]。

请综合以上约束与要求，给出可以直接被拷贝作为最终标书文件的纯文本内容："""


    async def generate_stream(
        self,
        section_title: str,
        section_type: str = "technical",
        project_context: str = "",
        rag_chunks: list[dict] = None,
        user_requirements: str = None,
        scoring_points: list[str] = None,
    ) -> AsyncGenerator[str, None]:
        """流式生成标书内容 — 完全由微型状态机重构 (Agent Flow)"""
        if not self.ready:
            yield "data: " + json.dumps({"error": "LLM 服务未就绪"}, ensure_ascii=False) + "\n\n"
            return
            
        import asyncio
        state = {
            "iteration": 0,
            "max_iter": 2,
            "draft": "",
            "review_feedbacks": [],
            "chunks": rag_chunks or [],
            "outline": ""
        }

        try:
            # === Node 1: Planner ===
            yield "data: " + json.dumps({"type": "status", "text": "📝 [多智能体管线 启动] - 节点 1: 专家开始构思文档结构规划..."}, ensure_ascii=False) + "\n\n"
            plan_res = await self._run_planner(section_title, project_context, str(user_requirements))
            state["outline"] = plan_res.get("outline", "")
            queries = plan_res.get("queries", [])
            
            # === Node 2: Retriever ===
            if queries:
                yield "data: " + json.dumps({"type": "status", "text": f"🔍 [多智能体管线 追加] - 节点 2: 发现认知盲区，底层探针主动追检 {len(queries)} 项额外短语..."}, ensure_ascii=False) + "\n\n"
                from app.services.knowledge_service import KnowledgeService
                try:
                    ks = KnowledgeService(self._tenant_id)
                    for q in queries:
                        extra = ks.search_semantic(query_embedding=[0]*768, top_k=1, tenant_id=self._tenant_id) # 这里使用兜底零向量因为没有直接可提取的纯文本倒排索引,或者假设项目包含更底层查询。作为Demo使用防崩
                        # 妥协版：调用 search_structured
                        extra_struc = ks.search_structured(query_text=q, tenant_id=self._tenant_id, top_k=1)
                        state["chunks"].extend(extra_struc)
                except Exception as e:
                    logger.warning(f"Retriever 补充查询跳过: {e}")

            # === Loop Node: Writer -> Reviewer ===
            while state["iteration"] < state["max_iter"]:
                iter_text = f" （第 {state['iteration'] + 1} 次深度修撰重试）" if state["iteration"] > 0 else " 执笔者撰稿"
                yield "data: " + json.dumps({"type": "status", "text": f"✍️ [多智能体管线 输出] - 节点 3:{iter_text} 开始撰写..."}, ensure_ascii=False) + "\n\n"
                
                # 构造包含状态机的动态强化 Prompt
                system_prompt = self.build_system_prompt()
                user_prompt = self.build_rag_prompt(
                    section_title=section_title,
                    section_type=section_type,
                    project_context=project_context,
                    rag_chunks=state["chunks"],
                    user_requirements=user_requirements,
                    scoring_points=scoring_points,
                    planner_outline=state["outline"],
                    review_feedbacks=state["review_feedbacks"] if state["iteration"] > 0 else None,
                )
                
                masked_prompt, mapping = self.desensitizer.mask(user_prompt)
                
                # 开始写稿，一次性生成完毕存放内存
                writer_res = await self.selector.generate("bid_generate", system_prompt, masked_prompt)
                unmasked_draft = self.desensitizer.unmask(writer_res.text, mapping)
                state["draft"] = unmasked_draft
                
                # --- Node 4: Reviewer ---
                yield "data: " + json.dumps({"type": "status", "text": f"⚖️ [多智能体管线 审查] - 节点 4: 评标机器人对初步文本进行苛刻质量巡视..."}, ensure_ascii=False) + "\n\n"
                review_out = await self._run_reviewer(state["draft"], scoring_points or [])
                passed = review_out.get("passed", True)
                
                if passed or state["iteration"] == state["max_iter"] - 1:
                    if passed:
                        yield "data: " + json.dumps({"type": "status", "text": "✅ 终核审查通过，开始数据推流至客户端。"}, ensure_ascii=False) + "\n\n"
                    else:
                        yield "data: " + json.dumps({"type": "status", "text": "⚠️ 制式循环拉满，将强制向客户端进行释出。"}, ensure_ascii=False) + "\n\n"
                    # 这里为了模拟打字机流式，把全量数据分割给前端
                    for i in range(0, len(state["draft"]), 6):
                        chunk = state["draft"][i:i+6]
                        yield "data: " + json.dumps({"type": "content", "text": chunk}, ensure_ascii=False) + "\n\n"
                        await asyncio.sleep(0.01)
                    break
                else:
                    # 被打回重造
                    feedbacks = review_out.get("feedbacks", ["未知格式或违规错误"])
                    state["review_feedbacks"] = feedbacks
                    fault_text = feedbacks[0] if feedbacks else "格式越界"
                    yield "data: " + json.dumps({"type": "status", "text": f"❌ 核查失败！专家意见[{fault_text[:15]}...] 正在请求指令打回退档重写！"}, ensure_ascii=False) + "\n\n"
                    state["iteration"] += 1

            yield "data: " + json.dumps({"type": "done"}, ensure_ascii=False) + "\n\n"

        except Exception as e:
            logger.error(f"多智能体生成核心失败: {e}")
            yield "data: " + json.dumps({
                "type": "error",
                "message": str(e),
            }, ensure_ascii=False) + "\n\n"

    # ============================================================
    # Chat 对话专用（与标书生成分离）
    # ============================================================

    def build_chat_system_prompt(self) -> str:
        """Chat 对话专用 System Prompt — 标书咨询顾问角色"""
        return """你是一位专业的标书咨询顾问，负责回答用户关于标书内容的具体问题。

## 核心原则
1. **精准回答**：只针对用户提出的具体问题回答，绝不复述或重新生成标书内容
2. **简洁有力**：回答控制在 100-300 字以内，直击要点
3. **专业判断**：如果问题涉及规范标准，直接给出是否合规的判断和依据
4. **可操作建议**：给出具体的改进建议而非笼统的描述

## 回答格式
- 直接回答问题，不要以"好的"、"您好"等开头
- 如有多个要点，用简短的编号列出
- 如涉及规范引用，注明规范名称和编号
- 回答末尾不要加总结性废话

## 特别注意
- 绝对不要重新生成或复述引用内容的原文
- 不要展开回答用户没有问到的内容
- 如果问题不够明确，直接给出最可能的解读并回答"""

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

        return f"""【引用内容】
{module_content[:500]}

【用户问题】
{user_question}

【项目背景】
{project_context}
{rag_section}

请直接回答用户的问题。只基于上方引用内容来作答，不要生成新的标书章节内容。"""

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
                sug_prompt = f"""基于以下对话，生成 2-3 个与当前问题紧密相关的后续提问建议。

用户问题：{user_question}
AI 回答摘要：{full_text[:300]}

要求：只输出一个 JSON 数组，格式为 ["问题1", "问题2", "问题3"]，不要输出其他任何内容。"""

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
