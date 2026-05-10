"""
SQLite数据库连接与会话管理
基于SQLAlchemy 2.0 实现，提供同步数据库连接、会话管理
核心功能：自动创建数据库目录、引擎初始化、会话依赖注入
"""
# ==================== 标准库导入 ====================
import os

# ==================== 第三方库导入 ====================
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# ==================== 内部模块导入 ====================
from config.settings import settings


# ==================== 数据库目录初始化 ====================
DB_DIR = os.path.dirname(settings.SQLITE_DB_PATH)
os.makedirs(DB_DIR, exist_ok=True)


# ==================== SQLite数据库连接URL ====================
SQLALCHEMY_DATABASE_URL = f"sqlite:///{settings.SQLITE_DB_PATH}"


# ==================== SQLAlchemy数据库引擎 ====================
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=settings.APP_DEBUG,
    pool_pre_ping=True
)


# ==================== 数据库会话工厂 ====================
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# ==================== ORM模型基类 ====================
Base = declarative_base()


# ==================== FastAPI数据库会话依赖注入 ====================
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()