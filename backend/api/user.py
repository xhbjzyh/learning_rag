"""
用户模块接口
彻底解决路径重复问题：/api/user/xxx 而非 /api/user/user/xxx
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
# 🔥 【新增开始】仅添加这3行，其余代码完全不动
from db.sqlite_conn import engine, Base
import models.db_models
Base.metadata.create_all(bind=engine)
# 🔥 【新增结束】

# ==================== 标准库导入 ====================
from contextlib import asynccontextmanager

# ==================== 第三方库导入 ====================
import uvicorn
from fastapi import FastAPI

from db.sqlite_conn import get_db
from service.user_service import user_service
from middleware.auth_middleware import get_current_user
from models.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    UserLoginResponse,
    UserInfoResponse,
    UserPasswordUpdateRequest,
    SuccessResponse,
    AdminCreateAuditorRequest,
    AdminCreateUserRequest,
    AdminResetPasswordRequest  # 导入新增模型
)
from models.db_models import SysUser, UserLearningRecord, UserProfile
from utils.response import success_response, BusinessException
from utils.common import orm_to_dict  # 序列化工具

# ==================== 核心修复：删除内部重复前缀 /user ====================
router = APIRouter(tags=["用户模块"])

# 管理员功能组
admin_router = APIRouter(prefix="/admin", tags=["管理员-用户管理"])

# ==================== 权限校验 ====================
def check_admin(user: SysUser):
    if user.role_id not in (1, 2):
        raise BusinessException(msg="无权限，仅管理员可访问")

def check_super_admin(user: SysUser):
    if user.role_id != 1:
        raise BusinessException(msg="无权限，仅超级管理员可操作")

# ==================== 普通用户接口 ====================
@router.post("/register", summary="用户注册", response_model=SuccessResponse[dict])
async def user_register(request: UserRegisterRequest, db: Session = Depends(get_db)):
    return success_response(data=user_service.user_register(db, request), msg="注册成功")

@router.post("/login", summary="用户登录", response_model=SuccessResponse[UserLoginResponse])
async def user_login(request: UserLoginRequest, db: Session = Depends(get_db)):
    return success_response(data=user_service.user_login(db, request), msg="登录成功")

@router.get("/info", summary="获取当前用户信息", response_model=SuccessResponse[UserInfoResponse])
async def get_user_info(current_user: SysUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return success_response(data=user_service.get_user_info(db, current_user.id))

@router.put("/password", summary="修改当前用户密码", response_model=SuccessResponse[dict])
async def update_password(request: UserPasswordUpdateRequest, current_user: SysUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return success_response(data=user_service.update_password(db, current_user.id, request), msg="密码修改成功")

# ==================== 管理员接口 ====================
@admin_router.get("/learning-records", summary="查看所有用户学习记录")
async def admin_learning_records(user_id: int = None, current_user: SysUser = Depends(get_current_user), db: Session = Depends(get_db)):
    check_admin(current_user)
    query = db.query(UserLearningRecord)
    if user_id: query = query.filter(UserLearningRecord.user_id == user_id)
    return success_response(data=[orm_to_dict(item) for item in query.all()])

@admin_router.get("/profiles", summary="查看所有用户画像")
async def admin_profiles(user_id: int = None, current_user: SysUser = Depends(get_current_user), db: Session = Depends(get_db)):
    check_admin(current_user)
    query = db.query(UserProfile)
    if user_id: query = query.filter(UserProfile.user_id == user_id)
    return success_response(data=[orm_to_dict(item) for item in query.all()])

@admin_router.post("/create-auditor", summary="创建审核员账号")
async def admin_create_auditor(request: AdminCreateAuditorRequest, current_user: SysUser = Depends(get_current_user), db: Session = Depends(get_db)):
    check_super_admin(current_user)
    return success_response(data=user_service.create_auditor(db, request.username, request.password))

@admin_router.get("/users/list", summary="用户列表（可视化）")
async def admin_user_list(page: int = 1, size: int = 10, current_user: SysUser = Depends(get_current_user), db: Session = Depends(get_db)):
    check_admin(current_user)
    return success_response(data=user_service.get_user_list(db, page, size))

@admin_router.get("/users/detail", summary="用户详情")
async def admin_user_detail(user_id: int, current_user: SysUser = Depends(get_current_user), db: Session = Depends(get_db)):
    check_admin(current_user)
    return success_response(data=user_service.get_user_info(db, user_id))

@admin_router.post("/users/create", summary="创建用户（审核员/普通用户）")
async def admin_create_user(request: AdminCreateUserRequest, current_user: SysUser = Depends(get_current_user), db: Session = Depends(get_db)):
    check_super_admin(current_user)
    return success_response(data=user_service.create_user(db, request.username, request.password, request.role_id))

# 🔴 新增：超级管理员重置用户密码
@admin_router.post("/users/reset-password", summary="超级管理员重置用户密码")
async def admin_reset_password(
    request: AdminResetPasswordRequest,
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_super_admin(current_user)
    user_service.reset_user_password(db, request.user_id, request.new_password)
    return success_response(msg="用户密码重置成功")

@admin_router.delete("/users/{user_id}", summary="删除用户（级联删除）")
async def admin_delete_user(user_id: int, current_user: SysUser = Depends(get_current_user), db: Session = Depends(get_db)):
    check_super_admin(current_user)
    if user_id == 1: raise BusinessException(msg="禁止删除超级管理员")
    return success_response(data=user_service.delete_user(db, user_id), msg="用户删除成功")

@admin_router.post("/users/update", summary="修改用户（状态/角色）")
async def admin_update_user(user_id: int, is_active: int = None, role_id: int = None, current_user: SysUser = Depends(get_current_user), db: Session = Depends(get_db)):
    check_super_admin(current_user)
    if user_id == 1: raise BusinessException(msg="禁止修改超级管理员")
    return success_response(data=user_service.update_user(db, user_id, is_active, role_id), msg="用户信息修改成功")

__all__ = ["router", "admin_router"]


# ==================== 统计接口 ====================
@router.get("/stat/dashboard", summary="获取仪表盘统计数据")
async def get_dashboard_stat(db: Session = Depends(get_db)):
    from models.db_models import SysUser, KnowledgeDocument, KnowledgePoint

    user_count = db.query(SysUser).count()
    doc_count = db.query(KnowledgeDocument).count()
    point_count = db.query(KnowledgePoint).count()

    return success_response(data={
        "user_count": user_count,
        "knowledge_count": 0,
        "document_count": doc_count,
        "chat_count": 0
    })