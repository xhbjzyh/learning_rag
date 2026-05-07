"""
管理员-审核员管理业务逻辑
"""
from sqlalchemy.orm import Session

from models.db_models import SysUser, UserProfile
from utils.password_utils import hash_password
from utils.response import BusinessErrorCode, BusinessException
from utils.logger import logger


class AuditorManageService:
    """审核员管理服务类"""

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


auditor_manage_service = AuditorManageService()