"""
统一日志工具
基于 loguru 实现，功能强大且配置灵活

核心功能：
1. 双端输出：同时输出到控制台和文件
2. 分级输出：DEBUG/INFO/WARNING/ERROR 分级记录
3. 自动分割：按日期/大小自动分割日志文件
4. 自动清理：过期日志自动压缩并清理
5. 异步安全：enqueue=True 保证多线程/异步环境安全
6. 堆栈追踪：backtrace=True 记录完整错误堆栈

日志文件规划：
- {date}.log：全量日志，按天分割，保留30天
- error.log：错误日志单独存放，按大小分割，保留90天
"""
# ==================== 标准库导入 ====================
import os
import sys

# ==================== 第三方库导入 ====================
from loguru import logger

# ==================== 内部模块导入 ====================
from config.settings import settings


# ==================== 日志目录初始化 ====================
# 修复：直接使用 settings.LOG_DIR，它已经是基于 BASE_DIR 的绝对路径
LOG_DIR = settings.LOG_DIR
# 确保日志目录存在，不存在则自动创建
os.makedirs(LOG_DIR, exist_ok=True)


# ==================== Loguru 基础配置 ====================
# 移除 loguru 默认的控制台输出（避免重复输出）
logger.remove()


# ==================== 日志格式定义 ====================
# 控制台输出格式（带颜色，便于开发调试）
console_format = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "  # 时间（绿色）
    "<level>{level: <8}</level> | "  # 日志级别（带颜色，左对齐8位）
    "<cyan>{name}</cyan>:<cyan>{line}</cyan> - "  # 文件名:行号（青色）
    "<level>{message}</level>"  # 日志内容（带颜色）
)

# 文件输出格式（纯文本，无颜色，便于日志分析）
file_format = (
    "{time:YYYY-MM-DD HH:mm:ss} | "  # 时间
    "{level: <8} | "  # 日志级别（左对齐8位）
    "{name}:{line} - "  # 文件名:行号
    "{message}"  # 日志内容
)


# ==================== 1. 控制台输出配置 ====================
logger.add(
    sys.stdout,  # 输出到标准输出
    format=console_format,  # 使用带颜色的控制台格式
    level=settings.LOG_LEVEL,  # 日志级别，从配置读取
    enqueue=True,  # 异步队列模式，保证多线程/异步安全
    backtrace=True,  # 记录完整的错误堆栈
    diagnose=settings.APP_DEBUG  # 调试模式下显示详细诊断信息，生产环境建议关闭
)


# ==================== 2. 全量日志文件配置（按天分割） ====================
logger.add(
    os.path.join(LOG_DIR, "{time:YYYY-MM-DD}.log"),  # 文件名按日期命名
    format=file_format,  # 使用纯文本文件格式
    level=settings.LOG_LEVEL,  # 日志级别
    rotation="00:00",  # 每天0点自动分割新文件
    retention="30 days",  # 保留最近30天的日志
    compression="zip",  # 过期日志自动压缩为zip格式，节省空间
    enqueue=True,  # 异步队列模式
    backtrace=True,  # 记录完整堆栈
    diagnose=settings.APP_DEBUG,  # 调试模式诊断信息
    encoding="utf-8"  # 文件编码为UTF-8，避免中文乱码
)


# ==================== 3. 错误日志单独配置（按大小分割） ====================
logger.add(
    os.path.join(LOG_DIR, "error.log"),  # 错误日志单独文件
    format=file_format,  # 使用纯文本文件格式
    level="ERROR",  # 仅记录 ERROR 及以上级别的日志
    rotation="10 MB",  # 文件达到10MB时自动分割
    retention="90 days",  # 保留最近90天的错误日志
    compression="zip",  # 过期自动压缩
    enqueue=True,  # 异步队列模式
    backtrace=True,  # 记录完整堆栈（错误日志必须开启）
    diagnose=True,  # 错误日志始终显示详细诊断信息
    encoding="utf-8"  # UTF-8编码
)


# ==================== 导出单例 ====================
# 导出 logger 单例，其他模块通过 `from utils.logger import logger` 使用
__all__ = ["logger"]