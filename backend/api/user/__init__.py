"""
用户模块路由导出
注意：所有路由统一在这里注册到user_router，main.py只需要导入一次
"""
from fastapi import APIRouter

from .content_private import router as content_private_router
from .content_public import router as content_public_router
from .content_apply import router as content_apply_router
from .learning_center import router as learning_center_router
from .user_profile import router as user_profile_router
from .personal_center import router as personal_center_router
from .rag_chat import router as rag_chat_router
from .user_course import router as user_course_router  # 🔥 新增：导入合并后的课程路由
from .recommendation_v2 import router as recommendation_v2_router  # 🔥 第二阶段：推荐系统

# 统一用户端根路由（去掉内部prefix，由main.py统一管理）
user_router = APIRouter()

# 注册所有子路由 + 清晰的Swagger分类标签
user_router.include_router(content_private_router, tags=["用户-私有内容管理"])
user_router.include_router(content_public_router, tags=["用户-公共内容浏览"])
user_router.include_router(content_apply_router, tags=["用户-内容公开申请"])
user_router.include_router(learning_center_router, tags=["用户-学习中心"])
user_router.include_router(user_profile_router, tags=["用户-学习画像"])
user_router.include_router(personal_center_router, tags=["用户-个人中心"])
user_router.include_router(rag_chat_router, tags=["用户-AI智能问答"])
user_router.include_router(user_course_router, tags=["用户-课程学习"])  # 🔥 注册合并后的课程路由
user_router.include_router(recommendation_v2_router, tags=["用户-个性化推荐"])  # 🔥 第二阶段：推荐系统

# 只导出统一的user_router
__all__ = ["user_router"]