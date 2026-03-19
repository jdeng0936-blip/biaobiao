"""
StorageBackend 存储层单元测试
覆盖：
  1. StorageBackend 抽象接口约束
  2. LocalStorage CRUD（upload/download/delete/exists）
  3. OSSStorage 未配置时的行为
  4. 工厂函数 get_storage_backend 自动选择
严禁调用真实 OSS/S3。
"""
import asyncio
import unittest
from unittest.mock import patch
from pathlib import Path
import tempfile
import shutil


# ============================================================
# StorageBackend 抽象接口测试
# ============================================================
class TestStorageBackendInterface(unittest.TestCase):
    """StorageBackend 抽象接口"""

    def test_cannot_instantiate_directly(self):
        from app.services.storage_backend import StorageBackend
        with self.assertRaises(TypeError):
            StorageBackend()


# ============================================================
# LocalStorage 测试
# ============================================================
class TestLocalStorage(unittest.TestCase):
    """LocalStorage 文件系统存储"""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        from app.services.storage_backend import LocalStorage
        self.storage = LocalStorage(base_dir=self.tmp_dir)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_upload_and_download(self):
        """上传后可下载"""
        data = b"test content for upload"
        url = asyncio.run(self.storage.upload(data, "docs/test.pdf"))
        self.assertIn("test.pdf", url)

        downloaded = asyncio.run(self.storage.download("docs/test.pdf"))
        self.assertEqual(downloaded, data)

    def test_exists_after_upload(self):
        """上传后 exists 返回 True"""
        asyncio.run(self.storage.upload(b"data", "check/file.txt"))
        self.assertTrue(asyncio.run(self.storage.exists("check/file.txt")))

    def test_not_exists_before_upload(self):
        """未上传时 exists 返回 False"""
        self.assertFalse(asyncio.run(self.storage.exists("no/such/file.txt")))

    def test_delete(self):
        """删除文件"""
        asyncio.run(self.storage.upload(b"data", "del/file.txt"))
        result = asyncio.run(self.storage.delete("del/file.txt"))
        self.assertTrue(result)
        self.assertFalse(asyncio.run(self.storage.exists("del/file.txt")))

    def test_delete_nonexistent(self):
        """删除不存在的文件返回 False"""
        result = asyncio.run(self.storage.delete("no/file.txt"))
        self.assertFalse(result)

    def test_download_nonexistent_raises(self):
        """下载不存在的文件抛出 FileNotFoundError"""
        with self.assertRaises(FileNotFoundError):
            asyncio.run(self.storage.download("no/file.txt"))

    def test_nested_directory_creation(self):
        """嵌套目录自动创建"""
        asyncio.run(self.storage.upload(b"nested", "a/b/c/d/file.txt"))
        self.assertTrue(asyncio.run(self.storage.exists("a/b/c/d/file.txt")))

    def test_upload_returns_url(self):
        """上传返回 file:// URL"""
        url = asyncio.run(self.storage.upload(b"x", "url_test.txt"))
        self.assertTrue(url.startswith("file://"))


# ============================================================
# OSSStorage 测试
# ============================================================
class TestOSSStorage(unittest.TestCase):
    """OSSStorage 对象存储（未接入 SDK）"""

    def test_upload_raises_not_implemented(self):
        from app.services.storage_backend import OSSStorage
        oss = OSSStorage()
        with self.assertRaises(NotImplementedError):
            asyncio.run(oss.upload(b"data", "test.pdf"))

    def test_download_raises_not_implemented(self):
        from app.services.storage_backend import OSSStorage
        oss = OSSStorage()
        with self.assertRaises(NotImplementedError):
            asyncio.run(oss.download("test.pdf"))


# ============================================================
# 工厂函数测试
# ============================================================
class TestGetStorageBackend(unittest.TestCase):
    """get_storage_backend 工厂"""

    def test_default_is_local(self):
        """无 OSS 环境变量时默认 LocalStorage"""
        import app.services.storage_backend as mod
        mod._storage = None  # 重置单例
        with patch.dict("os.environ", {}, clear=False):
            # 确保没有 OSS 相关变量
            import os
            os.environ.pop("OSS_BUCKET_NAME", None)
            os.environ.pop("S3_BUCKET_NAME", None)
            backend = mod.get_storage_backend()
            from app.services.storage_backend import LocalStorage
            self.assertIsInstance(backend, LocalStorage)
        mod._storage = None  # 清理

    def test_oss_when_configured(self):
        """有 OSS_BUCKET_NAME 时选择 OSSStorage"""
        import app.services.storage_backend as mod
        mod._storage = None
        with patch.dict("os.environ", {"OSS_BUCKET_NAME": "test-bucket"}, clear=False):
            backend = mod.get_storage_backend()
            from app.services.storage_backend import OSSStorage
            self.assertIsInstance(backend, OSSStorage)
        mod._storage = None


if __name__ == "__main__":
    unittest.main()
