"""
API 路由 — 项目 CRUD
提供项目的创建、列表查询、详情获取、更新功能。
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.project import Project


def _parse_uuid(project_id: str) -> uuid.UUID:
    """安全解析 UUID，无效则 404"""
    try:
        return uuid.UUID(project_id)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=404, detail="无效的项目 ID")

router = APIRouter(prefix="/projects", tags=["项目管理"])


# ──────────────────────────── 请求/响应模型 ────────────────────────────

class ProjectCreate(BaseModel):
    """创建项目请求"""
    name: str = Field(..., max_length=300, description="项目名称")
    project_type: str = Field(default="municipal_road", description="项目类型")
    bid_type: str = Field(default="NORMAL_BID_DOC", description="标书类型")
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    """更新项目请求"""
    name: Optional[str] = None
    status: Optional[str] = None
    progress: Optional[int] = None
    generated_sections: Optional[dict] = None
    description: Optional[str] = None


class ProjectOut(BaseModel):
    """项目响应"""
    id: str
    name: str
    project_type: str
    status: str
    description: Optional[str] = None
    progress: int
    generated_sections: Optional[dict] = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


# ──────────────────────────── 接口实现 ────────────────────────────

# 临时 tenant_id（正式环境从 JWT 中提取）
DEMO_TENANT = "demo_tenant"


@router.post("", response_model=ProjectOut)
async def create_project(body: ProjectCreate, db: AsyncSession = Depends(get_db)):
    """新建标书项目"""
    project = Project(
        name=body.name,
        project_type=body.project_type,
        status="draft",
        description=body.description,
        progress=0,
        tenant_id=DEMO_TENANT,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return _to_out(project)


@router.get("", response_model=list[ProjectOut])
async def list_projects(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """获取项目列表（支持按状态过滤）"""
    stmt = select(Project).where(Project.tenant_id == DEMO_TENANT)
    if status:
        stmt = stmt.where(Project.status == status)
    stmt = stmt.order_by(Project.updated_at.desc())
    result = await db.execute(stmt)
    projects = result.scalars().all()
    return [_to_out(p) for p in projects]


@router.get("/stats")
async def project_stats(db: AsyncSession = Depends(get_db)):
    """项目统计数据（供 Dashboard 使用）"""
    # 总项目数
    total = await db.scalar(
        select(func.count()).select_from(Project).where(Project.tenant_id == DEMO_TENANT)
    )
    # 进行中
    in_progress = await db.scalar(
        select(func.count()).select_from(Project).where(
            Project.tenant_id == DEMO_TENANT,
            Project.status.in_(["draft", "generating", "reviewing"]),
        )
    )
    # 已完成
    completed = await db.scalar(
        select(func.count()).select_from(Project).where(
            Project.tenant_id == DEMO_TENANT,
            Project.status == "completed",
        )
    )
    return {
        "total": total or 0,
        "in_progress": in_progress or 0,
        "completed": completed or 0,
    }


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    """获取单个项目详情"""
    result = await db.execute(
        select(Project).where(
            Project.id == _parse_uuid(project_id),
            Project.tenant_id == DEMO_TENANT,
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return _to_out(project)


@router.put("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: str,
    body: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新项目信息"""
    # 先查出来
    result = await db.execute(
        select(Project).where(
            Project.id == _parse_uuid(project_id),
            Project.tenant_id == DEMO_TENANT,
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 更新非 None 字段
    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)
    project.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(project)
    return _to_out(project)


@router.delete("/{project_id}")
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)):
    """删除项目"""
    result = await db.execute(
        select(Project).where(
            Project.id == _parse_uuid(project_id),
            Project.tenant_id == DEMO_TENANT,
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    await db.delete(project)
    await db.commit()
    return {"detail": "项目已删除"}


# ──────────────────────────── 工具函数 ────────────────────────────

def _to_out(p: Project) -> ProjectOut:
    """ORM → Pydantic 转换"""
    return ProjectOut(
        id=str(p.id),
        name=p.name,
        project_type=p.project_type,
        status=p.status,
        description=p.description,
        progress=p.progress,
        generated_sections=p.generated_sections,
        created_at=p.created_at.isoformat() if p.created_at else "",
        updated_at=p.updated_at.isoformat() if p.updated_at else "",
    )
