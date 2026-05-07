"""
认证业务逻辑实现
处理用户注册、登录、密码验证等核心认证业务
"""
from sqlalchemy.orm import Session

from models.db_models import SysUser, UserProfile
from models.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    UserPasswordUpdateRequest,
    UserInfoResponse
)
from utils.password_utils import hash_password, verify_password
from utils.jwt_utils import create_access_token
from utils.response import BusinessErrorCode, BusinessException
from utils.logger import logger


class AuthService:
    """认证服务类"""

    @staticmethod
    def user_register(db: Session, request: UserRegisterRequest):
        if request.password != request.confirm_password:
            raise BusinessException(code=BusinessErrorCode.PARAM_VALID_ERROR, msg="两次密码不一致")
        if db.query(SysUser).filter(SysUser.username == request.username).first():
            raise BusinessException(code=BusinessErrorCode.USERNAME_EXIST, msg="用户名已存在")

        new_user = SysUser(username=request.username, password=hash_password(request.password), role_id=3, is_active=1)
        db.add(new_user)
        db.flush()
        db.add(UserProfile(user_id=new_user.id, current_level="入门", preferred_difficulty="中等"))
        db.commit()
        logger.info(f"用户注册成功: {request.username}")
        return {"user_id": new_user.id, "username": new_user.username}

    @staticmethod
    def user_login(db: Session, request: UserLoginRequest):
        user = db.query(SysUser).filter(SysUser.username == request.username).first()
        if not user: raise BusinessException(code=BusinessErrorCode.USER_NOT_EXIST, msg="用户不存在")
        if user.is_active != 1: raise BusinessException(code=BusinessErrorCode.USER_DISABLED, msg="账号已禁用")
        if not verify_password(request.password, user.password): raise BusinessException(code=BusinessErrorCode.USER_PASSWORD_ERROR, msg="密码错误")

        token = create_access_token(user_id=user.id)
        logger.info(f"用户登录: {request.username}")
        return {"access_token": token, "user_info": UserInfoResponse.model_validate(user)}

    @staticmethod
    def update_password(db: Session, user_id: int, request: UserPasswordUpdateRequest):
        if request.new_password != request.confirm_new_password:
            raise BusinessException(code=BusinessErrorCode.PARAM_VALID_ERROR, msg="两次新密码不一致")
        user = db.query(SysUser).filter(SysUser.id == user_id).first()
        if not user:
            raise BusinessException(code=BusinessErrorCode.USER_NOT_EXIST, msg="用户不存在")

        if not verify_password(request.old_password, user.password):
            raise BusinessException(code=BusinessErrorCode.USER_PASSWORD_ERROR, msg="原密码错误")

        user.password = hash_password(request.new_password)
        db.commit()
        logger.info(f"用户修改密码: {user_id}")
        return {"msg": "密码修改成功"}

    @staticmethod
    def get_user_info(db: Session, user_id: int):
        user = db.query(SysUser).filter(SysUser.id == user_id).first()
        if not user: raise BusinessException(code=BusinessErrorCode.USER_NOT_EXIST, msg="用户不存在")
        return UserInfoResponse.model_validate(user)


auth_service = AuthService()