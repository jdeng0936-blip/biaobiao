"""
文件上传与解析 API 路由
支持 PDF/Word 上传 → 异步切片入库
"""
import os
import tempfile
import logging

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from pydantic import BaseModel

from app.core.deps import get_tenant_id

logger = logging.getLogger("upload_api")

router = APIRouter(prefix="/api/v1/upload", tags=["文件上传"])

# 允许的文件类型
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx"}
# 最大文件大小 50MB
MAX_FILE_SIZE = 50 * 1024 * 1024


@router.post("/document")
async def upload_document(
    file: UploadFile = File(...),
    tenant_id: str = Depends(get_tenant_id),
):
    """
    📤 上传招标/标书文件

    支持 PDF 格式。上传后自动执行：
    1. 文本提取
    2. 表格检测 → structured_tables
    3. 章节切片 → training_chunks
    4. 自动分类打标签
    """
    # 验证文件类型
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {ext}。仅支持: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # 读取文件内容
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件大小超过 50MB 限制")

    # 保存临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # 动态加载 scripts/chunking_pipeline.py（不污染 sys.path）
        import importlib.util
        _script_path = os.path.join(
            os.path.dirname(__file__), '..', '..', '..', 'scripts', 'chunking_pipeline.py'
        )
        _spec = importlib.util.spec_from_file_location("chunking_pipeline", _script_path)
        _module = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_module)
        ChunkingPipeline = _module.ChunkingPipeline

        db_url = os.getenv(
            "DATABASE_URL",
            "postgresql://mac111@localhost:5432/biaobiao"
        )

        # 开启真实的 Gemini 向量化存入 pgvector
        pipeline = ChunkingPipeline(
            max_chunk_size=800,
            min_chunk_size=100,
            vectorize=True,
            engine="gemini",
            db_url=db_url,
            tenant_id=tenant_id,
        )

        chunks = pipeline.process_file(tmp_path)
        pipeline.close()

        return {
            "filename": file.filename,
            "file_size": len(content),
            "chunks_created": len(chunks),
            "message": f"✅ 文件处理完成: {len(chunks)} 个知识片段已入库",
        }

    except Exception as e:
        logger.error(f"文件处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"文件处理失败: {str(e)}")
    finally:
        # 清理临时文件
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
