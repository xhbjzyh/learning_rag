"""
公共认证接口
处理用户注册、登录、获取用户信息、修改密码
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.sqlite_conn import get_db
from service.common.auth_service import auth_service
from middleware.auth_middleware import get_current_user
from models.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    UserLoginResponse,
    UserInfoResponse,
    UserPasswordUpdateRequest,
    SuccessResponse
)
from models.db_models import SysUser
from utils.response import success_response

router = APIRouter(tags=["公共认证接口"])


@router.post("/register", summary="用户注册", response_model=SuccessResponse[dict])
async def user_register(request: UserRegisterRequest, db: Session = Depends(get_db)):
    return success_response(data=auth_service.user_register(db, request), msg="注册成功")


@router.post("/login", summary="用户登录", response_model=SuccessResponse[UserLoginResponse])
async def user_login(request: UserLoginRequest, db: Session = Depends(get_db)):
    return success_response(data=auth_service.user_login(db, request), msg="登录成功")


@router.get("/info", summary="获取当前用户信息", response_model=SuccessResponse[UserInfoResponse])
async def get_user_info(current_user: SysUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return success_response(data=auth_service.get_user_info(db, current_user.id))


@router.put("/password", summary="修改当前用户密码", response_model=SuccessResponse[dict])
async def update_password(
    request: UserPasswordUpdateRequest,
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return success_response(data=auth_service.update_password(db, current_user.id, request), msg="密码修改成功")