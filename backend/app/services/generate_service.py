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

    def build_rag_prompt(
        self,
        section_title: str,
        section_type: str,
        project_context: str,
        rag_chunks: list[dict],
        user_requirements: Optional[str] = None,
        scoring_points: list[str] = None,
    ) -> str:
        """构建 RAG 增强的生成 Prompt — 含溯源编号"""
        # 知识库上下文（每个 chunk 带唯一编号，供 LLM 引用）
        knowledge_context = ""
        if rag_chunks:
            knowledge_context = "\n\n## 参考知识库（引用时请标注 [REF:编号]）\n"
            for i, chunk in enumerate(rag_chunks[:5], 1):
                source = chunk.get("source_file", "未知来源")
                density = chunk.get("data_density", "")
                similarity = chunk.get("similarity", 0)
                content = chunk.get("content", "")[:800]
                knowledge_context += f"\n### [REF:{i}]（来源: {source}，相似度 {similarity:.0%}，密度: {density}）\n{content}\n"

        # 用户额外要求
        user_req_section = ""
        if user_requirements:
            user_req_section = f"\n\n## 用户额外要求\n{user_requirements}"

        # 评分点驱动（借鉴点 #3）
        scoring_section = ""
        if scoring_points:
            scoring_section = "\n\n## 本章节对应的评分点（必须逐点覆盖）\n"
            for i, point in enumerate(scoring_points, 1):
                scoring_section += f"  {i}. {point}\n"
            scoring_section += "\n⚠️ 以上评分点是评审专家的打分依据，每个点都必须在正文中有明确的响应段落。"

        return f"""## 任务
为以下标书章节生成专业、完整的内容。

## 章节信息
- 章节标题: {section_title}
- 内容类型: {section_type}
- 项目背景: {project_context}
{knowledge_context}{scoring_section}{user_req_section}

## 格式要求（必须严格遵守）
1. 绝对禁止使用任何 Markdown 语法（#、*、**、```、-、> 等全部禁止）
2. 章节标题用中文编号：一、二、三、（一）（二）、1. 2. 3.
3. 每个段落开头空两格
4. 列举内容用（1）（2）（3）或 ① ② ③
5. 整体格式必须像正式打印的投标文件

## 溯源标注要求（极其重要）
当你引用或参考了上方某个知识库片段的内容时，在该段落末尾标注 [REF:编号]。
例如：本项目采用分层碾压工艺，每层厚度不超过 30cm。[REF:2]

## 内容要求
1. 充分参考上方知识库片段中的专业表达、具体参数和技术细节
2. 不要照搬原文，要结合当前项目特点重新组织和优化
3. 确保生成内容覆盖该章节应有的全部要点
4. 如有评分点，必须逐点覆盖，确保每个评分点在正文中都有对应内容
5. 文字量适中，确保内容详实但不注水（约 800-2000 字）

现在请直接输出该章节的标书正文内容："""

    async def generate_stream(
        self,
        section_title: str,
        section_type: str = "technical",
        project_context: str = "",
        rag_chunks: list[dict] = None,
        user_requirements: str = None,
    ) -> AsyncGenerator[str, None]:
        """流式生成标书内容 — 通过 LLMSelector 路由到 bid_generate 任务"""
        if not self.ready:
            yield "data: " + json.dumps({"error": "LLM 服务未就绪"}, ensure_ascii=False) + "\n\n"
            return

        system_prompt = self.build_system_prompt()
        user_prompt = self.build_rag_prompt(
            section_title=section_title,
            section_type=section_type,
            project_context=project_context,
            rag_chunks=rag_chunks or [],
            user_requirements=user_requirements,
        )

        try:
            # 脱敏：发送 LLM 前 mask
            masked_prompt, mapping = self.desensitizer.mask(user_prompt)
            masked_system = system_prompt  # system prompt 无敏感信息

            # 收集完整输出用于 unmask
            full_output = ""

            # 通过 LLMSelector 动态路由（task_type = bid_generate）
            async for text in self.selector.stream("bid_generate", masked_system, masked_prompt):
                # 实时回填脱敏占位符
                unmasked_text = self.desensitizer.unmask(text, mapping)
                full_output += unmasked_text
                yield "data: " + json.dumps({
                    "type": "content",
                    "text": unmasked_text,
                }, ensure_ascii=False) + "\n\n"

            yield "data: " + json.dumps({"type": "done"}, ensure_ascii=False) + "\n\n"

        except Exception as e:
            logger.error(f"生成失败: {e}")
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
