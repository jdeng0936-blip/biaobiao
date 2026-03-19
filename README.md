# 标标 AI — 智能标书制作平台

> 全程 AI 赋能的标书制作平台。从招标文件智能解读到高分标书生成，AI 全链路介入。

## 快速开始

### 开发环境

```bash
# 1. 启动数据库（Docker）
docker compose up -d postgres redis

# 2. 启动后端
cd backend && pip install -r requirements.txt
cp .env.example .env  # 填写 GEMINI_API_KEY
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# 3. 灌入种子数据（可选）
cd backend && python -m scripts.seed_knowledge

# 4. 启动前端
cd frontend && npm install && npx next dev -p 3001
```

### 一键 Docker 部署

```bash
docker compose up -d
# 端口映射: PostgreSQL:5434 | Redis:6380 | API:8001 | Web:3001
```

## 技术栈

| 层 | 技术 |
|:---|:---|
| 前端 | Next.js 14 + TypeScript + Zustand + Framer Motion |
| 后端 | FastAPI + SQLAlchemy 2.0 + asyncpg + Pydantic V2 |
| 数据库 | PostgreSQL 16 + pgvector + pg_trgm |
| AI | Gemini API (生成+Embedding) + RAG 三层检索 |
| 部署 | Docker Compose (多阶段构建) + Alembic |
| CI | GitHub Actions (pytest + tsc) |

## 核心能力

```
📝 5步标书工作流     招标解读 → 评分提取 → 目录生成 → AI撰写 → 审查导出
🧠 三层 RAG 检索     向量语义 + 结构化 + 关键词，知识库智能召回
🔄 数据飞轮          用户反馈(采纳/编辑/拒绝) → 差分沉入知识库 → AI 自我进化
🛡️ 反 AI 审查        L1 统计分析 + L2 N-gram 基线比对，消除 AI 痕迹
🔐 智能脱敏          正则+NER 双引擎，标书敏感信息自动替换/还原
📊 行业词库          6 大工程类型专用术语/规范/评审焦点/扣分项
📄 Word 导出         一键生成格式化 DOCX 投标文件
```

## 系统架构

```
前端 (Next.js)            后端 (FastAPI)              数据库
├── Landing               ├── auth (JWT)              ├── users
├── Dashboard (+飞轮)     ├── knowledge (三层RAG)     ├── projects
├── Workspace (5 Step)    ├── generate (SSE流)        ├── knowledge_chunks
├── Library (+AI训练)     ├── scoring (评分点)        ├── training_chunks
├── AI 对话               ├── feedback (数据飞轮)     ├── feedback_logs
├── Anti-Review           ├── anti-review (L1+L2)     ├── desensitize_entries
├── Craft Library         ├── desensitize (脱敏)      └── structured_tables
└── Variants              ├── project (CRUD)
                          ├── export (Word)
                          ├── craft (工艺图谱)
                          └── variant (变体引擎)
```

## API 端点

| 模块 | 端点 | 功能 |
|:---|:---:|:---|
| auth | 4 | 注册/登录/刷新/用户信息 JWT |
| project | 5 | CRUD + 统计 |
| knowledge | 3 | 三层 RAG 检索 + 统计 + 文件列表 |
| generate | 2 | SSE 流式章节生成 + AI 对话 |
| scoring | 2 | 评分点提取 + 目录生成 |
| feedback | 2 | 反馈提交 + 飞轮统计 |
| upload | 1 | 文档上传 (PDF/Word) |
| anti-review | 2 | 单文检测 + 批量审查 |
| export | 1 | Word 导出 |
| craft | 3 | 工艺树/详情/搜索 |
| variant | 4 | 维度/生成/列表/矩阵 |
| health | 1 | 健康检查 |

## 测试覆盖

```
240 passed in 2.37s — 18 个测试文件覆盖 22 个核心模块
```

| 文件 | 用例 | 覆盖 |
|:---|:---:|:---|
| test_pipeline | 27 | 表格推断 / 数值提取 / 章节切片 / NER脱敏 / 自动标签 |
| test_craft_auth_scoring | 27 | 工艺图谱 + 认证模型 + 评分模型 |
| test_security_feedback | 20 | Settings/bcrypt/JWT + 反馈飞轮模型 |
| test_generate | 19 | Pydantic 模型 / Prompt 构建 / RAG 注入 |
| test_anti_review | 18 | L1 统计 + L2 N-gram + 综合审查 |
| test_variant | 15 | 变体配置 / 生成逻辑 / 相似度矩阵 |
| test_knowledge_api | 15 | 知识库模型 / tenant_id 注入 |
| test_feedback_service | 13 | 差分计算 + 飞轮入库 + 统计查询 |
| test_storage | 13 | StorageBackend CRUD / 工厂函数 |
| test_llm_provider | 12 | ModelConfig / GeminiProvider / LLMSelector |
| test_project | 11 | UUID 安全解析 / Pydantic 模型 / ORM 转换 |
| test_embedding | 11 | Gemini Embedding Mock + 行业词库 6 行业校验 |
| test_desensitize | 10 | 脱敏 mask/unmask/roundtrip + 词典 |
| test_api_integration | 9 | 健康检查 / 反审标 / 工艺 / 变体 / 导出 / 评分 |
| test_export_docx | 8 | DOCX 生成 / ZIP 校验 / 内容完整性 |
| test_rag | 7 | 三层检索 + 反馈沉入 |
| test_llm | 5 | Prompt 构建 + Planner + Reviewer |

## 环境变量

```bash
# backend/.env—— 参考 backend/.env.example
DATABASE_URL=postgresql+asyncpg://biaobiao:biaobiao123@localhost:5434/biaobiao
GEMINI_API_KEY=your-key
JWT_SECRET_KEY=change-me-in-production

# frontend/.env.local
NEXT_PUBLIC_API_BASE=http://localhost:8001
```

## 项目结构

```
EmptyProject/
├── .github/workflows/ci.yml    # GitHub Actions CI
├── docker-compose.yml           # 一键部署（生产加固）
├── backend/
│   ├── .env.example            # 环境变量模板
│   ├── app/
│   │   ├── api/v1/             # FastAPI 路由 (11 模块)
│   │   ├── core/              # 安全/配置/数据库/依赖注入
│   │   ├── models/             # SQLAlchemy ORM
│   │   ├── services/           # 业务逻辑层
│   │   ├── llm/               # LLM Provider + Selector
│   │   └── data/               # 行业词库 + 种子数据
│   ├── alembic/                # 数据库迁移
│   ├── scripts/                # 工具脚本 (seed/pipeline)
│   ├── test_*.py               # 240 个单元测试（18 文件）
│   └── Dockerfile              # 多阶段构建 + non-root
└── frontend/
    ├── src/
    │   ├── app/                # Next.js 页面 (10 页)
    │   ├── components/         # 共享组件
    │   ├── lib/api.ts          # 统一 API 客户端
    │   └── store/              # Zustand 状态管理
    └── Dockerfile              # 3 阶段 standalone + non-root
```

## 许可

MIT License
