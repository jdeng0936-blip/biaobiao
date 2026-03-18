"""
统一脱敏网关
入库和在线共用同一套脱敏映射表（共识 #1）

核心链路：
  用户输入 → mask() → 云端 LLM → unmask() → 前端展示

支持的实体类型：
  - project: 项目名称
  - person: 人员姓名
  - amount: 金额数值
  - address: 地址信息
  - phone: 电话号码
  - org: 组织机构名
"""
import re
import logging
from typing import Optional

import psycopg2
import psycopg2.extras
import os

logger = logging.getLogger("desensitize_service")

# 实体类型 → 占位符前缀映射
_ENTITY_PREFIX = {
    "project": "PROJECT",
    "person": "PERSON",
    "amount": "AMOUNT",
    "address": "ADDR",
    "phone": "PHONE",
    "org": "ORG",
}

# 常见的中文项目名/人名/地址正则模式
_PATTERNS = {
    # 项目名：XX工程/XX项目/XX改造
    "project": re.compile(
        r'[A-Za-z\u4e00-\u9fa5]{2,20}(?:市|县|区|镇|乡|街道)?'
        r'[A-Za-z\u4e00-\u9fa5]{2,30}'
        r'(?:工程|项目|改造|建设|施工|标段)',
    ),
    # 金额：¥1,234.56 / 123.45万元 / 1234元
    "amount": re.compile(
        r'(?:¥|￥)?\s*[\d,]+(?:\.\d{1,2})?\s*(?:万元|亿元|元|千元)?'
        r'|[\d,]+(?:\.\d{1,2})?\s*(?:万元|亿元)',
    ),
    # 电话号码
    "phone": re.compile(
        r'1[3-9]\d{9}'
        r'|0\d{2,3}-?\d{7,8}',
    ),
}


class DesensitizeGateway:
    """
    统一脱敏网关

    用法:
        gateway = DesensitizeGateway(tenant_id="xxx")
        masked_text, mapping = gateway.mask(raw_text)
        # ... 发送 masked_text 到 LLM ...
        final_text = gateway.unmask(llm_output, mapping)
    """

    def __init__(self, tenant_id: str = "default"):
        self.tenant_id = tenant_id
        self.db_url = os.getenv(
            "DATABASE_URL",
            "postgresql://mac111@localhost:5432/biaobiao"
        )
        self._conn = None
        # 内存缓存当前 tenant 的词典
        self._dict_cache: dict[str, str] = {}  # original → placeholder
        self._reverse_cache: dict[str, str] = {}  # placeholder → original
        self._counter: dict[str, int] = {}  # 每种类型的计数器
        self._load_dict()

    @property
    def conn(self):
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(self.db_url.replace("+asyncpg", ""))
        return self._conn

    def _load_dict(self):
        """从数据库加载当前租户的脱敏词典到内存"""
        try:
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT original_text, placeholder, entity_type FROM desensitize_dict WHERE tenant_id = %s",
                    (self.tenant_id,),
                )
                for row in cur.fetchall():
                    self._dict_cache[row["original_text"]] = row["placeholder"]
                    self._reverse_cache[row["placeholder"]] = row["original_text"]
                    # 更新计数器
                    entity_type = row["entity_type"]
                    prefix = _ENTITY_PREFIX.get(entity_type, entity_type.upper())
                    # 从占位符提取序号（如 [PROJECT_3] → 3）
                    match = re.search(r'_(\d+)\]$', row["placeholder"])
                    if match:
                        idx = int(match.group(1))
                        self._counter[entity_type] = max(
                            self._counter.get(entity_type, 0), idx
                        )

            logger.info(f"📖 脱敏词典加载完成: {len(self._dict_cache)} 条 (tenant={self.tenant_id})")
        except Exception as e:
            logger.warning(f"脱敏词典加载失败: {e}")

    def _get_or_create_placeholder(self, original: str, entity_type: str) -> str:
        """获取或创建占位符"""
        # 已在词典中
        if original in self._dict_cache:
            return self._dict_cache[original]

        # 生成新占位符
        prefix = _ENTITY_PREFIX.get(entity_type, entity_type.upper())
        self._counter[entity_type] = self._counter.get(entity_type, 0) + 1
        placeholder = f"[{prefix}_{self._counter[entity_type]}]"

        # 写入数据库
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO desensitize_dict (original_text, placeholder, entity_type, tenant_id)
                       VALUES (%s, %s, %s, %s)
                       ON CONFLICT DO NOTHING""",
                    (original, placeholder, entity_type, self.tenant_id),
                )
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            logger.warning(f"写入脱敏词典失败: {e}")

        # 更新缓存
        self._dict_cache[original] = placeholder
        self._reverse_cache[placeholder] = original

        return placeholder

    def mask(self, text: str, extra_entities: dict[str, str] = None) -> tuple[str, dict[str, str]]:
        """
        脱敏：将敏感信息替换为占位符

        参数:
            text: 原始文本
            extra_entities: 额外的手动指定实体 {"原文": "类型"}

        返回:
            (脱敏后文本, 映射表 {占位符: 原文})
        """
        mapping = {}
        masked = text

        # 1. 先处理手动指定的实体（优先级最高）
        if extra_entities:
            for original, entity_type in extra_entities.items():
                if original and original in masked:
                    placeholder = self._get_or_create_placeholder(original, entity_type)
                    masked = masked.replace(original, placeholder)
                    mapping[placeholder] = original

        # 2. 再用已有词典做全局替换（按长度降序，避免短匹配覆盖长匹配）
        sorted_entries = sorted(
            self._dict_cache.items(),
            key=lambda x: len(x[0]),
            reverse=True,
        )
        for original, placeholder in sorted_entries:
            if original in masked and placeholder not in mapping:
                masked = masked.replace(original, placeholder)
                mapping[placeholder] = original

        # 3. 正则自动发现新实体
        for entity_type, pattern in _PATTERNS.items():
            for match in pattern.finditer(masked):
                found = match.group().strip()
                # 跳过已经是占位符的内容
                if found.startswith("[") and found.endswith("]"):
                    continue
                # 跳过太短的匹配
                if len(found) < 3:
                    continue
                placeholder = self._get_or_create_placeholder(found, entity_type)
                masked = masked.replace(found, placeholder)
                mapping[placeholder] = found

        return masked, mapping

    def unmask(self, text: str, mapping: dict[str, str] = None) -> str:
        """
        回填：将占位符替换回原始值

        参数:
            text: LLM 输出的含占位符文本
            mapping: mask() 返回的映射表（可选，不传则用全局词典）
        """
        result = text

        # 优先用传入的 mapping
        if mapping:
            for placeholder, original in mapping.items():
                result = result.replace(placeholder, original)

        # 再用全局词典补充回填
        for placeholder, original in self._reverse_cache.items():
            if placeholder in result:
                result = result.replace(placeholder, original)

        return result

    def get_dict_stats(self) -> dict:
        """获取词典统计"""
        stats = {}
        for original, placeholder in self._dict_cache.items():
            for entity_type, prefix in _ENTITY_PREFIX.items():
                if f"[{prefix}_" in placeholder:
                    stats[entity_type] = stats.get(entity_type, 0) + 1
                    break
        return {
            "total": len(self._dict_cache),
            "by_type": stats,
            "tenant_id": self.tenant_id,
        }

    def close(self):
        if self._conn and not self._conn.closed:
            self._conn.close()
