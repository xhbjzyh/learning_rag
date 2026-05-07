"""
全局配置管理
基于Pydantic Settings实现，自动从.env文件和环境变量读取配置
支持开发/测试/生产环境隔离，所有路径均为绝对路径，避免相对路径异常
"""
# ==================== 标准库导入 ====================
import os
from typing import Literal
from pathlib import Path

# ==================== 第三方库导入 ====================
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


# 项目根目录（全局唯一绝对路径，基于当前文件位置向上两级定位）
# 设计目的：彻底解决不同运行环境下的相对路径找不到文件的问题
BASE_DIR = Path(__file__).parent.parent.absolute()


class Settings(BaseSettings):
    """全局配置单例类
    优先级：环境变量 > .env文件 > 代码默认值
    """
    # Pydantic Settings 核心配置
    model_config = SettingsConfigDict(
        env_file=os.path.join(BASE_DIR, ".env"),  # 指定.env配置文件路径
        env_file_encoding="utf-8",  # 配置文件编码，避免中文乱码
        extra="ignore"  # 忽略未在类中定义的环境变量，避免启动报错
    )

    # ==================== 服务基础配置 ====================
    APP_HOST: str = Field(default="0.0.0.0", description="服务监听地址，0.0.0.0支持局域网/公网访问")
    APP_PORT: int = Field(default=8000, description="服务监听端口，前端/接口文档通过此端口访问")
    APP_DEBUG: bool = Field(default=True, description="调试模式开关，生产环境必须关闭")
    ENV: Literal["dev", "test", "prod"] = Field(default="dev", description="运行环境标识，用于区分不同环境的配置逻辑")

    # ==================== 项目路径配置 ====================
    # 设计说明：全部使用@property动态生成绝对路径，确保任何运行目录下都能正确定位文件
    @property
    def BASE_DIR(self) -> Path:
        """项目根目录（backend文件夹上级）"""
        return BASE_DIR

    @property
    def DATA_DIR(self) -> Path:
        """数据存储根目录，存放所有本地持久化数据"""
        return BASE_DIR / "data"

    @property
    def UPLOAD_DIR(self) -> Path:
        """文档上传目录，用户上传的PDF/DOCX/TXT文件存储在此"""
        return self.DATA_DIR / "uploads"

    @property
    def FAISS_DIR(self) -> Path:
        """FAISS向量库目录，存放向量索引文件与ID映射文件"""
        return self.DATA_DIR / "faiss"

    @property
    def SQLITE_DB_PATH(self) -> Path:
        """SQLite数据库文件完整路径，业务数据全部存在此库中"""
        return self.DATA_DIR / "sqlite" / "learning_rag.db"

    @property
    def LOG_DIR(self) -> Path:
        """日志文件存储目录，存放服务运行日志与错误日志"""
        return BASE_DIR / "logs"

    # ==================== JWT鉴权配置 ====================
    JWT_SECRET_KEY: str = Field(
        default="your-secret-key-keep-it-safe-2026",
        description="JWT签名加密密钥，生产环境必须替换为强随机字符串，严禁泄露"
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT签名加密算法，行业通用HS256")
    JWT_EXPIRE_MINUTES: int = Field(
        default=1440,  # 24小时
        description="JWT令牌过期时间，单位分钟，默认24小时有效期"
    )

    # ==================== 智谱AI大模型配置 ====================
    ZHIPU_API_KEY: str = Field(
        default="",
        description="智谱AI开放平台API Key，用于大模型对话、RAG问答生成"
    )
    ZHIPU_MODEL_NAME: str = Field(
        default="glm-4-flash",
        description="大模型名称，glm-4-flash为免费调用模型，适合开发测试"
    )

    # ==================== 文本嵌入模型配置 ====================
    EMBEDDING_MODEL_NAME: str = Field(
        default="BAAI/bge-small-zh-v1.5",
        description="中文语义嵌入模型名称，用于文本向量化，支持国内镜像下载"
    )
    EMBEDDING_DIM: int = Field(
        default=512,
        description="嵌入模型输出的向量维度，必须与所选模型匹配，bge-small-zh-v1.5固定为512维"
    )

    # ==================== FAISS向量库配置 ====================
    @property
    def FAISS_INDEX_PATH(self) -> Path:
        """FAISS向量索引文件完整路径，存储向量化后的知识点数据"""
        return self.FAISS_DIR / "rag_index.faiss"

    @property
    def DOC_MAP_PATH(self) -> Path:
        """向量ID与知识点ID映射文件路径，用于检索后还原知识点信息"""
        return self.FAISS_DIR / "doc_id_map.json"

    # ==================== 日志系统配置 ====================
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        description="日志输出级别，开发环境用DEBUG，生产环境用INFO/ERROR"
    )
    LOG_FILE_MAX_BYTES: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        description="单个日志文件最大大小，超出后自动滚动生成新文件"
    )
    LOG_FILE_BACKUP_COUNT: int = Field(
        default=10,
        description="日志文件最大备份数量，超出后自动删除最旧的日志"
    )


# 全局配置单例（项目中所有配置都从此处导入，禁止重复实例化Settings类）
settings = Settings()