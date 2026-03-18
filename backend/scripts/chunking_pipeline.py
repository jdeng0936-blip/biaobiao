#!/usr/bin/env python3
"""
标标 AI · 标书知识库切片入库流水线
=======================================
PDF → 文本提取 → 章节切片 → NER 脱敏 → 分类标签 → Embedding 向量化 → pgvector 入库

使用方式：
  # 处理单个文件，输出 JSON（不入库）
  python chunking_pipeline.py --input /path/to/标书.pdf --output chunks.json

  # 用 Gemini 向量化（推荐，从 .env 读取 GEMINI_API_KEY）
  python chunking_pipeline.py --input /path/to/训练资料/ -o chunks.json --vectorize --engine gemini

  # 用本地模型向量化（零费用，首次需下载 90MB 模型）
  python chunking_pipeline.py --input /path/to/训练资料/ -o chunks.json --vectorize --engine local

  # 用 OpenAI 向量化
  python chunking_pipeline.py --input /path/to/训练资料/ -o chunks.json --vectorize --engine openai

  # 向量化 + 入库 pgvector
  python chunking_pipeline.py --input /path/to/训练资料/ --vectorize --engine gemini --db-url postgresql://user:pass@localhost:5432/biaobiao

依赖安装：
  pip install PyPDF2 PyMuPDF python-dotenv
  # Gemini 引擎:  pip install google-genai
  # OpenAI 引擎:  pip install openai
  # 本地引擎:     pip install sentence-transformers
  # 入库:         pip install psycopg2-binary pgvector
"""

import argparse
import hashlib
import json
import logging
import os
import re
import sys
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

# ============================================================
# 自动加载 .env 文件
# ============================================================
try:
    from dotenv import load_dotenv
    # 从脚本所在目录的上级（backend/）加载 .env
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass  # 没装 python-dotenv 也不影响，可手动设环境变量

# ============================================================
# 日志配置
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("chunking_pipeline")


# ============================================================
# 数据结构
# ============================================================
@dataclass
class Chunk:
    """一个知识片段"""
    id: str                          # UUID
    content: str                     # 脱敏后文本
    content_hash: str                # 内容哈希（用于去重）

    # 来源追溯
    source_file: str                 # 脱敏后文件名
    original_file: str               # 原始文件名（仅内部调试用）
    page_start: int                  # 起始页码
    page_end: int                    # 结束页码
    chapter: str                     # 章标题
    section: str                     # 节标题

    # 分类标签
    project_type: list               # ['房建', '新建']
    doc_section: str                 # 'technical' / 'quality' / 'safety' ...
    craft_tags: list                 # ['混凝土', '裂缝防治']

    # 质量元数据
    char_count: int                  # 字符数
    has_params: bool                 # 是否含具体参数
    data_density: str                # 'high' / 'medium' / 'low'

    # 向量（可选，向量化后填充）
    embedding: Optional[list] = None

    # 时间
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


