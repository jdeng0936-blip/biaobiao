"""
数据管道单元测试 — 表格入库 + 切片管道
覆盖：
  1. TableIngestionService: detect_table_type / extract_numeric_values
  2. ChapterChunker: 章节切片逻辑
  3. Desensitizer: NER 脱敏规则
  4. AutoTagger: 分类标签 + 工艺标签 + 数据密度评估
严禁连接真实数据库。
"""
import unittest


# ============================================================
# TableIngestionService 纯逻辑测试
# ============================================================
class TestDetectTableType(unittest.TestCase):
    """表格类型推断"""

    def _svc(self):
        from app.services.table_ingestion import TableIngestionService
        svc = TableIngestionService.__new__(TableIngestionService)
        return svc

    def test_bill_of_quantities(self):
        svc = self._svc()
        t = svc.detect_table_type(["序号", "工程量清单编号", "分部分项工程", "综合单价", "合价"])
        self.assertEqual(t, "bill_of_quantities")

    def test_mix_ratio(self):
        svc = self._svc()
        t = svc.detect_table_type(["混凝土强度", "水灰比", "砂率", "用量"], "C30配合比表")
        self.assertEqual(t, "mix_ratio")

    def test_inspection_batch(self):
        svc = self._svc()
        t = svc.detect_table_type(["检验批编号", "验收日期", "质量检查"], "检验批记录")
        self.assertEqual(t, "inspection_batch")

    def test_material_list(self):
        svc = self._svc()
        t = svc.detect_table_type(["材料名称", "规格型号", "单位", "数量"])
        self.assertEqual(t, "material_list")

    def test_schedule(self):
        svc = self._svc()
        t = svc.detect_table_type(["工期安排", "节点名称", "计划开工", "里程碑"])
        self.assertEqual(t, "schedule")

    def test_unknown(self):
        svc = self._svc()
        t = svc.detect_table_type(["abc", "xyz", "123"])
        self.assertEqual(t, "unknown")


class TestExtractNumericValues(unittest.TestCase):
    """数值提取"""

    def _svc(self):
        from app.services.table_ingestion import TableIngestionService
        svc = TableIngestionService.__new__(TableIngestionService)
        return svc

    def test_basic_extraction(self):
        svc = self._svc()
        numerics = svc.extract_numeric_values({"水泥用量": "380kg/m³", "强度等级": "C30"})
        self.assertEqual(len(numerics), 2)
        self.assertEqual(numerics[0][1], 380.0)
        self.assertEqual(numerics[1][1], 30.0)

    def test_max_two(self):
        svc = self._svc()
        numerics = svc.extract_numeric_values({"a": "1", "b": "2", "c": "3"})
        self.assertEqual(len(numerics), 2)  # 最多 2 个

    def test_empty(self):
        svc = self._svc()
        numerics = svc.extract_numeric_values({})
        self.assertEqual(len(numerics), 0)

    def test_none_value(self):
        svc = self._svc()
        numerics = svc.extract_numeric_values({"a": None, "b": "没有数字"})
        self.assertEqual(len(numerics), 0)


# ============================================================
# ChapterChunker 测试
# ============================================================
class TestChapterChunker(unittest.TestCase):
    """章节切片"""

    def _chunker(self, max_size=800, min_size=50):
        from scripts.chunking_pipeline import ChapterChunker
        return ChapterChunker(max_chunk_size=max_size, min_chunk_size=min_size)

    def test_basic_chunking(self):
        chunker = self._chunker(min_size=10)
        pages = [
            {"page": 1, "text": "第一章 工程概况\n\n本工程位于合肥市，总建筑面积约5万平方米。"},
            {"page": 2, "text": "第二章 施工方案\n\n采用明挖法施工，基坑深度约8米。"},
        ]
        chunks = chunker.chunk(pages)
        self.assertGreater(len(chunks), 0)

    def test_chapter_detection(self):
        chunker = self._chunker(min_size=10)
        pages = [
            {"page": 1, "text": "第一章 总体部署\n\n施工总体部署内容"},
            {"page": 2, "text": "第二章 施工准备\n\n施工准备工作内容"},
        ]
        chunks = chunker.chunk(pages)
        titles = [c["chapter"] for c in chunks]
        self.assertTrue(any("总体部署" in t for t in titles))

    def test_max_size_split(self):
        chunker = self._chunker(max_size=50, min_size=10)
        # 用 \n\n 段落分隔触发切片
        long_text = "\n\n".join([f"这是第{i}个测试段落，包含足够的内容。" for i in range(20)])
        pages = [{"page": 1, "text": long_text}]
        chunks = chunker.chunk(pages)
        self.assertGreater(len(chunks), 1)

    def test_empty_pages(self):
        chunker = self._chunker()
        chunks = chunker.chunk([])
        self.assertEqual(len(chunks), 0)


