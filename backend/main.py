# ==================== 标准库导入 ====================
from contextlib import asynccontextmanager

# ==================== 第三方库导入 ====================
import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

# ==================== 内部模块导入 ====================
from config.settings import settings
from utils.logger import logger
from utils.response import success_response, ApiResponse

from middleware.log_middleware import RequestLogMiddleware
from middleware.exception_middleware import (
    global_exception_handler,
    validation_exception_handler,
    business_exception_handler,
    BusinessException
)

from core.rag_engine import rag_engine

# ==================== 数据库自动建表 + 初始化管理员 ====================
from db.sqlite_conn import engine, Base
import models.db_models
from models.db_models import SysRole, SysUser, UserProfile
from utils.password_utils import hash_password
from sqlalchemy.orm import Session
from db.sqlite_conn import SessionLocal

# 自动创建表
Base.metadata.create_all(bind=engine)

# 自动初始化 角色 + 超级管理员
def init_system_data():
    db = SessionLocal()
    try:
        # 1. 初始化角色（如果不存在）
        roles = db.query(SysRole).all()
        if not roles:
            role1 = SysRole(role_name="super_admin", description="超级管理员")
            role2 = SysRole(role_name="auditor", description="审核员")
            role3 = SysRole(role_name="user", description="普通用户")
            db.add_all([role1, role2, role3])
            db.commit()

        # 2. 初始化内置超级管理员（严格判断：不存在才创建）
        admin = db.query(SysUser).filter(SysUser.username == "admin").first()
        if not admin:
            admin_user = SysUser(
                username="admin",
                password=hash_password("admin123"),
                role_id=1,
                is_active=1
            )
            db.add(admin_user)
            db.flush()  # 拿到用户ID

            # 仅在创建管理员时，才插入画像（彻底避免唯一约束冲突）
            profile = UserProfile(
                user_id=admin_user.id,
                current_level="管理员",
                preferred_difficulty="中等"
            )
            db.add(profile)
            db.commit()
            logger.info("✅ 内置超级管理员初始化完成：admin / admin123")
    finally:
        db.close()

# 执行初始化
init_system_data()
# ==================== 初始化结束 ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 50)
    logger.info(f"🚀 后端服务启动成功（懒加载模式）")
    logger.info(f"📌 服务地址: http://127.0.0.1:{settings.APP_PORT}")
    logger.info(f"📚 接口文档: http://127.0.0.1:{settings.APP_PORT}/docs")
    logger.info(f"🔧 运行环境: {settings.ENV}")
    logger.info("💡 核心引擎采用懒加载，第一次调用接口时才会初始化模型")
    logger.info("=" * 50)
    yield
    logger.info("🛑 后端服务已关闭")


# 🔥 注意：app必须定义在路由注册的前面！
app = FastAPI(
    title="基于RAG的个性化学习推荐系统",
    description="管理端+用户端双角色体系的AI学习平台后端API",
    version="1.0.0",
    debug=settings.APP_DEBUG,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestLogMiddleware)

app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(BusinessException, business_exception_handler)

# ==================== 路由注册（修复版，添加了答题记录路由） ====================
# 公共接口（所有角色可访问）
from api.common import auth_router
app.include_router(auth_router, prefix="/api/common", tags=["公共认证接口"])

# 管理员接口（仅超级管理员可访问）
from api.admin import (
    user_manage_router,
    auditor_manage_router,
    content_global_router,
    audit_manage_router
)
app.include_router(user_manage_router, prefix="/api/admin/user", tags=["管理员-用户管理"])
app.include_router(auditor_manage_router, prefix="/api/admin/auditor", tags=["管理员-审核员管理"])
app.include_router(content_global_router, prefix="/api/admin/content", tags=["管理员-内容全局管理"])
app.include_router(audit_manage_router, prefix="/api/admin/audit", tags=["管理员-审核管理"])

# 审核员接口（仅审核员可访问）
from api.auditor import audit_workbench_router, auditor_public_content_router
app.include_router(audit_workbench_router, prefix="/api/auditor/audit", tags=["审核员-审核工作台"])
app.include_router(auditor_public_content_router, prefix="/api/auditor/content", tags=["审核员-公共内容查看"])

# 普通用户接口（仅普通用户可访问）
from api.user import (
    content_private_router,
    content_public_router,
    content_apply_router,
    learning_center_router,
    personal_recommend_router,
    user_profile_router,
    personal_center_router,
    rag_chat_router,
    exercise_router
)
# 🔥 新增：导入答题记录路由
from api.user.exercise_record import router as exercise_record_router

app.include_router(content_private_router, prefix="/api/user/content/private", tags=["用户-私有内容管理"])
app.include_router(content_public_router, prefix="/api/user/content/public", tags=["用户-公共内容消费"])
app.include_router(content_apply_router, prefix="/api/user/content/apply", tags=["用户-内容公开申请"])
app.include_router(learning_center_router, prefix="/api/user/learning", tags=["用户-学习中心"])
app.include_router(personal_recommend_router, prefix="/api/user/recommend", tags=["用户-个性化推荐"])
app.include_router(user_profile_router, prefix="/api/user/profile", tags=["用户-用户画像"])
app.include_router(personal_center_router, prefix="/api/user/personal", tags=["用户-个人中心"])
app.include_router(rag_chat_router, prefix="/api/user/rag", tags=["用户-RAG问答"])
app.include_router(exercise_router, prefix="/api/user/exercise", tags=["用户端-习题管理"])
# 🔥 新增：注册答题记录路由
app.include_router(exercise_record_router, prefix="/api/user/exercise-record", tags=["用户端-答题记录与错题本"])

# ==================== 健康检查接口 ====================
@app.get("/health", summary="健康检查接口", response_model=ApiResponse)
async def health_check():
    logger.info("健康检查接口被调用")
    return success_response(
        data={
            "app_name": "learning_rag_backend",
            "version": "1.0.0",
            "status": "running",
            "env": settings.ENV
        }
    )

# ==================== 测试接口 ====================
@app.get("/test/rag", summary="RAG问答测试接口", response_model=ApiResponse)
async def test_rag(query: str = "什么是RAG？"):
    logger.info(f"RAG测试接口被调用，查询: {query}")
    answer = rag_engine.answer(query)
    return success_response(
        data={"query": query, "answer": answer},
        msg="RAG问答成功"
    )

if __name__ == "__main__":
    uvicorn.run(
        app="main:app",
        host="0.0.0.0",
        port=settings.APP_PORT,
        reload=False,
        log_level="info"
    )