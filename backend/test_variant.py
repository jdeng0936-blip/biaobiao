"""
变体引擎 API — 单元测试
覆盖：
  1. VariantConfig / VariantItem Pydantic 模型校验
  2. 变体生成业务逻辑（数量限制/stats 统计/状态分布）
  3. 相似度矩阵对称性
严禁调用外部 API。
"""
import unittest
from pydantic import ValidationError


# ============================================================
# VariantConfig Pydantic 模型测试
# ============================================================
class TestVariantConfig(unittest.TestCase):
    """VariantConfig 数据校验"""

    def test_valid_config(self):
        from app.api.v1.variant import VariantConfig
        cfg = VariantConfig(
            dimensions={"craft": ["明挖法", "顶管法"], "style": ["技术严谨型"]},
            target_count=5,
        )
        self.assertEqual(cfg.target_count, 5)
        self.assertIn("craft", cfg.dimensions)

    def test_default_target_count(self):
        from app.api.v1.variant import VariantConfig
        cfg = VariantConfig(dimensions={"craft": ["明挖法"]})
        self.assertEqual(cfg.target_count, 10)

    def test_optional_source_text(self):
        from app.api.v1.variant import VariantConfig
        cfg = VariantConfig(dimensions={"x": ["a"]})
        self.assertIsNone(cfg.source_text)
        cfg2 = VariantConfig(dimensions={"x": ["a"]}, source_text="原始标书文本")
        self.assertEqual(cfg2.source_text, "原始标书文本")

    def test_missing_dimensions_raises(self):
        from app.api.v1.variant import VariantConfig
        with self.assertRaises(ValidationError):
            VariantConfig(target_count=5)  # 缺 dimensions

    def test_dimensions_must_be_dict(self):
        from app.api.v1.variant import VariantConfig
        with self.assertRaises(ValidationError):
            VariantConfig(dimensions="not_a_dict")


# ============================================================
# VariantItem Pydantic 模型测试
# ============================================================
class TestVariantItem(unittest.TestCase):
    """VariantItem 数据校验"""

    def test_valid_item(self):
        from app.api.v1.variant import VariantItem
        item = VariantItem(
            id="abc12345",
            name="变体 A-01",
            style="技术严谨型+明挖法+传统稳重",
            similarity=12.5,
            score=90.3,
            status="done",
        )
        self.assertEqual(item.status, "done")
        self.assertAlmostEqual(item.similarity, 12.5)

    def test_score_optional(self):
        from app.api.v1.variant import VariantItem
        item = VariantItem(
            id="x", name="y", style="z", similarity=1.0, status="pending"
        )
        self.assertIsNone(item.score)

    def test_missing_required_field(self):
        from app.api.v1.variant import VariantItem
        with self.assertRaises(ValidationError):
            VariantItem(id="x", name="y")  # 缺少 style/similarity/status


# ============================================================
# 变体生成业务逻辑测试
# ============================================================
class TestVariantGeneration(unittest.TestCase):
    """变体生成端点业务逻辑"""

    def test_generate_respects_target_count(self):
        """生成数量 = target_count"""
        import asyncio
        from app.api.v1.variant import generate_variants, VariantConfig

        cfg = VariantConfig(
            dimensions={"craft": ["明挖法"], "style": ["技术严谨型"]},
            target_count=6,
        )
        result = asyncio.run(generate_variants(cfg))
        self.assertEqual(len(result["variants"]), 6)

    def test_generate_max_20(self):
        """生成数量上限 20"""
        import asyncio
        from app.api.v1.variant import generate_variants, VariantConfig

        cfg = VariantConfig(
            dimensions={"craft": ["明挖法"]},
            target_count=50,
        )
        result = asyncio.run(generate_variants(cfg))
        self.assertLessEqual(len(result["variants"]), 20)

    def test_stats_correct(self):
        """统计数据 (done + generating + pending) 正确"""
        import asyncio
        from app.api.v1.variant import generate_variants, VariantConfig

        cfg = VariantConfig(
            dimensions={"craft": ["明挖法"], "style": ["技术严谨型"]},
            target_count=10,
        )
        result = asyncio.run(generate_variants(cfg))
        stats = result["stats"]
        total = stats["done"] + stats["generating"] + stats["pending"]
        self.assertEqual(total, 10)
        self.assertIn("avg_score", stats)

    def test_variant_has_uuid_id(self):
        """变体 ID 是 UUID 前缀"""
        import asyncio
        from app.api.v1.variant import generate_variants, VariantConfig

        cfg = VariantConfig(dimensions={"craft": ["明挖法"]}, target_count=3)
        result = asyncio.run(generate_variants(cfg))
        for v in result["variants"]:
            self.assertEqual(len(v["id"]), 8)

    def test_similarity_in_range(self):
        """相似度在 [4, 18] 范围"""
        import asyncio
        from app.api.v1.variant import generate_variants, VariantConfig

        cfg = VariantConfig(dimensions={"craft": ["明挖法"]}, target_count=5)
        result = asyncio.run(generate_variants(cfg))
        for v in result["variants"]:
            self.assertTrue(4 <= v["similarity"] <= 18)


# ============================================================
# 相似度矩阵测试
# ============================================================
class TestSimilarityMatrix(unittest.TestCase):
    """相似度矩阵"""

    def test_matrix_symmetric(self):
        """矩阵对称"""
        import asyncio
        from app.api.v1.variant import generate_variants, similarity_matrix, VariantConfig

        # 先生成变体（至少 6 个）
        cfg = VariantConfig(dimensions={"craft": ["明挖法"]}, target_count=6)
        asyncio.run(generate_variants(cfg))

        result = asyncio.run(similarity_matrix())
        matrix = result["matrix"]
        n = len(matrix)
        for i in range(n):
            for j in range(n):
                self.assertEqual(matrix[i][j], matrix[j][i])

    def test_matrix_diagonal_zero(self):
        """对角线为零"""
        import asyncio
        from app.api.v1.variant import generate_variants, similarity_matrix, VariantConfig

        cfg = VariantConfig(dimensions={"craft": ["明挖法"]}, target_count=6)
        asyncio.run(generate_variants(cfg))

        result = asyncio.run(similarity_matrix())
        matrix = result["matrix"]
        for i in range(len(matrix)):
            self.assertEqual(matrix[i][i], 0)


if __name__ == "__main__":
    unittest.main()