# ============================================================
# Step 1: PDF 文本提取
# ============================================================
class PDFExtractor:
    """从 PDF 中提取文本，按页返回。支持 PyPDF2 + PyMuPDF 双引擎回退"""

    def extract(self, pdf_path: str) -> list[dict]:
        """
        返回: [{ 'page': 1, 'text': '...' }, ...]
        优先使用 PyPDF2，失败时自动回退到 PyMuPDF (fitz)
        """
        # 先尝试 PyPDF2
        pages = self._extract_with_pypdf2(pdf_path)

        # PyPDF2 失败，回退到 PyMuPDF
        if not pages:
            logger.info("  🔄 PyPDF2 提取失败，尝试 PyMuPDF...")
            pages = self._extract_with_pymupdf(pdf_path)

        return pages

    def _extract_with_pypdf2(self, pdf_path: str) -> list[dict]:
        """使用 PyPDF2 提取"""
        try:
            import PyPDF2
        except ImportError:
            logger.warning("  ⚠️ PyPDF2 未安装，跳过")
            return []

        pages = []
        try:
            with open(pdf_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                total = len(reader.pages)
                logger.info(f"  📄 [PyPDF2] {os.path.basename(pdf_path)}: {total} 页")

                for i, page in enumerate(reader.pages):
                    text = page.extract_text() or ""
                    text = self._clean_text(text)
                    if text.strip():
                        pages.append({"page": i + 1, "text": text})

            logger.info(f"  ✅ 提取 {len(pages)}/{total} 页有效内容")
        except Exception as e:
            logger.warning(f"  ⚠️ PyPDF2 无法解析: {e}")
            return []

        return pages

    def _extract_with_pymupdf(self, pdf_path: str) -> list[dict]:
        """使用 PyMuPDF (fitz) 提取——兼容性更强"""
        try:
            import fitz  # PyMuPDF
        except ImportError:
            logger.error("  ❌ PyMuPDF 也未安装，请执行: pip install PyMuPDF")
            return []

        pages = []
        try:
            doc = fitz.open(pdf_path)
            total = doc.page_count
            logger.info(f"  📄 [PyMuPDF] {os.path.basename(pdf_path)}: {total} 页")

            for i in range(total):
                page = doc[i]
                text = page.get_text() or ""
                text = self._clean_text(text)
                if text.strip():
                    pages.append({"page": i + 1, "text": text})

            doc.close()
            logger.info(f"  ✅ 提取 {len(pages)}/{total} 页有效内容")
        except Exception as e:
            logger.error(f"  ❌ PyMuPDF 提取也失败: {e}")
            return []

        return pages

    def _clean_text(self, text: str) -> str:
        """清理每页文本"""
        # 移除页码行 如 "第 X 页/共 X 页"
        text = re.sub(r"第\s*\d+\s*页\s*/\s*共\s*\d+\s*页", "", text)
        # 移除多余空行
        text = re.sub(r"\n{3,}", "\n\n", text)
        # 移除行首空格（保留缩进）
        lines = []
        for line in text.split("\n"):
            stripped = line.strip()
            if stripped:
                lines.append(stripped)
        return "\n".join(lines)


# ============================================================
# Step 2: 章节识别与切片
# ============================================================
class ChapterChunker:
    """按章节结构进行语义切片"""

    # 章节标题正则
    CHAPTER_PATTERNS = [
        # 第X章
        r"^第[一二三四五六七八九十\d]+章\s*.+",
        # 第X节
        r"^第[一二三四五六七八九十\d]+节\s*.+",
        # X.X.X 数字编号
        r"^\d+\.\d+(?:\.\d+)?\s+.+",
        # X、标题 / (X)标题
        r"^[一二三四五六七八九十]+[、．]\s*.+",
        r"^（[一二三四五六七八九十]+）\s*.+",
        r"^\([一二三四五六七八九十]+\)\s*.+",
    ]

    def __init__(self, max_chunk_size: int = 800, min_chunk_size: int = 100):
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size

    def chunk(self, pages: list[dict]) -> list[dict]:
        """
        将页面列表切分为语义块

        返回: [{ 'text': '...', 'chapter': '第二章...', 'section': '§17...', 
                 'page_start': 5, 'page_end': 7 }, ...]
        """
        # 先合并所有页面文本，并记录每段文字对应的页码
        segments = []
        for page_info in pages:
            page_num = page_info["page"]
            text = page_info["text"]
            for para in text.split("\n\n"):
                para = para.strip()
                if para:
                    segments.append({"text": para, "page": page_num})

        # 识别章节结构
        chunks = []
        current_chapter = "未分类"
        current_section = ""
        current_text = ""
        current_page_start = 1
        current_page_end = 1

        for seg in segments:
            line = seg["text"]
            page = seg["page"]

            # 检查是否是章节标题
            is_chapter = False
            is_section = False

            if re.match(self.CHAPTER_PATTERNS[0], line):
                is_chapter = True
            elif re.match(self.CHAPTER_PATTERNS[1], line):
                is_section = True
            elif re.match(self.CHAPTER_PATTERNS[2], line) and len(line) < 60:
                is_section = True

            # 遇到新章节或当前块过大，则切割
            if (is_chapter or is_section) and current_text.strip():
                if len(current_text) >= self.min_chunk_size:
                    chunks.append({
                        "text": current_text.strip(),
                        "chapter": current_chapter,
                        "section": current_section,
                        "page_start": current_page_start,
                        "page_end": current_page_end,
                    })
                current_text = ""
                current_page_start = page

            # 更新章节标题
            if is_chapter:
                current_chapter = line[:50]  # 截断过长标题
                current_section = ""
            elif is_section:
                current_section = line[:50]

            # 累积文本
            current_text += line + "\n"
            current_page_end = page

            # 如果当前块已超过最大尺寸，强制切割
            if len(current_text) > self.max_chunk_size:
                chunks.append({
                    "text": current_text.strip(),
                    "chapter": current_chapter,
                    "section": current_section,
                    "page_start": current_page_start,
                    "page_end": current_page_end,
                })
                current_text = ""
                current_page_start = page

        # 收尾
        if current_text.strip() and len(current_text) >= self.min_chunk_size:
            chunks.append({
                "text": current_text.strip(),
                "chapter": current_chapter,
                "section": current_section,
                "page_start": current_page_start,
                "page_end": current_page_end,
            })

        logger.info(f"  🔪 切片完成: {len(chunks)} 个知识片段")
        return chunks


# ============================================================
# Step 3: NER 脱敏处理
# ============================================================
class Desensitizer:
    """对敏感信息进行脱敏替换"""

    # 脱敏规则（正则 → 替换文本）
    RULES = [
        # 企业名称（常见建筑企业名模式）
        (r"(?:安徽|中建|中国|中铁|中交|中核|中冶|北京|上海|广东|江苏|浙江|湖北|四川|山东|河南)"
         r"[\u4e00-\u9fa5]{2,15}(?:集团|建设|建筑|工程|科工|科技|装饰|市政)"
         r"[\u4e00-\u9fa5]{0,10}(?:有限公司|股份公司|有限责任公司)",
         "[投标企业]"),

        # 建设单位
        (r"(?:安徽|合肥|北京|上海|广州|深圳)[\u4e00-\u9fa5]{2,20}"
         r"(?:有限责任公司|有限公司|学院|学校|局|中心|集团)",
         "[建设单位]"),

        # 项目编号
        (r"\d{4}[A-Z]{2,}[A-Z\d]{4,10}(?:/[A-Z\d-]+)?", "[项目编号]"),

        # 金额
        (r"\d+(?:\.\d+)?(?:万元|元|亿元)", "[金额]"),

        # 手机号
        (r"1[3-9]\d{9}", "[联系电话]"),

        # 身份证号
        (r"\d{17}[\dXx]", "[身份证号]"),

        # 具体地址中的门牌号
        (r"(?:芙蓉路|天津路|繁华大道|沈阳路|望江西路|长江西路|花园大道)"
         r"(?:\d+号)?", "[项目地址]"),

        # 日期年份脱敏（保留月日，脱敏年份）
        # 注意：不脱敏规范标准中的年份
        (r"(202[0-9])年(\d{1,2}月)", r"[年份]\2"),
    ]

    def desensitize(self, text: str) -> str:
        """对文本执行所有脱敏规则"""
        result = text
        for pattern, replacement in self.RULES:
            result = re.sub(pattern, replacement, result)
        return result

    def desensitize_filename(self, filename: str) -> str:
        """对文件名脱敏"""
        # 移除企业名
        result = re.sub(
            r"(?:中建科工|安徽圆明基|安徽敬泽|[\u4e00-\u9fa5]+公司)-?",
            "",
            filename,
        )
        # 移除项目编号
        result = re.sub(r"\d{4}[A-Z]+\d+", "", result)
        return result.strip("- _") or "标书"


# ============================================================
# Step 4: 自动分类与标签
# ============================================================
class AutoTagger:
    """基于关键词规则自动打标签"""

    # 工程类型识别规则
    PROJECT_TYPE_RULES = {
        "房建-新建": ["联合工房", "主体结构", "框架", "筏板", "桩基", "地上", "地下室"],
        "房建-维修改造": ["维修改造", "翻新", "改造工程", "维修工程"],
        "房建-装修": ["装修", "装饰", "吊顶", "墙面", "地面", "食堂"],
        "市政-道路": ["道路", "路基", "沥青", "摊铺", "侧石", "人行道"],
        "市政-管网": ["管道", "排水", "给水", "雨污", "检查井"],
        "市政-桥梁": ["桥梁", "箱涵", "挡墙", "围堰"],
        "物流仓储": ["物流", "仓储", "分拣", "自动化", "货架"],
    }

    # 文档段落类型识别
    DOC_SECTION_RULES = {
        "overview": ["工程概况", "编制说明", "项目概述", "总体筹划"],
        "technical": ["施工方案", "施工工艺", "施工方法", "技术措施"],
        "quality": ["质量", "通病", "防治", "验收", "检测", "样板"],
        "safety": ["安全", "危大", "应急", "消防", "防护"],
        "schedule": ["进度", "工期", "里程碑", "滞后", "纠偏"],
        "resource": ["物资", "机械", "劳动力", "材料", "设备"],
        "difficulty": ["重难点", "难点分析", "对策", "攻坚"],
        "innovation": ["新技术", "新工艺", "BIM", "智能", "信息化"],
        "design": ["设计方案", "设计思路", "改造设计", "设计原则"],
        "civilization": ["文明施工", "环保", "绿色", "扬尘", "噪音"],
    }

    # 施工工艺标签
    CRAFT_TAG_RULES = {
        "土方开挖": ["土方", "开挖", "基坑", "清表"],
        "基坑支护": ["支护", "围护", "土钉", "降水"],
        "混凝土": ["混凝土", "浇筑", "振捣", "养护", "配合比"],
        "钢筋工程": ["钢筋", "直螺纹", "绑扎", "套筒"],
        "模板工程": ["模板", "支模", "盘扣", "脚手架"],
        "钢结构": ["钢结构", "网架", "焊接", "吊装", "高强螺栓"],
        "防水工程": ["防水", "卷材", "涂膜", "蓄水试验"],
        "屋面工程": ["屋面", "铝镁锰", "保温层", "找坡"],
        "装修工程": ["装修", "装饰", "抹灰", "腻子", "涂料", "乳胶漆"],
        "吊顶工程": ["吊顶", "龙骨", "铝扣板", "石膏板"],
        "墙地砖": ["墙砖", "地砖", "铺贴", "瓷砖"],
        "机电安装": ["给水", "排水", "配电", "穿线", "桥架"],
        "消防": ["消防", "喷淋", "消火栓", "灭火"],
        "智能化": ["智能化", "弱电", "监控", "门禁"],
        "沥青摊铺": ["沥青", "摊铺", "碾压", "面层"],
        "路基处理": ["路基", "压实", "灰土", "回弹模量"],
        "水稳基层": ["水泥稳定", "水稳", "碎石基层"],
        "管道铺设": ["管道", "管线", "铺设", "接口"],
        "检查井": ["检查井", "雨水口", "井盖"],
        "围墙围挡": ["围墙", "围挡", "大门"],
        "绿化景观": ["绿化", "景观", "种植", "草坪"],
        "测量控制": ["测量", "放线", "全站仪", "沉降观测"],
        "BIM技术": ["BIM", "三维", "碰撞检查", "深化设计"],
        "成品保护": ["成品保护", "覆盖", "防护"],
    }

    def tag(self, text: str, chapter: str = "", section: str = "") -> dict:
        """
        自动为文本打标签

        返回: {
            'project_type': ['房建', '新建'],
            'doc_section': 'technical',
            'craft_tags': ['混凝土', '裂缝防治'],
            'has_params': True,
            'data_density': 'high'
        }
        """
        full_text = f"{chapter} {section} {text}"

        # 工程类型
        project_types = []
        for ptype, keywords in self.PROJECT_TYPE_RULES.items():
            if any(kw in full_text for kw in keywords):
                project_types.append(ptype)
        if not project_types:
            project_types = ["未分类"]

        # 文档段落类型
        doc_section = "other"
        max_score = 0
        for section_type, keywords in self.DOC_SECTION_RULES.items():
            score = sum(1 for kw in keywords if kw in full_text)
            if score > max_score:
                max_score = score
                doc_section = section_type

        # 工艺标签
        craft_tags = []
        for tag_name, keywords in self.CRAFT_TAG_RULES.items():
            if any(kw in full_text for kw in keywords):
                craft_tags.append(tag_name)

        # 参数密度评估
        # 查找具体数值（如 35Mpa、200mm、1:3、≥95%）
        param_patterns = [
            r"\d+(?:\.\d+)?(?:mm|cm|m|MPa|Mpa|KN|kN|℃|°C|kg|吨|米|%)",
            r"\d+:\d+",  # 配合比
            r"[≥≤><]\s*\d+",
            r"\d+(?:\.\d+)?(?:千克|立方米|平方米|毫米|厘米)",
        ]
        param_count = sum(
            len(re.findall(p, text)) for p in param_patterns
        )
        has_params = param_count >= 3
        if param_count >= 8:
            data_density = "high"
        elif param_count >= 3:
            data_density = "medium"
        else:
            data_density = "low"

        return {
            "project_type": project_types,
            "doc_section": doc_section,
            "craft_tags": craft_tags,
            "has_params": has_params,
            "data_density": data_density,
        }


# ============================================================
# Step 5: Embedding 向量化（三引擎：Gemini / OpenAI / 本地模型）
# ============================================================
class EmbeddingService:
    """
    三引擎文本向量化服务
    - gemini:  Google Gemini Embedding API（推荐，免费额度大）
    - openai:  OpenAI text-embedding-3-small
    - local:   本地 bge-small-zh 模型（零费用，离线可用）
    """

    # 各引擎的向量维度
    DIMENSIONS = {
        "gemini": 3072,   # gemini-embedding-001 实际输出 3072 维
        "openai": 1536,
        "local": 512,
    }

    def __init__(self, engine: str = "gemini", api_key: str = None):
        self.engine = engine
        self.dimensions = self.DIMENSIONS.get(engine, 768)
        self.ready = False

        if engine == "gemini":
            self._init_gemini(api_key)
        elif engine == "openai":
            self._init_openai(api_key)
        elif engine == "local":
            self._init_local()
        else:
            logger.error(f"❌ 未知引擎: {engine}（可选: gemini / openai / local）")

    def _init_gemini(self, api_key: str = None):
        """初始化 Gemini Embedding"""
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.warning("⚠️ 未设置 GEMINI_API_KEY，请在 backend/.env 中配置")
            return
        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
            self.model_name = "gemini-embedding-001"
            self.ready = True
            logger.info(f"  ✅ Gemini Embedding 引擎就绪 (维度: {self.dimensions})")
        except ImportError:
            logger.error("  ❌ 请安装: pip install google-genai")

    def _init_openai(self, api_key: str = None):
        """初始化 OpenAI Embedding"""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("⚠️ 未设置 OPENAI_API_KEY，请在 backend/.env 中配置")
            return
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
            self.model_name = "text-embedding-3-small"
            self.ready = True
            logger.info(f"  ✅ OpenAI Embedding 引擎就绪 (维度: {self.dimensions})")
        except ImportError:
            logger.error("  ❌ 请安装: pip install openai")

    def _init_local(self):
        """初始化本地 BGE 模型（首次下载 ~90MB）"""
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("  ⏳ 加载本地模型 bge-small-zh-v1.5（首次需下载 ~90MB）...")
            self.model = SentenceTransformer("BAAI/bge-small-zh-v1.5")
            self.ready = True
            logger.info(f"  ✅ 本地 Embedding 引擎就绪 (维度: {self.dimensions})")
        except ImportError:
            logger.error("  ❌ 请安装: pip install sentence-transformers")

    def embed(self, texts: list[str]) -> list[list[float]]:
        """批量向量化"""
        if not self.ready:
            logger.warning("  ⚠️ Embedding 引擎未就绪，跳过向量化")
            return [None] * len(texts)

        if self.engine == "gemini":
            return self._embed_gemini(texts)
        elif self.engine == "openai":
            return self._embed_openai(texts)
        elif self.engine == "local":
            return self._embed_local(texts)

        return [None] * len(texts)

    def _embed_gemini(self, texts: list[str]) -> list[list[float]]:
        """Gemini 批量向量化"""
        embeddings = []
        batch_size = 100
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            logger.info(f"  🧮 [Gemini] 向量化 {i + 1}-{i + len(batch)}/{len(texts)}")
            try:
                result = self.client.models.embed_content(
                    model=self.model_name,
                    contents=batch,
                )
                for emb in result.embeddings:
                    embeddings.append(emb.values)
            except Exception as e:
                logger.error(f"  ❌ Gemini 向量化失败: {e}")
                embeddings.extend([None] * len(batch))
        return embeddings

    def _embed_openai(self, texts: list[str]) -> list[list[float]]:
        """OpenAI 批量向量化"""
        embeddings = []
        batch_size = 100
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            logger.info(f"  🧮 [OpenAI] 向量化 {i + 1}-{i + len(batch)}/{len(texts)}")
            try:
                response = self.client.embeddings.create(
                    model=self.model_name,
                    input=batch,
                )
                for item in response.data:
                    embeddings.append(item.embedding)
            except Exception as e:
                logger.error(f"  ❌ OpenAI 向量化失败: {e}")
                embeddings.extend([None] * len(batch))
        return embeddings

    def _embed_local(self, texts: list[str]) -> list[list[float]]:
        """本地模型批量向量化"""
        logger.info(f"  🧮 [本地模型] 向量化 {len(texts)} 个片段...")
        try:
            vectors = self.model.encode(texts, show_progress_bar=True)
            return [v.tolist() for v in vectors]
        except Exception as e:
            logger.error(f"  ❌ 本地向量化失败: {e}")
            return [None] * len(texts)


# ============================================================
# Step 6: pgvector 入库（可选）
# ============================================================
class PgVectorStore:
    """将 chunks 写入 PostgreSQL + pgvector"""

    def __init__(self, db_url: str, vector_dims: int = 3072):
        self.vector_dims = vector_dims
        try:
            import psycopg2
            self.conn = psycopg2.connect(db_url)
            self.conn.autocommit = True
            logger.info("  ✅ 数据库连接成功")
        except Exception as e:
            logger.error(f"  ❌ 数据库连接失败: {e}")
            self.conn = None

    def init_table(self):
        """创建表和索引（动态向量维度）"""
        if not self.conn:
            return

        create_sql = f"""
        CREATE EXTENSION IF NOT EXISTS vector;
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

        CREATE TABLE IF NOT EXISTS training_chunks (
            id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            content       TEXT NOT NULL,
            content_hash  VARCHAR(64) UNIQUE NOT NULL,
            embedding     VECTOR({self.vector_dims}),

        -- 来源追溯
        source_file   TEXT,
        page_start    INTEGER,
        page_end      INTEGER,
        chapter       TEXT,
        section       TEXT,

        -- 分类标签
        project_type  TEXT[],
        doc_section   TEXT,
        craft_tags    TEXT[],

        -- 质量元数据
        char_count    INTEGER,
        has_params    BOOLEAN DEFAULT false,
        data_density  TEXT DEFAULT 'medium',
        bid_result    BOOLEAN,
        quality_score FLOAT,

        -- 时间
        created_at    TIMESTAMPTZ DEFAULT NOW(),
        updated_at    TIMESTAMPTZ DEFAULT NOW()
    );

    -- 注意: pgvector 的 hnsw/ivfflat 索引限制 2000 维
    -- Gemini embedding 输出 3072 维，暂不建向量索引
    -- 精确搜索仍可用（小数据量足够快），或后续使用降维方案

    -- 元数据组合索引
    CREATE INDEX IF NOT EXISTS idx_chunks_tags
        ON training_chunks USING GIN (project_type, craft_tags);

    CREATE INDEX IF NOT EXISTS idx_chunks_doc_section
        ON training_chunks (doc_section);
        """

        with self.conn.cursor() as cur:
            cur.execute(create_sql)
        logger.info(f"  ✅ 数据表初始化完成 (向量维度: {self.vector_dims})")

    def upsert(self, chunks: list[Chunk]):
        """插入或更新 chunks（基于 content_hash 去重）"""
        if not self.conn:
            return

        inserted = 0
        skipped = 0
        with self.conn.cursor() as cur:
            for chunk in chunks:
                try:
                    embedding_str = (
                        str(chunk.embedding) if chunk.embedding else None
                    )
                    cur.execute(
                        """
                        INSERT INTO training_chunks (
                            id, content, content_hash, embedding,
                            source_file, page_start, page_end, chapter, section,
                            project_type, doc_section, craft_tags,
                            char_count, has_params, data_density
                        ) VALUES (
                            %s, %s, %s, %s::vector,
                            %s, %s, %s, %s, %s,
                            %s, %s, %s,
                            %s, %s, %s
                        )
                        ON CONFLICT (content_hash) DO NOTHING
                        """,
                        (
                            chunk.id, chunk.content, chunk.content_hash,
                            embedding_str,
                            chunk.source_file, chunk.page_start, chunk.page_end,
                            chunk.chapter, chunk.section,
                            chunk.project_type, chunk.doc_section, chunk.craft_tags,
                            chunk.char_count, chunk.has_params, chunk.data_density,
                        ),
                    )
                    if cur.rowcount > 0:
                        inserted += 1
                    else:
                        skipped += 1
                except Exception as e:
                    logger.warning(f"  ⚠️ 插入失败: {e}")
                    skipped += 1

        logger.info(f"  ✅ 入库完成: 新增 {inserted}, 跳过(重复) {skipped}")

    def close(self):
        if self.conn:
            self.conn.close()


# ============================================================
# 主流水线
# ============================================================
class ChunkingPipeline:
    """标书切片完整流水线"""

    def __init__(
        self,
        max_chunk_size: int = 800,
        min_chunk_size: int = 100,
        vectorize: bool = False,
        engine: str = "gemini",
        db_url: str = None,
        api_key: str = None,
    ):
        self.extractor = PDFExtractor()
        self.chunker = ChapterChunker(max_chunk_size, min_chunk_size)
        self.desensitizer = Desensitizer()
        self.tagger = AutoTagger()
        self.vectorize = vectorize
        self.db_url = db_url

        if vectorize:
            self.embedder = EmbeddingService(engine=engine, api_key=api_key)
        else:
            self.embedder = None

        if db_url:
            # 根据引擎获取向量维度
            vector_dims = self.embedder.dimensions if self.embedder else 3072
            self.store = PgVectorStore(db_url, vector_dims=vector_dims)
            self.store.init_table()
        else:
            self.store = None

    def process_file(self, pdf_path: str) -> list[Chunk]:
        """处理单个 PDF 文件 — 含表格检测分流"""
        filename = os.path.basename(pdf_path)
        logger.info(f"\n{'='*60}")
        logger.info(f"📂 开始处理: {filename}")
        logger.info(f"{'='*60}")

        # Step 1: 提取文本
        pages = self.extractor.extract(pdf_path)
        if not pages:
            logger.warning(f"  ⚠️ 跳过（无法提取文本）: {filename}")
            return []

        # Step 1.5: 表格检测分流（新增）
        table_rows = self._extract_tables_from_pdf(pdf_path, filename)
        if table_rows > 0:
            logger.info(f"  📊 表格分流: {table_rows} 行已入库 structured_tables")

        # Step 2: 章节切片（纯文本部分）
        raw_chunks = self.chunker.chunk(pages)

        # Step 3 & 4: 脱敏 + 标签
        chunks = []
        safe_filename = self.desensitizer.desensitize_filename(filename)

        for raw in raw_chunks:
            # 脱敏
            clean_text = self.desensitizer.desensitize(raw["text"])

            # 自动打标签
            tags = self.tagger.tag(
                raw["text"],  # 用原始文本打标签（脱敏前）
                raw["chapter"],
                raw["section"],
            )

            # 内容哈希（用于去重）
            content_hash = hashlib.sha256(clean_text.encode()).hexdigest()[:16]

            chunk = Chunk(
                id=str(uuid.uuid4()),
                content=clean_text,
                content_hash=content_hash,
                source_file=safe_filename,
                original_file=filename,
                page_start=raw["page_start"],
                page_end=raw["page_end"],
                chapter=raw["chapter"],
                section=raw["section"],
                project_type=tags["project_type"],
                doc_section=tags["doc_section"],
                craft_tags=tags["craft_tags"],
                char_count=len(clean_text),
                has_params=tags["has_params"],
                data_density=tags["data_density"],
            )
            chunks.append(chunk)

        logger.info(f"  🏷️ 标签统计:")
        logger.info(f"    工程类型: {set(t for c in chunks for t in c.project_type)}")
        logger.info(f"    高密度片段: {sum(1 for c in chunks if c.data_density == 'high')}/{len(chunks)}")
        logger.info(f"    含参数片段: {sum(1 for c in chunks if c.has_params)}/{len(chunks)}")

        # Step 5: 向量化（可选）
        if self.vectorize and self.embedder and self.embedder.ready:
            logger.info(f"  🧮 开始向量化 {len(chunks)} 个片段...")
            texts = [c.content for c in chunks]
            embeddings = self.embedder.embed(texts)
            for chunk, emb in zip(chunks, embeddings):
                chunk.embedding = emb
            logger.info(f"  ✅ 向量化完成")

        # Step 6: 入库（可选）
        if self.store:
            logger.info(f"  💾 写入数据库...")
            self.store.upsert(chunks)

        return chunks

    def _extract_tables_from_pdf(self, pdf_path: str, filename: str) -> int:
        """
        从 PDF 中检测表格并入库到 structured_tables

        使用 PyMuPDF 的 find_tables() 方法检测表格结构。
        检测到的表格跳过文本切片，直接结构化入库。
        """
        total_rows = 0
        try:
            import fitz
        except ImportError:
            logger.debug("  PyMuPDF 未安装，跳过表格检测")
            return 0

        if not self.db_url:
            return 0

        try:
            # 懒加载表格入库服务
            from app.services.table_ingestion import TableIngestionService
            ingestion = TableIngestionService(db_url=self.db_url)
        except Exception:
            # 独立脚本运行时可能无法导入 app 模块
            logger.debug("  表格入库服务不可用，跳过表格检测")
            return 0

        try:
            doc = fitz.open(pdf_path)
            for page_idx in range(doc.page_count):
                page = doc[page_idx]
                try:
                    tables = page.find_tables()
                    for table in tables:
                        # 提取表格数据
                        data = table.extract()
                        if not data or len(data) < 2:
                            continue  # 至少需要表头+1行数据

                        headers = [str(h or "").strip() for h in data[0]]
                        rows = [[str(c or "").strip() for c in row] for row in data[1:]]

                        # 过滤空行
                        rows = [r for r in rows if any(c.strip() for c in r)]
                        if not rows:
                            continue

                        # 入库
                        count = ingestion.ingest_table(
                            headers=headers,
                            rows=rows,
                            source_file=filename,
                            table_title=f"Page {page_idx + 1} 表格",
                        )
                        total_rows += count
                except Exception as e:
                    logger.debug(f"  表格检测跳过 page {page_idx + 1}: {e}")
                    continue

            doc.close()
            ingestion.close()
        except Exception as e:
            logger.warning(f"  表格检测异常: {e}")

        return total_rows

    def process_directory(self, dir_path: str) -> list[Chunk]:
        """批量处理目录下所有 PDF"""
        all_chunks = []
        pdf_files = sorted(Path(dir_path).glob("*.pdf"))

        if not pdf_files:
            logger.error(f"❌ 目录 {dir_path} 中没有找到 PDF 文件")
            return []

        logger.info(f"📁 发现 {len(pdf_files)} 个 PDF 文件")

        for pdf_path in pdf_files:
            chunks = self.process_file(str(pdf_path))
            all_chunks.extend(chunks)

        return all_chunks

    def save_json(self, chunks: list[Chunk], output_path: str):
        """将切片结果保存为 JSON"""
        data = []
        for chunk in chunks:
            d = asdict(chunk)
            # 不输出原始文件名（隐私）和 embedding（太大）
            d.pop("original_file", None)
            if d.get("embedding"):
                d["embedding"] = f"[{len(d['embedding'])} dims]"
            data.append(d)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"\n📦 JSON 已保存: {output_path} ({len(data)} 个片段)")

    def close(self):
        if self.store:
            self.store.close()


