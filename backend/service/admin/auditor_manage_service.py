"""
管理员-审核员管理业务逻辑
"""
from sqlalchemy.orm import Session

from models.db_models import SysUser, UserProfile
from models.schemas import UserInfoResponse
from utils.password_utils import hash_password
from utils.response import BusinessErrorCode, BusinessException
from utils.logger import logger


class AuditorManageService:
    """审核员管理服务类"""

    @staticmethod
    def create_auditor(db: Session, username: str, password: str):
        """创建审核员账号（role_id=2）"""
        # 检查用户名是否已存在
        existing_user = db.query(SysUser).filter(SysUser.username == username).first()
        if existing_user:
            raise BusinessException(msg="用户名已存在")

        # 创建审核员
        auditor = SysUser(
            username=username,
            password=hash_password(password),
            role_id=2,  # 审核员角色
            is_active=1
        )
        db.add(auditor)
        db.flush()  # 获取用户ID

        # 创建用户画像
        profile = UserProfile(
            user_id=auditor.id,
            current_level="审核员",
            preferred_difficulty="中等"
        )
        db.add(profile)
        db.commit()

        logger.info(f"管理员创建审核员账号: {username}")
        return UserInfoResponse.model_validate(auditor)

    @staticmethod
    def create_user(db: Session, username: str, password: str, role_id: int):
        """创建用户（审核员/普通用户）"""
        # 检查用户名是否已存在
        existing_user = db.query(SysUser).filter(SysUser.username == username).first()
        if existing_user:
            raise BusinessException(msg="用户名已存在")

        # 检查角色ID是否合法
        if role_id not in [2, 3]:
            raise BusinessException(msg="角色ID不合法，只能创建审核员(2)或普通用户(3)")

        # 创建用户
        user = SysUser(
            username=username,
            password=hash_password(password),
            role_id=role_id,
            is_active=1
        )
        db.add(user)
        db.flush()  # 获取用户ID

        # 创建用户画像
        profile = UserProfile(
            user_id=user.id,
            current_level="审核员" if role_id == 2 else "普通用户",
            preferred_difficulty="中等"
        )
        db.add(profile)
        db.commit()

        logger.info(f"管理员创建用户账号: {username}, 角色ID: {role_id}")
        return UserInfoResponse.model_validate(user)

    @staticmethod
    def get_auditor_list(db: Session, page: int, size: int):
        """获取审核员列表（分页）"""
        # 只查询 role_id=2 的审核员
        query = db.query(SysUser).filter(SysUser.role_id == 2).order_by(SysUser.id.desc())
        total = query.count()
        auditors = query.offset((page - 1) * size).limit(size).all()
        return {
            "total": total,
            "items": [UserInfoResponse.model_validate(a) for a in auditors]
        }

    @staticmethod
    def delete_auditor(db: Session, auditor_id: int):
        """删除审核员"""
        # 查询审核员
        auditor = db.query(SysUser).filter(SysUser.id == auditor_id).first()
        if not auditor:
            raise BusinessException(code=BusinessErrorCode.USER_NOT_EXIST, msg="审核员不存在")

        # 检查是否是审核员角色
        if auditor.role_id != 2:
            raise BusinessException(msg="只能删除审核员账号")

        # 禁止删除自己
        if auditor_id == 1:
            raise BusinessException(msg="禁止删除超级管理员")

        # 级联删除用户画像
        db.query(UserProfile).filter(UserProfile.user_id == auditor_id).delete()
        db.delete(auditor)
        db.commit()

        logger.info(f"管理员删除审核员账号: {auditor_id}")
        return {"user_id": auditor_id}


auditor_manage_service = AuditorManageService()