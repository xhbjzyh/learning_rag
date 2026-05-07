"""
审核员-审核工作台接口
"""
from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from db.sqlite_conn import get_db
from middleware.auth_middleware import get_current_user, role_required
from models.db_models import SysUser
from service.auditor.audit_workbench_service import audit_workbench_service
from utils.response import success_response, ApiResponse

router = APIRouter(
    prefix="/audit",
    tags=["审核员-审核工作台"],
    dependencies=[Depends(role_required([1, 2]))]
)


@router.get(
    "/pending",
    summary="获取待审核内容列表",
    response_model=ApiResponse
)
async def get_pending_audit_list(
    db: Session = Depends(get_db)
):
    return success_response(
        data=audit_workbench_service.get_pending_audit_list(db),
        msg="获取待审核列表成功"
    )


@router.get(
    "/history",
    summary="获取审核历史记录",
    response_model=ApiResponse
)
async def get_audit_history(
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 超级管理员查看所有审核记录，审核员只看自己的
    auditor_id = current_user.id if current_user.role_id == 2 else None
    return success_response(
        data=audit_workbench_service.get_audit_history(db, auditor_id),
        msg="获取审核历史成功"
    )


@router.get(
    "/stats",
    summary="获取审核统计数据",
    response_model=ApiResponse
)
async def get_audit_stats(
    db: Session = Depends(get_db)
):
    return success_response(
        data=audit_workbench_service.get_audit_stats(db),
        msg="获取审核统计成功"
    )


@router.put(
    "/apply/{apply_id}",
    summary="审核文档公开申请",
    response_model=ApiResponse
)
async def audit_document_apply(
    apply_id: int = Path(..., description="申请ID", ge=1),
    audit_status: int = Query(..., description="审核状态：1=通过，2=驳回", ge=1, le=2),
    audit_remark: str = Query(None, description="审核备注"),
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return success_response(
        data=audit_workbench_service.audit_document(
            db=db,
            apply_id=apply_id,
            audit_status=audit_status,
            audit_remark=audit_remark,
            auditor_id=current_user.id
        ),
        msg="审核完成"
    )