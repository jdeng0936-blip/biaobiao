# 标标 AI — 智能标书制作平台

> 全程 AI 赋能的标书制作平台。从招标文件智能解读到高分标书生成，AI 全链路介入。

## 快速开始

### 开发环境

```bash
# 1. 启动数据库（Docker）
docker compose up -d postgres redis

# 2. 启动后端
cd backend && pip install -r requirements.txt
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# 3. 启动前端
cd frontend && npm install && npx next dev -p 3001
```

### 一键 Docker 部署

```bash
docker compose up -d
# 自定义端口
PG_PORT=5434 API_PORT=8001 FE_PORT=3001 docker compose up -d
```

## 技术栈

| 层 | 技术 |
|:---|:---|
| 前端 | Next.js 14 + TypeScript + Tailwind CSS + Zustand + Framer Motion |
| 后端 | FastAPI + SQLAlchemy 2.0 + asyncpg + Pydantic V2 |
| 数据库 | PostgreSQL 16 + pgvector |
| AI | Gemini API + OpenAI GPT + Langchain + Langfuse |
| 部署 | Docker Compose + Alembic |

## 系统架构

```
前端 (Next.js)            后端 (FastAPI)            数据库
├── Landing               ├── auth (JWT)            ├── users
├── Login                 ├── knowledge (三层RAG)   ├── projects
├── Dashboard             ├── generate (SSE流)      ├── desensitize_entries
├── Workspace (5 Step)    ├── scoring (评分点)      ├── structured_tables
├── Library               ├── project (CRUD)        └── knowledge_chunks
├── Anti-Review           ├── craft (工艺图谱)
├── Craft Library         ├── variant (变体引擎)
└── Variants              └── export (Word导出)
```

## API 端点 (25 个)

| 模块 | 端点数 | 功能 |
|:---|:---:|:---|
| auth | 2 | 注册/登录 JWT |
| knowledge | 3 | 三层 RAG 检索 |
| generate | 1 | SSE 流式生成 |
| scoring | 2 | 评分点提取+目录 |
| upload | 1 | PDF 文件上传 |
| anti-review | 1 | 反审标检测 |
| export | 1 | Word 导出 |
| project | 6 | CRUD+统计 |
| craft | 3 | 工艺树/详情/搜索 |
| variant | 4 | 维度/生成/列表/矩阵 |
| health | 1 | 健康检查 |

## 环境变量

```bash
# backend/.env
DATABASE_URL=postgresql+asyncpg://biaobiao:biaobiao123@localhost:5434/biaobiao
GEMINI_API_KEY=your-key
OPENAI_API_KEY=your-key

# frontend/.env.local
NEXT_PUBLIC_API_BASE=http://localhost:8001
```

## 许可

MIT License
