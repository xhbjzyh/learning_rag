# ==================== 标准库导入 ====================
from contextlib import asynccontextmanager

# ==================== 第三方库导入 ====================
import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

# ==================== 内部模块导入 ====================
from api.knowledge import router as knowledge_router
from api.rag import router as rag_router
from api.user import router as user_router, admin_router as user_admin_router
from api.recommend import router as recommend_router
from api.stats import router as stats_router
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

# ==================== 数据库自动建表 + 初始化管理员 【移动到这里】====================
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
# ==================== 初始化结束 【新增结束】====================

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

app.include_router(rag_router, prefix="/api/rag")
app.include_router(knowledge_router, prefix="/api/knowledge", tags=["知识库模块"])
app.include_router(user_router, prefix="/api/user", tags=["用户模块"])
app.include_router(user_admin_router, prefix="/api/user", tags=["管理员-用户管理"])
app.include_router(recommend_router, prefix="/api/recommend", tags=["个性化推荐模块"])

from api.admin_knowledge import router as admin_knowledge_router
app.include_router(admin_knowledge_router, prefix="/api", tags=["管理员-知识点管理"])
app.include_router(stats_router)
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
        reload=settings.APP_DEBUG,
        log_level="info"
    )