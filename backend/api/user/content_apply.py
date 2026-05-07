"""
用户-内容公开申请接口
"""
from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from db.sqlite_conn import get_db
from middleware.auth_middleware import get_current_user
from models.db_models import SysUser
from service.user.content_apply_service import content_apply_service
from utils.response import success_response, ApiResponse

router = APIRouter(
    prefix="/content/apply",
    tags=["用户-内容公开申请"],
    dependencies=[Depends(get_current_user)]
)


@router.post(
    "/document/{doc_id}",
    summary="申请公开文档",
    response_model=ApiResponse
)
async def apply_document_public(
    doc_id: int = Path(..., description="文档ID", ge=1),
    apply_remark: str = Query(None, description="申请理由"),
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return success_response(
        data=content_apply_service.apply_public(
            db=db,
            doc_id=doc_id,
            user_id=current_user.id,
            apply_remark=apply_remark
        ),
        msg="申请提交成功"
    )


@router.get(
    "/my",
    summary="获取我的公开申请列表",
    response_model=ApiResponse
)
async def get_my_apply_list(
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return success_response(
        data=content_apply_service.get_my_apply_list(db, current_user.id),
        msg="获取申请列表成功"
    )


@router.delete(
    "/{apply_id}",
    summary="取消待审核的公开申请",
    response_model=ApiResponse
)
async def cancel_apply(
    apply_id: int = Path(..., description="申请ID", ge=1),
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return success_response(
        data=content_apply_service.cancel_apply(db, apply_id, current_user.id),
        msg="申请已取消"
    )