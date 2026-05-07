"""
管理员-审核员管理接口
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.sqlite_conn import get_db
from middleware.auth_middleware import get_current_user, role_required
from models.schemas import (
    AdminCreateAuditorRequest,
    AdminCreateUserRequest,
    SuccessResponse
)
from models.db_models import SysUser
from service.admin.auditor_manage_service import auditor_manage_service
from utils.response import success_response, BusinessException

router = APIRouter(
    prefix="/auditor",
    tags=["管理员-审核员管理"],
    dependencies=[Depends(role_required([1]))]
)


def check_super_admin(user: SysUser):
    if user.role_id != 1:
        raise BusinessException(msg="无权限，仅超级管理员可操作")


@router.post("/create", summary="创建审核员账号")
async def admin_create_auditor(
    request: AdminCreateAuditorRequest,
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_super_admin(current_user)
    return success_response(data=auditor_manage_service.create_auditor(db, request.username, request.password))


@router.post("/user/create", summary="创建用户（审核员/普通用户）")
async def admin_create_user(
    request: AdminCreateUserRequest,
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_super_admin(current_user)
    return success_response(data=auditor_manage_service.create_user(db, request.username, request.password, request.role_id))