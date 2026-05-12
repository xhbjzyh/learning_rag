"""
审核员-审核工作台接口
"""
from fastapi import APIRouter, Depends, Path, Query, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
from urllib.parse import quote

from db.sqlite_conn import get_db
from middleware.auth_middleware import get_current_user, role_required
from models.db_models import SysUser, KnowledgeDocument
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


@router.get(
    "/document/{doc_id}/download",
    summary="审核员下载待审核文档"
)
async def download_pending_document(
    doc_id: int = Path(..., description="文档ID"),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """审核员下载待审核文档（用于审核前查看）"""
    # 查询文档信息（不限制公开状态，审核员可以查看所有待审核文档）
    document = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.id == doc_id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 检查文件是否存在
    file_path = document.file_path
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件已被删除或损坏")

    # 文件名编码
    encoded_filename = quote(document.file_name, encoding='utf-8')

    # 返回文件下载响应
    return FileResponse(
        path=file_path,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
        }
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