# ============================================================
# 统计报告
# ============================================================
def print_report(chunks: list[Chunk]):
    """打印切片统计报告"""
    if not chunks:
        return

    logger.info(f"\n{'='*60}")
    logger.info(f"📊 切片统计报告")
    logger.info(f"{'='*60}")
    logger.info(f"  总片段数: {len(chunks)}")
    logger.info(f"  总字符数: {sum(c.char_count for c in chunks):,}")
    logger.info(f"  平均字符: {sum(c.char_count for c in chunks) // len(chunks)}")

    # 按来源统计
    logger.info(f"\n  📂 按来源文件:")
    sources = {}
    for c in chunks:
        sources.setdefault(c.source_file, []).append(c)
    for src, src_chunks in sources.items():
        logger.info(f"    {src}: {len(src_chunks)} 片段, "
                    f"{sum(c.char_count for c in src_chunks):,} 字符")

    # 按文档类型统计
    logger.info(f"\n  📋 按文档类型:")
    sections = {}
    for c in chunks:
        sections.setdefault(c.doc_section, 0)
        sections[c.doc_section] += 1
    for sec, count in sorted(sections.items(), key=lambda x: -x[1]):
        logger.info(f"    {sec}: {count} 片段")

    # 数据密度分布
    logger.info(f"\n  📈 数据密度分布:")
    densities = {"high": 0, "medium": 0, "low": 0}
    for c in chunks:
        densities[c.data_density] = densities.get(c.data_density, 0) + 1
    for d, count in densities.items():
        bar = "█" * (count * 30 // len(chunks))
        logger.info(f"    {d:8s}: {bar} {count} ({100*count//len(chunks)}%)")


# ============================================================
# CLI 入口
# ============================================================
def main():
    parser = argparse.ArgumentParser(
        description="标标 AI · 标书知识库切片入库流水线",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--input", "-i", required=True,
        help="输入文件路径（PDF 文件或包含 PDF 的目录）",
    )
    parser.add_argument(
        "--output", "-o", default="chunks.json",
        help="输出 JSON 文件路径（默认: chunks.json）",
    )
    parser.add_argument(
        "--max-chunk-size", type=int, default=800,
        help="最大切片字符数（默认: 800）",
    )
    parser.add_argument(
        "--min-chunk-size", type=int, default=100,
        help="最小切片字符数（默认: 100）",
    )
    parser.add_argument(
        "--vectorize", action="store_true",
        help="启用 Embedding 向量化",
    )
    parser.add_argument(
        "--engine", choices=["gemini", "openai", "local"], default="gemini",
        help="向量化引擎: gemini（推荐）/ openai / local（默认: gemini）",
    )
    parser.add_argument(
        "--db-url",
        help="PostgreSQL 连接字符串（启用后自动创建表并入库）",
    )
    parser.add_argument(
        "--api-key",
        help="API Key（也可通过 .env 文件设置 GEMINI_API_KEY 或 OPENAI_API_KEY）",
    )

    args = parser.parse_args()

    # 初始化流水线
    pipeline = ChunkingPipeline(
        max_chunk_size=args.max_chunk_size,
        min_chunk_size=args.min_chunk_size,
        vectorize=args.vectorize,
        engine=args.engine,
        db_url=args.db_url,
        api_key=args.api_key,
    )

    # 执行处理
    input_path = args.input
    if os.path.isdir(input_path):
        chunks = pipeline.process_directory(input_path)
    elif os.path.isfile(input_path):
        chunks = pipeline.process_file(input_path)
    else:
        logger.error(f"❌ 路径不存在: {input_path}")
        sys.exit(1)

    # 输出 JSON
    if chunks:
        pipeline.save_json(chunks, args.output)
        print_report(chunks)
    else:
        logger.warning("⚠️ 没有生成任何有效片段")

    pipeline.close()

    logger.info(f"\n✅ 流水线执行完毕!")


if __name__ == "__main__":
    main()
