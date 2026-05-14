"""
Redis缓存服务
支持向量检索结果缓存、推荐结果缓存等场景
"""
import json
try:
    import redis
except ImportError:
    redis = None
from typing import Optional, Any
from utils.logger import logger
from config.settings import settings


class CacheService:
    """Redis缓存服务"""

    def __init__(self):
        self.redis_client = None
        self.default_ttl = 300  # 默认5分钟

        try:
            if redis is None:
                logger.warning("⚠️ Redis模块未安装，将使用内存缓存")
                return
            
            self.redis_client = redis.Redis(
                host=getattr(settings, 'REDIS_HOST', 'localhost'),
                port=getattr(settings, 'REDIS_PORT', 6379),
                db=0,
                decode_responses=True,
                socket_timeout=2
            )
            # 测试连接
            self.redis_client.ping()
            logger.info("✅ Redis连接成功")
        except Exception as e:
            logger.warning(f"⚠️ Redis连接失败，将使用内存缓存: {e}")
            self.redis_client = None

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        try:
            if self.redis_client:
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"缓存读取失败: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """设置缓存"""
        try:
            if self.redis_client:
                serialized = json.dumps(value, ensure_ascii=False)
                ttl = ttl or self.default_ttl
                self.redis_client.setex(key, ttl, serialized)
                return True
            return False
        except Exception as e:
            logger.error(f"缓存写入失败: {e}")
            return False

    def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            if self.redis_client:
                self.redis_client.delete(key)
                return True
            return False
        except Exception as e:
            logger.error(f"缓存删除失败: {e}")
            return False

    def clear_pattern(self, pattern: str) -> bool:
        """清除匹配模式的缓存"""
        try:
            if self.redis_client:
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
                return True
            return False
        except Exception as e:
            logger.error(f"缓存清理失败: {e}")
            return False


# 全局单例
cache_service = CacheService()
