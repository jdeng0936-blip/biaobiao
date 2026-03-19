# ============================================
# 标标 AI 前端 — 多阶段 Dockerfile（standalone 模式）
# 最终镜像仅含运行时必要文件，体积 ~100MB
# ============================================

# Stage 1: 安装依赖（可单独缓存）
FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci --ignore-scripts

# Stage 2: 构建（依赖 standalone 输出）
FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# 启用 standalone 输出模式（需 next.config 配置 output: 'standalone'）
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# Stage 3: 生产镜像（极简）
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# 创建非 root 用户
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# 只复制必需文件
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
