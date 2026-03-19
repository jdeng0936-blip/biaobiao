"""
存储后端抽象层（二进制零入库合规）

开发环境使用 LocalStorage（文件系统），
生产环境配置 OSSStorage（阿里云/AWS S3）。

用法：
    storage = get_storage_backend()
    url = await storage.upload(file_bytes, "documents/xxx.pdf")
    content = await storage.download("documents/xxx.pdf")
"""
import os
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

logger = logging.getLogger("storage")


class StorageBackend(ABC):
    """存储后端抽象接口"""

    @abstractmethod
    async def upload(self, data: bytes, key: str, content_type: str = "") -> str:
        """
        上传二进制数据，返回访问 URL。
        - data: 文件二进制内容
        - key: 存储路径/键名，如 "documents/abc123.pdf"
        - content_type: MIME 类型
        - return: 文件访问 URL
        """
        ...

    @abstractmethod
    async def download(self, key: str) -> bytes:
        """根据 key 下载文件内容"""
        ...

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """删除文件，返回是否成功"""
        ...

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """检查文件是否存在"""
        ...


class LocalStorage(StorageBackend):
    """本地文件系统存储（开发环境）"""

    def __init__(self, base_dir: str = "/tmp/biaobiao_storage"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"📂 LocalStorage 已初始化: {self.base_dir}")

    def _resolve(self, key: str) -> Path:
        path = self.base_dir / key
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    async def upload(self, data: bytes, key: str, content_type: str = "") -> str:
        path = self._resolve(key)
        path.write_bytes(data)
        url = f"file://{path.absolute()}"
        logger.info(f"📤 LocalStorage 上传: {key} ({len(data)} bytes)")
        return url

    async def download(self, key: str) -> bytes:
        path = self._resolve(key)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {key}")
        return path.read_bytes()

    async def delete(self, key: str) -> bool:
        path = self._resolve(key)
        if path.exists():
            path.unlink()
            return True
        return False

    async def exists(self, key: str) -> bool:
        return self._resolve(key).exists()


class OSSStorage(StorageBackend):
    """
    OSS / S3 对象存储（生产环境）

    需要环境变量：
    - OSS_ENDPOINT / AWS_S3_ENDPOINT
    - OSS_ACCESS_KEY_ID / AWS_ACCESS_KEY_ID
    - OSS_ACCESS_KEY_SECRET / AWS_SECRET_ACCESS_KEY
    - OSS_BUCKET_NAME / S3_BUCKET_NAME
    """

    def __init__(self):
        self.bucket_name = os.getenv("OSS_BUCKET_NAME", os.getenv("S3_BUCKET_NAME", ""))
        self.endpoint = os.getenv("OSS_ENDPOINT", os.getenv("AWS_S3_ENDPOINT", ""))
        # 实际集成时使用 boto3 / oss2 客户端
        self._client = None
        if self.bucket_name and self.endpoint:
            logger.info(f"☁️ OSSStorage 已初始化: {self.endpoint}/{self.bucket_name}")
        else:
            logger.warning("⚠️ OSSStorage 环境变量未配置，上传将失败")

    async def upload(self, data: bytes, key: str, content_type: str = "") -> str:
        # TODO: 接入真实 OSS/S3 SDK
        raise NotImplementedError(
            "OSSStorage.upload 尚未接入真实 SDK。"
            "请配置 OSS_ENDPOINT / OSS_BUCKET_NAME 并安装 oss2 或 boto3。"
        )

    async def download(self, key: str) -> bytes:
        raise NotImplementedError("OSSStorage.download 尚未接入真实 SDK")

    async def delete(self, key: str) -> bool:
        raise NotImplementedError("OSSStorage.delete 尚未接入真实 SDK")

    async def exists(self, key: str) -> bool:
        raise NotImplementedError("OSSStorage.exists 尚未接入真实 SDK")


# ============================================================
# 工厂函数
# ============================================================
_storage: Optional[StorageBackend] = None


def get_storage_backend() -> StorageBackend:
    """获取存储后端全局单例（根据环境变量自动选择）"""
    global _storage
    if _storage is None:
        if os.getenv("OSS_BUCKET_NAME") or os.getenv("S3_BUCKET_NAME"):
            _storage = OSSStorage()
        else:
            _storage = LocalStorage()
    return _storage
