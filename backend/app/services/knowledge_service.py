"""
知识库检索服务 — 三层检索管线
  Layer 1: pgvector 语义检索（training_chunks 表）
  Layer 2: structured_tables SQL 精确查询（关系表）
  Layer 3: 结果融合 + 去重 + 相关性重排序
"""
import os
import logging
from typing import Optional

import psycopg2
import psycopg2.extras
import psycopg2.pool

logger = logging.getLogger("knowledge_service")

# 进程级连接池（所有 KnowledgeService 实例共享）
_pool: psycopg2.pool.SimpleConnectionPool | None = None


def _get_pool(db_url: str) -> psycopg2.pool.SimpleConnectionPool:
    """获取或创建进程级连接池"""
    global _pool
    if _pool is None or _pool.closed:
        _pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=5,
            dsn=db_url,
        )
        logger.info(f"✅ psycopg2 连接池已创建 (1-5)")
    return _pool


class KnowledgeService:
    """知识库三层检索核心服务

    注意：内部使用同步 psycopg2 连接池，在 FastAPI 异步路由中调用时必须通过
    async 包装方法（search_async/get_stats_async/get_files_async）
    以避免阻塞事件循环。
    """

    def __init__(self, db_url: str = None, tenant_id: str = "default"):
        raw_url = db_url or os.getenv(
            "DATABASE_URL",
            "postgresql://mac111@localhost:5432/biaobiao"
        )
        self.db_url = raw_url.replace("+asyncpg", "")
        self.tenant_id = tenant_id
        self._conn = None

    @property
    def conn(self):
        """从连接池获取连接（懒加载）"""
        if self._conn is None or self._conn.closed:
            pool = _get_pool(self.db_url)
            self._conn = pool.getconn()
        return self._conn

    # ============================================================
    # Layer 1: pgvector 语义检索
    # ============================================================
    def search_semantic(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        project_type: Optional[str] = None,
        doc_section: Optional[str] = None,
        min_density: Optional[str] = None,
        tenant_id: str = "default",
    ) -> list[dict]:
        """Layer 1 — 向量余弦相似度检索"""
        conditions = ["embedding IS NOT NULL", "tenant_id = %s"]
        filter_params = [tenant_id]

        if project_type:
            conditions.append("%s = ANY(project_type)")
            filter_params.append(project_type)

        if doc_section:
            conditions.append("doc_section = %s")
            filter_params.append(doc_section)

        if min_density:
            density_map = {"high": 3, "medium": 2, "low": 1}
            conditions.append(
                "CASE data_density "
                "WHEN 'high' THEN 3 WHEN 'medium' THEN 2 ELSE 1 END >= %s"
            )
            filter_params.append(density_map.get(min_density, 1))

        where_sql = "WHERE " + " AND ".join(conditions)
        embedding_str = str(query_embedding)
        params = [embedding_str] + filter_params + [embedding_str, top_k]

        sql = f"""
            SELECT
                id, content, source_file, chapter, section,
                project_type, doc_section, craft_tags,
                char_count, has_params, data_density,
                1 - (embedding <=> %s::vector) AS similarity
            FROM training_chunks
            {where_sql}
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """

        try:
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql, params)
                results = cur.fetchall()
        except Exception:
            self.conn.rollback()
            raise

        return [
            {
                "id": str(row["id"]),
                "content": row["content"],
                "source_file": row["source_file"],
                "chapter": row["chapter"],
                "section": row["section"],
                "project_type": row["project_type"],
                "doc_section": row["doc_section"],
                "craft_tags": row["craft_tags"],
                "char_count": row["char_count"],
                "has_params": row["has_params"],
                "data_density": row["data_density"],
                "similarity": round(float(row["similarity"]), 4),
                "retrieval_layer": "L1_semantic",  # 标记来源层
            }
            for row in results
        ]

    # ============================================================
    # Layer 2: structured_tables SQL 精确查询
    # ============================================================
    def search_structured(
        self,
        query_text: str,
        tenant_id: str = "default",
        table_type: Optional[str] = None,
        top_k: int = 5,
    ) -> list[dict]:
        """
        Layer 2 — 结构化表格精确查询

        从 structured_tables 中基于关键词匹配和 JSONB 搜索。
        适用于工程量清单、配合比、检验批次等结构化数据。
        """
        conditions = ["tenant_id = %s"]
        params: list = [tenant_id]

        if table_type:
            conditions.append("table_type = %s")
            params.append(table_type)

        # JSONB 全文搜索 + raw_text 模糊匹配
        conditions.append(
            "(raw_text ILIKE %s OR row_data::text ILIKE %s)"
        )
        like_pattern = f"%{query_text}%"
        params.extend([like_pattern, like_pattern])

        where_sql = "WHERE " + " AND ".join(conditions)
        params.append(top_k)

        sql = f"""
            SELECT
                id, source_file, table_type, table_title,
                row_index, row_data, raw_text,
                numeric_value_1, numeric_label_1,
                numeric_value_2, numeric_label_2
            FROM structured_tables
            {where_sql}
            ORDER BY row_index
            LIMIT %s
        """

        try:
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql, params)
                results = cur.fetchall()
        except Exception:
            self.conn.rollback()
            raise

        return [
            {
                "id": str(row["id"]),
                "content": self._format_structured_row(row),
                "source_file": row["source_file"],
                "table_type": row["table_type"],
                "table_title": row["table_title"],
                "row_data": row["row_data"],
                "similarity": 0.85,  # 精确匹配给固定高分
                "retrieval_layer": "L2_structured",
            }
            for row in results
        ]

    @staticmethod
    def _format_structured_row(row: dict) -> str:
        """将结构化行格式化为可读文本"""
        parts = []
        if row.get("table_title"):
            parts.append(f"[{row['table_title']}]")

        row_data = row.get("row_data", {})
        if isinstance(row_data, dict):
            kv_pairs = [f"{k}: {v}" for k, v in row_data.items()]
            parts.append("，".join(kv_pairs))
        elif row.get("raw_text"):
            parts.append(row["raw_text"])

        return " | ".join(parts)

    # ============================================================
    # Layer 3: 融合 + 去重 + 重排序
    # ============================================================
    def search(
        self,
        query_embedding: list[float],
        query_text: str = "",
        top_k: int = 10,
        project_type: Optional[str] = None,
        doc_section: Optional[str] = None,
        min_density: Optional[str] = None,
        tenant_id: str = "default",
        enable_structured: bool = True,
    ) -> list[dict]:
        """
        三层融合检索入口

        1. Layer 1: pgvector 语义检索
        2. Layer 2: structured_tables SQL 查询（如果有 query_text）
        3. Layer 3: 融合去重 + 按综合分数排序
        """
        # Layer 1: 语义检索
        semantic_results = self.search_semantic(
            query_embedding=query_embedding,
            top_k=top_k,
            project_type=project_type,
            doc_section=doc_section,
            min_density=min_density,
            tenant_id=tenant_id,
        )

        # Layer 2: 结构化查询（仅在有文本查询时启用）
        structured_results = []
        if enable_structured and query_text:
            try:
                structured_results = self.search_structured(
                    query_text=query_text,
                    tenant_id=tenant_id,
                    top_k=5,
                )
            except Exception as e:
                logger.warning(f"L2 结构化检索失败（不影响主检索）: {e}")

        # Layer 3: 融合去重
        merged = self._merge_results(semantic_results, structured_results, top_k)

        logger.info(
            f"三层检索: L1={len(semantic_results)} + L2={len(structured_results)} → 融合={len(merged)}"
        )
        return merged

    @staticmethod
    def _merge_results(
        semantic: list[dict],
        structured: list[dict],
        top_k: int,
    ) -> list[dict]:
        """融合去重 + 综合排序"""
        seen_ids = set()
        merged = []

        # 语义结果优先（已按相似度排序）
        for item in semantic:
            item_id = item["id"]
            if item_id not in seen_ids:
                seen_ids.add(item_id)
                merged.append(item)

        # 结构化结果补充（高优先级插入前部）
        for item in structured:
            item_id = item["id"]
            if item_id not in seen_ids:
                seen_ids.add(item_id)
                # 结构化精确匹配在语义结果之后、低相似度之前插入
                insert_pos = min(3, len(merged))  # 最多插到第3位
                merged.insert(insert_pos, item)

        return merged[:top_k]

    # ============================================================
    # 统计与文件列表（保持不变）
    # ============================================================
    def get_stats(self, tenant_id: str = None) -> dict:
        """获取知识库统计信息（含结构化表格）— 强制 tenant 过滤"""
        tid = tenant_id or self.tenant_id
        stats = {}

        # training_chunks 统计
        with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    count(*) as total_chunks,
                    count(embedding) as with_embedding,
                    count(DISTINCT source_file) as total_files,
                    sum(char_count) as total_chars,
                    count(*) FILTER (WHERE data_density = 'high') as high_density,
                    count(*) FILTER (WHERE data_density = 'medium') as medium_density,
                    count(*) FILTER (WHERE data_density = 'low') as low_density,
                    count(*) FILTER (WHERE has_params = true) as with_params
                FROM training_chunks
                WHERE tenant_id = %s
            """, (tid,))
            row = cur.fetchone()

        stats.update({
            "total_chunks": row["total_chunks"],
            "with_embedding": row["with_embedding"],
            "total_files": row["total_files"],
            "total_chars": row["total_chars"],
            "density": {
                "high": row["high_density"],
                "medium": row["medium_density"],
                "low": row["low_density"],
            },
            "with_params": row["with_params"],
        })

        # structured_tables 统计
        try:
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT
                        count(*) as total_rows,
                        count(DISTINCT source_file) as table_files,
                        count(DISTINCT table_type) as table_types
                    FROM structured_tables
                    WHERE tenant_id = %s
                """, (tid,))
                st_row = cur.fetchone()
                stats["structured_tables"] = {
                    "total_rows": st_row["total_rows"],
                    "table_files": st_row["table_files"],
                    "table_types": st_row["table_types"],
                }
        except Exception:
            stats["structured_tables"] = {"total_rows": 0, "table_files": 0, "table_types": 0}

        return stats

    def get_files(self, tenant_id: str = None) -> list[dict]:
        """获取知识库中所有文件列表 — 强制 tenant 过滤"""
        tid = tenant_id or self.tenant_id
        with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    source_file,
                    count(*) as chunk_count,
                    sum(char_count) as total_chars,
                    count(*) FILTER (WHERE data_density = 'high') as high_density,
                    count(*) FILTER (WHERE has_params = true) as with_params,
                    min(created_at) as first_added
                FROM training_chunks
                WHERE tenant_id = %s
                GROUP BY source_file
                ORDER BY count(*) DESC
            """, (tid,))
            return [dict(row) for row in cur.fetchall()]

    def insert_feedback_chunk(
        self,
        content: str,
        section: str,
        tenant_id: str = "default",
        source_tag: str = "human_revised",
        metadata: dict = None,
    ) -> bool:
        """
        Feedback Flywheel 专用 — 将人工修订的高质量语料插入 training_chunks

        所有写入操作强制绑定 tenant_id（多租户防线）。
        """
        import json
        from datetime import datetime

        sql = """
            INSERT INTO training_chunks (
                content, source_file, chapter, section,
                project_type, doc_section, craft_tags,
                char_count, has_params, data_density,
                tenant_id, created_at
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s
            )
        """

        meta_str = json.dumps(metadata or {}, ensure_ascii=False)

        params = (
            content,
            f"feedback://{source_tag}",  # 来源标记为反馈
            section,                      # chapter
            section,                      # section
            "{}",                         # project_type (JSONB)
            "feedback",                   # doc_section
            f'{{"source": "{source_tag}", "meta": {meta_str}}}',  # craft_tags (JSONB)
            len(content),                 # char_count
            False,                        # has_params
            "high",                       # data_density — 人工修订一律标记为高密度
            tenant_id,                    # tenant_id — 多租户铁律
            datetime.now(tz=datetime.now().astimezone().tzinfo),  # created_at (timezone-aware)
        )

        try:
            with self.conn.cursor() as cur:
                cur.execute(sql, params)
            self.conn.commit()
            logger.info(
                f"[知识库] 飞轮语料已入库 | tenant={tenant_id} | section={section[:20]} | len={len(content)}"
            )
            return True
        except Exception as e:
            self.conn.rollback()
            logger.error(f"[知识库] 飞轮语料入库失败: {e}")
            return False

    def close(self):
        """归还连接到连接池"""
        if self._conn and not self._conn.closed:
            pool = _get_pool(self.db_url)
            pool.putconn(self._conn)
            self._conn = None

    # ============================================================
    # Async 包装方法 — 供 FastAPI 异步路由调用
    # ============================================================
    async def search_async(self, **kwargs) -> list[dict]:
        """异步包装 search()，避免阻塞事件循环"""
        import asyncio
        return await asyncio.to_thread(self.search, **kwargs)

    async def search_semantic_async(self, **kwargs) -> list[dict]:
        """异步包装 search_semantic()"""
        import asyncio
        return await asyncio.to_thread(self.search_semantic, **kwargs)

    async def get_stats_async(self, tenant_id: str = None) -> dict:
        """异步包装 get_stats()"""
        import asyncio
        return await asyncio.to_thread(self.get_stats, tenant_id)

    async def get_files_async(self, tenant_id: str = None) -> list[dict]:
        """异步包装 get_files()"""
        import asyncio
        return await asyncio.to_thread(self.get_files, tenant_id)
