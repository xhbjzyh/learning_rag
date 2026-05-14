from fastapi import APIRouter
from .auth import router as auth_router
from .file_upload import router as file_upload_router

# 创建通用路由
router = APIRouter()

# 注册子路由（不添加额外prefix，保持原有路径）
router.include_router(auth_router, tags=["认证相关"])
router.include_router(file_upload_router, tags=["文件上传"])

__all__ = ["router", "auth_router", "file_upload_router"]
