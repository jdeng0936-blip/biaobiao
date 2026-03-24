"""
合规审查 API 路由 — 独立合规检查接口

支持:
  - 单章节合规检查
  - 批量全文合规检查
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from app.core.deps import get_tenant_id
from app.services.compliance_service import (
    ComplianceService, ComplianceContext, Severity
)

router = APIRouter(prefix="/api/v1/compliance", tags=["合规审查"])


# ============================================================
# 请求/响应模型
# ============================================================
class ComplianceCheckRequest(BaseModel):
    """单章节合规检查请求"""
    content: str = Field(..., min_length=10, description="待检查的章节内容")
    section_title: str = Field(default="", description="章节标题")
    project_name: str = Field(default="", description="项目名称")
    company_name: str = Field(default="", description="投标公司名")
    project_type: str = Field(default="", description="工程类型")
    scoring_points: list[str] = Field(default=[], description="评分点列表")
    min_word_count: int = Field(default=500, ge=0, description="最低字数要求")
    timeline_days: Optional[int] = Field(default=None, description="招标要求工期(天)")


class BatchComplianceRequest(BaseModel):
    """批量合规检查请求"""
    sections: dict[str, str] = Field(..., description="章节标题→内容映射")
    project_name: str = Field(default="", description="项目名称")
    company_name: str = Field(default="", description="投标公司名")
    project_type: str = Field(default="", description="工程类型")
    scoring_points: list[str] = Field(default=[], description="评分点列表")


class IssueResponse(BaseModel):
    """单个问题"""
    severity: str
    category: str
    message: str
    location: str = ""
    suggestion: str = ""


class ComplianceCheckResponse(BaseModel):
    """合规检查响应"""
    passed: bool
    score: float
    summary: str
    issues: list[IssueResponse]
    critical_count: int
    warning_count: int


class BatchComplianceResponse(BaseModel):
    """批量检查响应"""
    overall_passed: bool
    overall_score: float
    sections: dict[str, ComplianceCheckResponse]


# ============================================================
# API 端点
# ============================================================
@router.post("/check", response_model=ComplianceCheckResponse)
async def check_compliance(
    req: ComplianceCheckRequest,
    tenant_id: str = Depends(get_tenant_id),
):
    """
    🔍 单章节合规检查

    三级检查：L1 格式规范 → L2 内容合规 → L3 废标预警
    """
    service = ComplianceService(tenant_id=tenant_id)
    context = ComplianceContext(
        project_name=req.project_name,
        company_name=req.company_name,
        project_type=req.project_type,
        scoring_points=req.scoring_points,
        min_word_count=req.min_word_count,
        timeline_days=req.timeline_days,
    )

    result = await service.check(req.content, context)

    return ComplianceCheckResponse(
        passed=result.passed,
        score=result.score,
        summary=result.summary,
        issues=[
            IssueResponse(
                severity=i.severity.value,
                category=i.category.value,
                message=i.message,
                location=i.location,
                suggestion=i.suggestion,
            )
            for i in result.issues
        ],
        critical_count=len(result.critical_issues),
        warning_count=len(result.warning_issues),
    )


@router.post("/check-batch", response_model=BatchComplianceResponse)
async def check_compliance_batch(
    req: BatchComplianceRequest,
    tenant_id: str = Depends(get_tenant_id),
):
    """
    🔍 批量合规检查 — 全部章节

    对每个章节独立执行三级合规检查，返回汇总结果。
    """
    if not req.sections:
        raise HTTPException(status_code=400, detail="章节内容不能为空")

    service = ComplianceService(tenant_id=tenant_id)
    base_context = ComplianceContext(
        project_name=req.project_name,
        company_name=req.company_name,
        project_type=req.project_type,
        scoring_points=req.scoring_points,
    )

    section_results: dict[str, ComplianceCheckResponse] = {}
    total_score = 0.0
    all_passed = True

    for title, content in req.sections.items():
        result = await service.check(content, base_context)
        total_score += result.score
        if not result.passed:
            all_passed = False

        section_results[title] = ComplianceCheckResponse(
            passed=result.passed,
            score=result.score,
            summary=result.summary,
            issues=[
                IssueResponse(
                    severity=i.severity.value,
                    category=i.category.value,
                    message=i.message,
                    location=i.location,
                    suggestion=i.suggestion,
                )
                for i in result.issues
            ],
            critical_count=len(result.critical_issues),
            warning_count=len(result.warning_issues),
        )

    section_count = len(req.sections)
    overall_score = total_score / section_count if section_count > 0 else 0

    return BatchComplianceResponse(
        overall_passed=all_passed,
        overall_score=round(overall_score, 1),
        sections=section_results,
    )
