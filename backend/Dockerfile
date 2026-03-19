# ============================================
# 标标 AI 后端 — 多阶段 Dockerfile
# 分离依赖安装与代码复制，优化缓存层
# ============================================

# Stage 1: 构建环境（安装编译依赖）
FROM python:3.12-slim AS builder

WORKDIR /app

# 系统编译依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Python 依赖（独立缓存层）
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: 生产镜像（仅运行时依赖）
FROM python:3.12-slim AS runner

WORKDIR /app

# 仅安装运行时库（libpq）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 && \
    rm -rf /var/lib/apt/lists/*

# 创建非 root 用户
RUN groupadd --system --gid 1001 appgroup && \
    useradd --system --uid 1001 --gid appgroup appuser

# 复制 Python 依赖
COPY --from=builder /install /usr/local

# 复制应用代码
COPY . .

# 切换到非 root 用户
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
