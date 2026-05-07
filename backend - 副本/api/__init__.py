"""
接口层模块初始化
统一导出所有路由模块，供 main.py 一次性注册
"""
from .common import auth_router
from .admin import (
    user_manage_router,
    auditor_manage_router,
    content_global_router,
    audit_manage_router,
    system_config_router,
    system_audit_router
)
from .auditor import audit_workbench_router, auditor_public_content_router
from .user import (
    content_private_router,
    content_public_router,
    content_apply_router,
    learning_center_router,
    personal_recommend_router,
    user_profile_router,
    personal_center_router,
    rag_chat_router
)

__all__ = [
    "auth_router",
    "user_manage_router",
    "auditor_manage_router",
    "content_global_router",
    "audit_manage_router",
    "system_config_router",
    "system_audit_router",
    "audit_workbench_router",
    "auditor_public_content_router",
    "content_private_router",
    "content_public_router",
    "content_apply_router",
    "learning_center_router",
    "personal_recommend_router",
    "user_profile_router",
    "personal_center_router",
    "rag_chat_router"
]