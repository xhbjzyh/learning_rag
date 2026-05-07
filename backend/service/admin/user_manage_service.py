"""
管理员-用户管理业务逻辑
"""
from sqlalchemy.orm import Session

from models.db_models import SysUser, UserProfile
from models.schemas import UserInfoResponse
from utils.password_utils import hash_password
from utils.response import BusinessErrorCode, BusinessException
from utils.logger import logger


class UserManageService:
    """用户管理服务类"""

    @staticmethod
    def get_user_list(db: Session, page: int, size: int):
        # 🔥 修复1：只返回普通用户（role_id=3），排除管理员
        query = db.query(SysUser).filter(SysUser.role_id == 3).order_by(SysUser.id.desc())
        total = query.count()
        users = query.offset((page - 1) * size).limit(size).all()
        return {"total": total, "items": [UserInfoResponse.model_validate(u) for u in users]}

    # 🔥 修复2：添加缺失的 get_user_info 方法（解决500报错）
    @staticmethod
    def get_user_info(db: Session, user_id: int):
        user = db.query(SysUser).filter(SysUser.id == user_id).first()
        if not user:
            raise BusinessException(code=BusinessErrorCode.USER_NOT_EXIST, msg="用户不存在")

        # 禁止查看超级管理员详情
        if user_id == 1:
            raise BusinessException(msg="禁止查看超级管理员账号信息")

        return UserInfoResponse.model_validate(user)

    @staticmethod
    def update_user(db: Session, user_id: int, is_active: int = None, role_id: int = None):
        user = db.query(SysUser).filter(SysUser.id == user_id).first()
        if not user:
            raise BusinessException(code=BusinessErrorCode.USER_NOT_EXIST, msg="用户不存在")

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

        if user_id == 1:
            raise BusinessException(msg="禁止删除超级管理员")

        db.query(UserProfile).filter(UserProfile.user_id == user_id).delete()
        db.delete(user)
        db.commit()
        logger.info(f"管理员删除用户: {user_id}")
        return {"user_id": user_id}

    @staticmethod
    def reset_user_password(db: Session, user_id: int, new_password: str):
        user = db.query(SysUser).filter(SysUser.id == user_id).first()
        if not user:
            raise BusinessException(code=BusinessErrorCode.USER_NOT_EXIST, msg="用户不存在")

        if user_id == 1:
            raise BusinessException(msg="禁止操作超级管理员账号")

        user.password = hash_password(new_password)
        db.commit()
        logger.warning(f"超级管理员重置用户密码，用户ID: {user_id}")


user_manage_service = UserManageService()