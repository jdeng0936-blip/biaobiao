"""
表格数据结构化入库服务

将 PDF/Word 中解析出的表格数据转换为结构化 JSON 并入库到 structured_tables。
支持两种模式：
  1. 规则引擎：基于表头推断列含义，转换为 key-value
  2. LLM 辅助：对复杂表格调用 LLM 提取 JSON Schema
"""
import logging
import re
import uuid
from typing import Optional

import psycopg2
import psycopg2.extras
import os

logger = logging.getLogger("table_ingestion")

# 常见表格类型及其关键词
TABLE_TYPE_KEYWORDS = {
    "bill_of_quantities": ["工程量", "清单", "分部分项", "综合单价", "合价"],
    "mix_ratio": ["配合比", "混凝土", "水灰比", "砂率", "配比"],
    "inspection_batch": ["检验批", "验收", "质量检查", "检测"],
    "material_list": ["材料", "设备", "规格型号", "单位", "数量"],
    "equipment_list": ["设备", "机具", "型号", "功率", "台数"],
    "personnel_list": ["人员", "岗位", "姓名", "资质", "持证"],
    "schedule": ["工期", "进度", "计划", "节点", "里程碑"],
}


class TableIngestionService:
    """表格数据入库服务"""

    def __init__(self, db_url: str = None, tenant_id: str = "default"):
        self.db_url = db_url or os.getenv(
            "DATABASE_URL",
            "postgresql://mac111@localhost:5432/biaobiao"
        )
        self.tenant_id = tenant_id
        self._conn = None

    @property
    def conn(self):
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(self.db_url.replace("+asyncpg", ""))
        return self._conn

    def detect_table_type(self, headers: list[str], title: str = "") -> str:
        """根据表头和标题推断表格类型"""
        combined = " ".join(headers) + " " + title
        scores = {}
        for table_type, keywords in TABLE_TYPE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in combined)
            if score > 0:
                scores[table_type] = score

        if scores:
            return max(scores, key=scores.get)
        return "unknown"

    def extract_numeric_values(self, row_data: dict) -> list[tuple]:
        """从行数据中提取关键数值字段"""
        numerics = []

        for key, value in row_data.items():
            if value is None:
                continue
            # 尝试提取数值
            val_str = str(value).strip()
            # 匹配数字（含小数、百分比、单位）
            match = re.search(r"([\d.]+)", val_str)
            if match:
                try:
                    num = float(match.group(1))
                    numerics.append((key, num))
                except ValueError:
                    continue

        return numerics[:2]  # 最多提取 2 个数值字段

    def ingest_table(
        self,
        headers: list[str],
        rows: list[list[str]],
        source_file: str,
        table_title: str = "",
        table_type: Optional[str] = None,
    ) -> int:
        """
        将解析出的表格数据入库到 structured_tables

        参数:
            headers: 表头列名列表
            rows: 数据行列表（每行是字符串列表）
            source_file: 来源文件名
            table_title: 表格标题
            table_type: 表格类型（可选，自动推断）

        返回:
            入库行数
        """
        if not headers or not rows:
            return 0

        if not table_type:
            table_type = self.detect_table_type(headers, table_title)

        inserted = 0
        try:
            with self.conn.cursor() as cur:
                for row_idx, row_values in enumerate(rows):
                    # 构建 key-value JSON（表头注入）
                    row_data = {}
                    for i, header in enumerate(headers):
                        if i < len(row_values):
                            row_data[header.strip()] = row_values[i].strip() if row_values[i] else None

                    # 原始文本（表头+数据拼接）
                    raw_text = " | ".join(
                        f"{h}: {row_data.get(h, '')}" for h in headers
                    )

                    # 提取数值字段
                    numerics = self.extract_numeric_values(row_data)
                    num_val_1 = numerics[0][1] if len(numerics) > 0 else None
                    num_label_1 = numerics[0][0] if len(numerics) > 0 else None
                    num_val_2 = numerics[1][1] if len(numerics) > 1 else None
                    num_label_2 = numerics[1][0] if len(numerics) > 1 else None

                    cur.execute("""
                        INSERT INTO structured_tables
                        (id, source_file, table_type, table_title, row_index,
                         row_data, raw_text,
                         numeric_value_1, numeric_label_1,
                         numeric_value_2, numeric_label_2,
                         tenant_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        str(uuid.uuid4()),
                        source_file,
                        table_type,
                        table_title or None,
                        row_idx,
                        psycopg2.extras.Json(row_data),
                        raw_text,
                        num_val_1, num_label_1,
                        num_val_2, num_label_2,
                        self.tenant_id,
                    ))
                    inserted += 1

            self.conn.commit()
            logger.info(f"✅ 表格入库: {source_file} → {table_type}, {inserted} 行")

        except Exception as e:
            self.conn.rollback()
            logger.error(f"表格入库失败: {e}")
            raise

        return inserted

    def ingest_kv_pairs(
        self,
        kv_list: list[dict],
        source_file: str,
        table_title: str = "",
        table_type: str = "unknown",
    ) -> int:
        """
        直接入库 key-value 字典列表

        用于已经由 LLM 提取完成的结构化数据。
        """
        if not kv_list:
            return 0

        inserted = 0
        try:
            with self.conn.cursor() as cur:
                for row_idx, row_data in enumerate(kv_list):
                    raw_text = "，".join(f"{k}: {v}" for k, v in row_data.items())
                    numerics = self.extract_numeric_values(row_data)

                    cur.execute("""
                        INSERT INTO structured_tables
                        (id, source_file, table_type, table_title, row_index,
                         row_data, raw_text,
                         numeric_value_1, numeric_label_1,
                         numeric_value_2, numeric_label_2,
                         tenant_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        str(uuid.uuid4()),
                        source_file,
                        table_type,
                        table_title or None,
                        row_idx,
                        psycopg2.extras.Json(row_data),
                        raw_text,
                        numerics[0][1] if len(numerics) > 0 else None,
                        numerics[0][0] if len(numerics) > 0 else None,
                        numerics[1][1] if len(numerics) > 1 else None,
                        numerics[1][0] if len(numerics) > 1 else None,
                        self.tenant_id,
                    ))
                    inserted += 1

            self.conn.commit()
            logger.info(f"✅ KV 入库: {source_file} → {table_type}, {inserted} 行")

        except Exception as e:
            self.conn.rollback()
            logger.error(f"KV 入库失败: {e}")
            raise

        return inserted

    def close(self):
        if self._conn and not self._conn.closed:
            self._conn.close()
