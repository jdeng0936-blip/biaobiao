---
description: 启动标标 AI 前后端服务，自动检测端口冲突并调整
---

# 启动标标 AI 服务

## 端口冲突规则（⚠️ 强制执行）

启动任何服务前 **必须先检测端口占用**，如果目标端口被占用，**立即自动递增到下一个可用端口**，绝不硬等或报错阻塞。

检测方式：
```bash
lsof -ti :<PORT> >/dev/null 2>&1 && echo "占用" || echo "可用"
```

默认端口分配：
- 前端: 3001（如占用 → 3002 → 3003 ...）
- 后端: 8001（如占用 → 8002 → 8003 ...）
- PostgreSQL Docker: 5434（如占用 → 5435 → 5436 ...）

**如果调整了端口，必须同步更新：**
1. 前端 `.env.local` 中的 `NEXT_PUBLIC_API_BASE`
2. 后端 `.env` 中的 `DATABASE_URL`（如 PG 端口变了）
3. 后端 `main.py` CORS `allow_origins`（如前端端口变了）

## 步骤

### 1. 检测并启动 PostgreSQL Docker 容器

```bash
# 检测 biaobiao-pg 容器是否已在运行
docker ps --filter "name=biaobiao-pg" --format '{{.Status}}' | grep -q "Up" && echo "PG 已运行" && exit 0

# 找可用端口（从 5434 开始递增）
for p in 5434 5435 5436 5437; do
  lsof -ti :$p >/dev/null 2>&1 || { PG_PORT=$p; break; }
done

# 启动容器
docker run -d --name biaobiao-pg \
  -e POSTGRES_USER=biaobiao \
  -e POSTGRES_PASSWORD=biaobiao123 \
  -e POSTGRES_DB=biaobiao \
  -p ${PG_PORT}:5432 \
  pgvector/pgvector:pg16

# 等待就绪 + 启用 pgvector
sleep 3
docker exec biaobiao-pg psql -U biaobiao -d biaobiao -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 更新 .env（如端口不是默认 5434）
```

### 2. 启动后端

// turbo
```bash
# 找可用端口
for p in 8001 8002 8003; do
  lsof -ti :$p >/dev/null 2>&1 || { API_PORT=$p; break; }
done
echo "后端将使用端口: $API_PORT"
```

⚠️ **后端是长运行进程**，必须提示用户在自己终端中运行：
```bash
cd backend && python3 -m uvicorn app.main:app --host 0.0.0.0 --port <API_PORT> --reload
```

### 3. 启动前端

// turbo
```bash
# 找可用端口
for p in 3001 3002 3003; do
  lsof -ti :$p >/dev/null 2>&1 || { FE_PORT=$p; break; }
done
echo "前端将使用端口: $FE_PORT"
```

⚠️ **前端也是长运行进程**，必须提示用户在自己终端中运行：
```bash
cd frontend && npx next dev -p <FE_PORT>
```

### 4. 验证

// turbo
```bash
curl -s http://localhost:<API_PORT>/api/health
curl -s -o /dev/null -w '%{http_code}' http://localhost:<FE_PORT>
```
