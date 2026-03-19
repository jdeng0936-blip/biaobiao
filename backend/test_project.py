"""
项目管理 API — 单元测试
覆盖：_parse_uuid / ProjectCreate / ProjectUpdate / ProjectOut / 工具函数
采用延迟导入防止环境无 fastapi 时整个文件收集失败。
"""
import unittest
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

# 检测 fastapi 是否可用
try:
    import fastapi  # noqa: F401
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

SKIP_MSG = "fastapi 未安装，跳过项目 API 测试"


@unittest.skipUnless(HAS_FASTAPI, SKIP_MSG)
class TestParseUUID(unittest.TestCase):
    """_parse_uuid 辅助函数测试"""

    def test_valid_uuid(self):
        from app.api.v1.project import _parse_uuid
        test_id = str(uuid.uuid4())
        result = _parse_uuid(test_id)
        self.assertEqual(str(result), test_id)

    def test_invalid_uuid_raises_404(self):
        from app.api.v1.project import _parse_uuid
        from fastapi import HTTPException
        with self.assertRaises(HTTPException) as ctx:
            _parse_uuid("not-a-uuid")
        self.assertEqual(ctx.exception.status_code, 404)
        self.assertIn("无效", ctx.exception.detail)

    def test_empty_string_raises_404(self):
        from app.api.v1.project import _parse_uuid
        from fastapi import HTTPException
        with self.assertRaises(HTTPException) as ctx:
            _parse_uuid("")
        self.assertEqual(ctx.exception.status_code, 404)

    def test_none_raises_404(self):
        from app.api.v1.project import _parse_uuid
        from fastapi import HTTPException
        with self.assertRaises(HTTPException):
            _parse_uuid(None)  # type: ignore


@unittest.skipUnless(HAS_FASTAPI, SKIP_MSG)
class TestProjectModels(unittest.TestCase):
    """Pydantic 请求/响应模型验证"""

    def test_create_defaults(self):
        from app.api.v1.project import ProjectCreate
        body = ProjectCreate(name="测试项目")
        self.assertEqual(body.project_type, "municipal_road")
        self.assertEqual(body.bid_type, "NORMAL_BID_DOC")
        self.assertIsNone(body.description)

    def test_create_name_required(self):
        from app.api.v1.project import ProjectCreate
        from pydantic import ValidationError
        with self.assertRaises(ValidationError):
            ProjectCreate()  # type: ignore

    def test_update_all_optional(self):
        from app.api.v1.project import ProjectUpdate
        body = ProjectUpdate()
        self.assertIsNone(body.name)
        self.assertIsNone(body.status)
        self.assertIsNone(body.progress)

    def test_update_partial(self):
        from app.api.v1.project import ProjectUpdate
        body = ProjectUpdate(status="completed", progress=100)
        self.assertEqual(body.status, "completed")
        self.assertEqual(body.progress, 100)
        self.assertIsNone(body.name)

    def test_out_model_format(self):
        from app.api.v1.project import ProjectOut
        now = datetime.now(timezone.utc)
        out = ProjectOut(
            id=str(uuid.uuid4()),
            name="测试",
            project_type="building",
            status="draft",
            progress=0,
            created_at=now.isoformat(),
            updated_at=now.isoformat(),
        )
        self.assertEqual(out.status, "draft")
        self.assertIsNone(out.description)
        self.assertIsNone(out.generated_sections)


@unittest.skipUnless(HAS_FASTAPI, SKIP_MSG)
class TestToOut(unittest.TestCase):
    """_to_out 转换函数测试"""

    def test_converts_orm_to_pydantic(self):
        from app.api.v1.project import _to_out
        mock_project = MagicMock()
        mock_project.id = uuid.uuid4()
        mock_project.name = "市政道路项目"
        mock_project.project_type = "municipal_road"
        mock_project.status = "generating"
        mock_project.description = "测试描述"
        mock_project.progress = 50
        mock_project.generated_sections = {"s1": "内容"}
        mock_project.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        mock_project.updated_at = datetime(2024, 6, 1, tzinfo=timezone.utc)

        result = _to_out(mock_project)
        self.assertEqual(result.name, "市政道路项目")
        self.assertEqual(result.progress, 50)
        self.assertEqual(result.status, "generating")
        self.assertIn("2024-01-01", result.created_at)

    def test_handles_none_timestamps(self):
        from app.api.v1.project import _to_out
        mock_project = MagicMock()
        mock_project.id = uuid.uuid4()
        mock_project.name = "空时间项目"
        mock_project.project_type = "bridge"
        mock_project.status = "draft"
        mock_project.description = None
        mock_project.progress = 0
        mock_project.generated_sections = None
        mock_project.created_at = None
        mock_project.updated_at = None

        result = _to_out(mock_project)
        self.assertEqual(result.created_at, "")
        self.assertEqual(result.updated_at, "")


if __name__ == "__main__":
    unittest.main()
