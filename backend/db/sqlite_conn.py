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
# 设计说明：从settings中直接获取数据库文件的父目录，确保路径唯一且绝对
# 修复原代码：settings.SQLITE_DB_PATH本身已是绝对路径，无需重复拼接BASE_DIR
DB_DIR = os.path.dirname(settings.SQLITE_DB_PATH)
os.makedirs(DB_DIR, exist_ok=True)  # exist_ok=True避免目录已存在时报错


# ==================== SQLite数据库连接URL ====================
# SQLite连接URL规则：sqlite:/// + 绝对路径（三个斜杠是SQLite的固定要求）
# 修复原代码：直接使用settings.SQLITE_DB_PATH的绝对路径，避免重复拼接导致的路径错误
SQLALCHEMY_DATABASE_URL = f"sqlite:///{settings.SQLITE_DB_PATH}"


# ==================== SQLAlchemy数据库引擎 ====================
# 引擎是SQLAlchemy的核心，负责管理数据库连接池
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    # SQLite多线程必须配置：check_same_thread=False
    # 原因：SQLite默认只允许创建连接的线程使用它，FastAPI是多线程环境，必须关闭此限制
    connect_args={"check_same_thread": False},
    echo=settings.APP_DEBUG,  # 调试模式下打印完整SQL语句，方便排查问题，生产环境建议关闭
    pool_pre_ping=True  # 连接池健康检查，避免使用已断开的连接
)


# ==================== 数据库会话工厂 ====================
# SessionLocal是一个工厂函数，调用它会创建一个新的数据库会话
SessionLocal = sessionmaker(
    autocommit=False,  # 禁止自动提交，必须手动commit()，保证数据一致性
    autoflush=False,   # 禁止自动刷新，避免不必要的数据库交互
    bind=engine        # 绑定到上面创建的引擎
)


# ==================== ORM模型基类 ====================
# 所有数据库表模型（models/db_models.py中的类）都必须继承这个Base
# SQLAlchemy会通过Base自动管理所有表的创建、映射关系
Base = declarative_base()


# ==================== FastAPI数据库会话依赖注入 ====================
def get_db() -> Session:
    """
    数据库会话依赖注入函数
    使用方式：在FastAPI接口参数中添加 `db: Session = Depends(get_db)`

    生命周期管理：
    1. 接口请求进来时：创建一个新的数据库会话
    2. 接口处理期间：使用该会话进行数据库操作
    3. 接口返回后：无论成功或失败，自动关闭会话，避免连接泄漏
    """
    db = SessionLocal()
    try:
        yield db  # 将会话交给接口使用
    finally:
        db.close()  # 无论接口是否报错，都确保会话关闭