"""
用户业务逻辑实现
处理用户注册、登录、信息管理、密码修改等核心业务
【增强】管理员创建审核员、权限控制、密码重置
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


class UserService:
    """用户服务类"""

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

        # 防护：超级管理员可以改自己密码，普通逻辑不变
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

    @staticmethod
    def create_auditor(db: Session, username: str, password: str):
        if db.query(SysUser).filter(SysUser.username == username).first():
            raise BusinessException(code=BusinessErrorCode.USERNAME_EXIST, msg="用户名已存在")
        user = SysUser(username=username, password=hash_password(password), role_id=2, is_active=1)
        db.add(user)
        db.flush()
        db.add(UserProfile(user_id=user.id, current_level="管理员"))
        db.commit()
        logger.info(f"创建审核员: {username}")
        return {"user_id": user.id, "username": user.username, "role_id": 2}

    @staticmethod
    def create_user(db: Session, username: str, password: str, role_id: int):
        if role_id not in (2,3): raise BusinessException(msg="仅允许创建审核员/普通用户")
        if db.query(SysUser).filter(SysUser.username == username).first():
            raise BusinessException(code=BusinessErrorCode.USERNAME_EXIST, msg="用户名已存在")
        user = SysUser(username=username, password=hash_password(password), role_id=role_id, is_active=1)
        db.add(user)
        db.flush()
        db.add(UserProfile(user_id=user.id, current_level="入门" if role_id==3 else "管理员"))
        db.commit()
        logger.info(f"管理员创建用户: {username}")
        return {"user_id": user.id, "username": user.username, "role_id": role_id}

    # 🔴 新增：超级管理员重置用户密码（无需原密码）
    @staticmethod
    def reset_user_password(db: Session, user_id: int, new_password: str):
        user = db.query(SysUser).filter(SysUser.id == user_id).first()
        if not user:
            raise BusinessException(code=BusinessErrorCode.USER_NOT_EXIST, msg="用户不存在")

        # 🔥 核心防护：禁止重置超级管理员（id=1）密码
        if user_id == 1:
            raise BusinessException(msg="禁止操作超级管理员账号")

        user.password = hash_password(new_password)
        db.commit()
        logger.warning(f"超级管理员重置用户密码，用户ID: {user_id}")

    @staticmethod
    def get_user_list(db: Session, page: int, size: int):
        query = db.query(SysUser).order_by(SysUser.id.desc())
        total = query.count()
        users = query.offset((page-1)*size).limit(size).all()
        return {"total": total, "items": [UserInfoResponse.model_validate(u) for u in users]}

    @staticmethod
    def update_user(db: Session, user_id: int, is_active: int = None, role_id: int = None):
        user = db.query(SysUser).filter(SysUser.id == user_id).first()
        if not user:
            raise BusinessException(code=BusinessErrorCode.USER_NOT_EXIST, msg="用户不存在")

        # 🔥 核心防护：禁止修改超级管理员信息
        if user_id == 1:
            raise BusinessException(msg="禁止操作超级管理员账号")

        if is_active is not None:
            user.is_active = is_active
        if role_id is not None:
            user.role_id = role_id
        db.commit()
        logger.info(f"管理员修改用户信息: {user_id}")
        return UserInfoResponse.model_validate(user)
    @staticmethod
    def delete_user(db: Session, user_id: int):
        user = db.query(SysUser).filter(SysUser.id == user_id).first()
        if not user: raise BusinessException(code=BusinessErrorCode.USER_NOT_EXIST, msg="用户不存在")
        db.query(UserProfile).filter(UserProfile.user_id == user_id).delete()
        db.delete(user)
        db.commit()
        logger.info(f"管理员删除用户: {user_id}")
        return {"user_id": user_id}

user_service = UserService()