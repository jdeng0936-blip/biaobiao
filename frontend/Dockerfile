# 标标 AI 前端 — 多阶段 Dockerfile
# Stage 1: 构建
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Stage 2: 生产镜像（仅含构建产物）
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

# 只复制生产必需文件
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/node_modules ./node_modules

EXPOSE 3000

CMD ["npm", "start"]
