"""
服务层模块初始化
"""
from .common.auth_service import auth_service
from .admin.user_manage_service import user_manage_service
from .admin.auditor_manage_service import auditor_manage_service
from .admin.content_global_service import content_global_service
from .auditor.audit_workbench_service import audit_workbench_service
from .user.content_private_service import content_private_service
from .user.content_public_service import content_public_service
from .user.learning_center_service import learning_center_service
from .user.personal_recommend_service import personal_recommend_service
from .user.user_profile_service import user_profile_service
from .user.personal_center_service import personal_center_service
from .user.rag_service import rag_service

__all__ = [
    "auth_service",
    "user_manage_service",
    "auditor_manage_service",
    "content_global_service",
    "audit_workbench_service",
    "content_private_service",
    "content_public_service",
    "learning_center_service",
    "personal_recommend_service",
    "user_profile_service",
    "personal_center_service",
    "rag_service"
]