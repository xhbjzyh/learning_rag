"""
密码加密工具
使用bcrypt算法实现密码的不可逆加密与校验

bcrypt算法优势：
1. 自动加盐：每次加密生成不同的盐值，抗彩虹表攻击
2. 计算成本可调：通过rounds参数控制加密耗时，越高越安全
3. 行业标准：被广泛应用于各类系统的密码存储

设计说明：
- bcrypt仅支持前72字节密码，超长密码自动截断，避免报错
- 使用passlib库封装，简化bcrypt的使用与兼容性处理
"""
# ==================== 第三方库导入 ====================
from passlib.context import CryptContext


# ==================== 密码加密上下文初始化 ====================
# CryptContext是passlib的核心类，用于统一管理密码加密算法
pwd_context = CryptContext(
    schemes=["bcrypt"],  # 指定使用bcrypt算法
    deprecated="auto",   # 自动处理过时的算法配置，保证兼容性
    bcrypt__rounds=12    # bcrypt计算轮数，推荐值12，越高越安全但越慢
)


def hash_password(password: str) -> str:
    """
    密码加密（不可逆）
    用于用户注册或修改密码时，将原始密码加密后存储到数据库

    :param password: 原始密码（明文）
    :return: 加密后的密码（包含盐值和算法信息的字符串）

    注意事项：
    - bcrypt仅支持前72字节密码，超长密码会自动截断
    - 加密后的密码长度固定为60字节
    - 每次加密同一密码，结果都不同（因为自动加盐）
    """
    # bcrypt仅支持前72字节，自动截断超长密码，避免运行时错误
    if len(password) > 72:
        password = password[:72]
    # 执行加密并返回结果
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    校验密码是否正确
    用于用户登录时，比对输入的原始密码与数据库中存储的加密密码

    :param plain_password: 用户输入的原始密码（明文）
    :param hashed_password: 数据库中存储的加密密码
    :return: 密码是否正确，True=正确，False=错误

    设计说明：
    - 自动从hashed_password中提取盐值和算法信息
    - 即使plain_password被截断，也能正确校验
    - 校验过程耗时与加密过程一致，抗时序攻击
    """
    # 同样处理超长密码，保证与加密时的输入一致
    if len(plain_password) > 72:
        plain_password = plain_password[:72]
    # 执行校验并返回结果
    return pwd_context.verify(plain_password, hashed_password)