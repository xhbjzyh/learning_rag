"""
JWT令牌工具类
实现JWT令牌的生成、校验、解析

JWT（JSON Web Token）优势：
1. 无状态：服务器不存储会话，减轻服务器压力
2. 跨域友好：适合前后端分离架构
3. 自包含：载荷中包含用户信息，无需额外查询数据库

载荷字段设计（标准JWT声明）：
- sub：Subject，主题，这里存储用户ID
- exp：Expiration Time，过期时间，UTC时间戳
- iat：Issued At，签发时间，UTC时间戳
"""
# ==================== 标准库导入 ====================
from datetime import datetime, timedelta, timezone
from typing import Optional

# ==================== 第三方库导入 ====================
from jose import JWTError, jwt

# ==================== 内部模块导入 ====================
from config.settings import settings
from utils.logger import logger


def create_access_token(user_id: int, expires_delta: Optional[timedelta] = None) -> str:
    """
    生成JWT访问令牌
    用于用户登录成功后，返回给前端，前端后续请求在Header中携带此令牌

    :param user_id: 用户ID（整数）
    :param expires_delta: 自定义过期时间（可选），默认使用配置中的JWT_EXPIRE_MINUTES
    :return: JWT令牌字符串（格式：Header.Payload.Signature）

    注意事项：
    - 令牌默认有效期24小时，可在config/settings.py中修改
    - 自定义过期时间优先级高于配置
    - 所有时间均使用UTC时区，避免时区问题
    """
    # ==================== 计算过期时间 ====================
    if expires_delta:
        # 使用自定义过期时间
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # 使用配置中的默认过期时间
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)

    # ==================== 构建JWT载荷 ====================
    to_encode = {
        "sub": str(user_id),  # 主题：用户ID，转字符串是JWT标准要求
        "exp": expire,        # 过期时间：UTC时间戳，jose库会自动处理
        "iat": datetime.now(timezone.utc)  # 签发时间：UTC时间戳，用于调试
    }

    # ==================== 生成JWT令牌 ====================
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,  # 签名密钥，必须保密
        algorithm=settings.JWT_ALGORITHM  # 签名算法，行业通用HS256
    )
    return encoded_jwt


def verify_token(token: str) -> Optional[int]:
    """
    校验JWT令牌，返回用户ID
    用于中间件或接口依赖注入中，验证用户身份

    :param token: JWT令牌字符串（来自前端Header的Authorization）
    :return: 校验成功返回用户ID（整数），失败返回None

    校验流程：
    1. 验证签名：确保令牌未被篡改
    2. 验证过期时间：确保令牌未过期
    3. 提取用户ID：确保载荷中包含有效用户ID

    注意事项：
    - 所有JWTError都会被捕获并记录日志
    - 不会抛出异常，而是返回None，由调用者处理
    """
    try:
        # ==================== 解析并校验JWT令牌 ====================
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,  # 签名密钥，必须与生成时一致
            algorithms=[settings.JWT_ALGORITHM]  # 签名算法，必须与生成时一致
        )

        # ==================== 提取并验证用户ID ====================
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            logger.warning("JWT令牌解析失败：载荷中无用户ID(sub)")
            return None

        # 转换为整数并返回
        return int(user_id_str)

    except JWTError as e:
        # 捕获所有JWT相关错误（签名错误、过期、格式错误等）
        logger.warning(f"JWT令牌校验失败: {str(e)}")
        return None