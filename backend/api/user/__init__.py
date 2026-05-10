"""
用户模块路由导出
注意：所有路由统一在这里注册到user_router，main.py只需要导入一次
"""
from fastapi import APIRouter

from .content_private import router as content_private_router
from .content_public import router as content_public_router
from .content_apply import router as content_apply_router
from .learning_center import router as learning_center_router
from .personal_recommend import router as personal_recommend_router
from .user_profile import router as user_profile_router
from .personal_center import router as personal_center_router
from .rag_chat import router as rag_chat_router
from .exercise import router as exercise_router
from .exercise_record import router as exercise_record_router
from .course import router as course_router

# 统一用户端根路由
user_router = APIRouter(prefix="/user")

# 注册所有子路由（各自的prefix会自动叠加）
user_router.include_router(content_private_router)
user_router.include_router(content_public_router)
user_router.include_router(content_apply_router)
user_router.include_router(learning_center_router)
user_router.include_router(personal_recommend_router)
user_router.include_router(user_profile_router)
user_router.include_router(personal_center_router)
user_router.include_router(rag_chat_router)
user_router.include_router(exercise_router)
user_router.include_router(exercise_record_router)
user_router.include_router(course_router)

# 只导出统一的user_router
__all__ = ["user_router"]