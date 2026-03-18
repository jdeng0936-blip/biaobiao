"""
标书导出 API 路由
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.services.export_service import BidExportService

router = APIRouter(prefix="/api/v1/export", tags=["导出"])

# 服务单例
_service: BidExportService | None = None


def get_service() -> BidExportService:
    global _service
    if _service is None:
        _service = BidExportService()
    return _service


# ============================================================
# 请求模型
# ============================================================
class ExportWordRequest(BaseModel):
    """Word 导出请求"""
    project_name: str = Field(..., min_length=2, max_length=300, description="项目名称")
    company_name: str = Field(default="", max_length=200, description="投标公司名")
    sections: dict[str, str] = Field(..., description="章节标题→内容映射")


# ============================================================
# API 端点
# ============================================================
@router.post("/word")
async def export_word(req: ExportWordRequest):
    """
    📄 导出标书为 Word 文档

    将已生成的标书章节内容导出为 .docx 文件。
    包含：封面、目录占位、章节排版（中文编号、首行缩进）、页眉页脚。
    """
    if not req.sections:
        raise HTTPException(status_code=400, detail="章节内容不能为空")

    service = get_service()
    try:
        docx_bytes = service.export_document(
            project_name=req.project_name,
            sections=req.sections,
            company_name=req.company_name,
        )

        # 文件名安全处理
        safe_name = req.project_name.replace("/", "_").replace("\\", "_")[:50]
        filename = f"{safe_name}_投标文件.docx"

        return Response(
            content=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")
