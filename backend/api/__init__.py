"""
接口层模块初始化
统一导出所有路由模块，供 main.py 一次性注册
"""
from .user import router as user_router
from .knowledge import router as knowledge_router
from .rag import router as rag_router
from .recommend import router as recommend_router

__all__ = ["user_router", "knowledge_router", "rag_router", "recommend_router"]