# ============================================================
# Desensitizer 测试
# ============================================================
class TestDesensitizer(unittest.TestCase):
    """NER 脱敏"""

    def _desensitizer(self):
        from scripts.chunking_pipeline import Desensitizer
        return Desensitizer()

    def test_phone_desensitize(self):
        d = self._desensitizer()
        result = d.desensitize("联系人电话: 13812345678")
        self.assertNotIn("13812345678", result)
        self.assertIn("[联系电话]", result)

    def test_id_card_desensitize(self):
        d = self._desensitizer()
        # 使用不会被手机号规则误匹配的身份证号
        result = d.desensitize("身份证: 320102200001011234")
        self.assertNotIn("320102200001011234", result)
        self.assertIn("[身份证号]", result)

    def test_amount_desensitize(self):
        d = self._desensitizer()
        result = d.desensitize("合同金额为3500万元")
        self.assertIn("[金额]", result)

    def test_filename_desensitize(self):
        d = self._desensitizer()
        result = d.desensitize_filename("中建科工-2024AB1234-施工方案.pdf")
        self.assertNotIn("中建科工", result)

    def test_no_false_positive(self):
        d = self._desensitizer()
        text = "混凝土强度等级C30，抗渗等级P6。"
        result = d.desensitize(text)
        self.assertIn("C30", result)
        self.assertIn("P6", result)


# ============================================================
# AutoTagger 测试
# ============================================================
class TestAutoTagger(unittest.TestCase):
    """自动分类标签"""

    def _tagger(self):
        from scripts.chunking_pipeline import AutoTagger
        return AutoTagger()

    def test_project_type_road(self):
        tagger = self._tagger()
        result = tagger.tag("道路路基施工完成后进行沥青摊铺")
        self.assertTrue(any("市政-道路" in pt for pt in result["project_type"]))

    def test_project_type_building(self):
        tagger = self._tagger()
        result = tagger.tag("主体结构框架柱浇筑完成")
        self.assertTrue(any("房建" in pt for pt in result["project_type"]))

    def test_doc_section_quality(self):
        tagger = self._tagger()
        result = tagger.tag("质量通病防治措施，验收标准")
        self.assertEqual(result["doc_section"], "quality")

    def test_doc_section_safety(self):
        tagger = self._tagger()
        result = tagger.tag("安全管理制度，危大工程专项方案")
        self.assertEqual(result["doc_section"], "safety")

    def test_craft_tags(self):
        tagger = self._tagger()
        result = tagger.tag("混凝土浇筑后及时振捣养护，使用盘扣式脚手架")
        self.assertIn("混凝土", result["craft_tags"])
        self.assertIn("模板工程", result["craft_tags"])

    def test_data_density_high(self):
        tagger = self._tagger()
        text = "压实度≥96%, 沥青温度120℃, 厚度50mm, 宽度3.5m, 碾压速度2km/h, 含水率8%, 弯沉值20mm, 回弹模量300MPa"
        result = tagger.tag(text)
        self.assertEqual(result["data_density"], "high")
        self.assertTrue(result["has_params"])

    def test_data_density_low(self):
        tagger = self._tagger()
        result = tagger.tag("施工组织设计应根据工程特点编制")
        self.assertEqual(result["data_density"], "low")
        self.assertFalse(result["has_params"])

    def test_unknown_project_type(self):
        tagger = self._tagger()
        result = tagger.tag("这是一段无关内容")
        self.assertIn("未分类", result["project_type"])


if __name__ == "__main__":
    unittest.main()
