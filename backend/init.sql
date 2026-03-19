-- 标标 AI — PostgreSQL 初始化脚本
-- docker-compose 挂载后自动执行一次

-- 启用 pgvector 向量扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 启用 pg_trgm 模糊搜索（用于结构化检索）
CREATE EXTENSION IF NOT EXISTS pg_trgm;
