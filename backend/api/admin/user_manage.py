"""
管理员-用户管理接口
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from db.sqlite_conn import get_db
from middleware.auth_middleware import get_current_user, role_required
from models.schemas import (
    AdminResetPasswordRequest,
    SuccessResponse
)
from models.db_models import SysUser, UserLearningRecord, UserProfile, UserExerciseRecord
from service.admin.user_manage_service import user_manage_service
from utils.response import success_response, BusinessException
from utils.common import orm_to_dict

router = APIRouter(
    prefix="/user",
    tags=["管理员-用户管理"],
    dependencies=[Depends(role_required([1, 2]))]
)


def check_super_admin(user: SysUser):
    if user.role_id != 1:
        raise BusinessException(msg="无权限，仅超级管理员可操作")


# 🔥 修复：学习记录只返回普通用户的数据
@router.get("/learning-records", summary="查看所有用户学习记录")
async def admin_learning_records(
    user_id: int = None,
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 关联用户表，只查询普通用户（role_id=3）的学习记录
    query = db.query(UserLearningRecord).join(
        SysUser,
        UserLearningRecord.user_id == SysUser.id
    ).filter(SysUser.role_id == 3)

    if user_id:
        query = query.filter(UserLearningRecord.user_id == user_id)
    return success_response(data=[orm_to_dict(item) for item in query.all()])


# 🔥 新增：查看所有用户答题记录（修正表名）
@router.get("/answer-records", summary="查看所有用户答题记录")
async def admin_answer_records(
    user_id: int = None,
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 关联用户表，只查询普通用户（role_id=3）的答题记录
    query = db.query(UserExerciseRecord).join(
        SysUser,
        UserExerciseRecord.user_id == SysUser.id
    ).filter(SysUser.role_id == 3)

    if user_id:
        query = query.filter(UserExerciseRecord.user_id == user_id)

    # 按答题时间倒序排列
    query = query.order_by(UserExerciseRecord.create_time.desc())

    return success_response(data=[orm_to_dict(item) for item in query.all()])


# 🔥 修复：用户画像只返回普通用户的数据
@router.get("/profiles", summary="查看所有用户画像")
async def admin_profiles(
    user_id: int = None,
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 关联用户表，只查询普通用户（role_id=3）的画像
    query = db.query(UserProfile).join(
        SysUser,
        UserProfile.user_id == SysUser.id
    ).filter(SysUser.role_id == 3)

    if user_id:
        query = query.filter(UserProfile.user_id == user_id)
    return success_response(data=[orm_to_dict(item) for item in query.all()])


@router.get("/list", summary="用户列表（分页）")
async def admin_user_list(
    page: int = 1,
    size: int = 10,
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return success_response(data=user_manage_service.get_user_list(db, page, size))


@router.get("/detail", summary="用户详情")
async def admin_user_detail(
    user_id: int,
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return success_response(data=user_manage_service.get_user_info(db, user_id))


@router.post("/reset-password", summary="超级管理员重置用户密码")
async def admin_reset_password(
    request: AdminResetPasswordRequest,
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_super_admin(current_user)
    user_manage_service.reset_user_password(db, request.user_id, request.new_password)
    return success_response(msg="用户密码重置成功")


@router.delete("/{user_id}", summary="删除用户（级联删除）")
async def admin_delete_user(
    user_id: int,
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_super_admin(current_user)
    return success_response(data=user_manage_service.delete_user(db, user_id), msg="用户删除成功")


@router.post("/update", summary="修改用户（状态/角色）")
async def admin_update_user(
    user_id: int,
    is_active: int = None,
    role_id: int = None,
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_super_admin(current_user)
    return success_response(data=user_manage_service.update_user(db, user_id, is_active, role_id), msg="用户信息修改成功")