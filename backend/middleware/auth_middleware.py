"""
JWT鉴权中间件与权限依赖
实现接口的登录校验、角色权限控制

设计思路：
1. 登录校验：通过 get_current_user 依赖注入实现，未登录直接抛出业务异常
2. 角色权限：通过 role_required 工厂函数实现，支持自定义允许的角色ID列表
3. 分层校验：先校验登录，再校验权限，逻辑清晰

使用方式：
- 仅需登录：在接口参数中添加 `current_user: SysUser = Depends(get_current_user)`
- 需要特定角色：在接口装饰器中添加 `dependencies=[Depends(role_required([1]))]`
"""
# ==================== 标准库导入 ====================
from typing import Optional, List

# ==================== 第三方库导入 ====================
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

# ==================== 内部模块导入 ====================
from utils.jwt_utils import verify_token
from utils.logger import logger
from db.sqlite_conn import get_db
from models.db_models import SysUser
from utils.response import BusinessErrorCode, BusinessException


# ==================== HTTP Bearer 认证方案 ====================
# HTTPBearer 是 FastAPI 提供的安全方案，自动从请求头中提取 Authorization: Bearer <token>
# auto_error=False：不自动抛出401错误，由我们自己控制异常逻辑
oauth2_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
) -> SysUser:
    """
    依赖注入：获取当前登录用户
    核心功能：
    1. 从请求头提取 JWT 令牌
    2. 校验令牌有效性与过期时间
    3. 查询数据库获取用户信息
    4. 验证用户状态（是否被禁用）

    使用方式：
    在接口参数中直接添加：`current_user: SysUser = Depends(get_current_user)`

    异常说明：
    - 未携带令牌：抛出 UNAUTHORIZED 异常
    - 令牌无效/过期：抛出 UNAUTHORIZED 异常
    - 用户不存在/被禁用：抛出 USER_NOT_EXIST 异常

    :param credentials: HTTP Bearer 认证凭证（自动注入）
    :param db: 数据库会话（自动注入）
    :return: 当前登录用户对象（SysUser）
    """
    # ==================== 1. 检查是否携带令牌 ====================
    if not credentials:
        logger.warning("请求未携带Authorization令牌")
        raise BusinessException(
            code=BusinessErrorCode.UNAUTHORIZED,
            msg="请先登录"
        )

    # ==================== 2. 校验令牌有效性 ====================
    token = credentials.credentials
    user_id = verify_token(token)
    if not user_id:
        raise BusinessException(
            code=BusinessErrorCode.UNAUTHORIZED,
            msg="登录已过期，请重新登录"
        )

    # ==================== 3. 查询并验证用户 ====================
    # 查询条件：用户ID匹配 + 账号处于启用状态
    user = db.query(SysUser).filter(
        SysUser.id == user_id,
        SysUser.is_active == 1
    ).first()

    if not user:
        raise BusinessException(
            code=BusinessErrorCode.USER_NOT_EXIST,
            msg="用户不存在或已被禁用"
        )

    # ==================== 4. 返回用户对象 ====================
    return user


def role_required(allowed_roles: List[int]):
    """
    角色权限校验工厂函数
    核心功能：根据传入的允许角色ID列表，生成一个权限校验依赖

    设计模式：工厂函数模式，动态生成校验函数

    使用方式：
    在接口装饰器中添加 dependencies 参数：
    @app.get("/admin", dependencies=[Depends(role_required([1]))])

    示例：
    - 仅超级管理员：role_required([1])
    - 超级管理员+审核员：role_required([1, 2])

    :param allowed_roles: 允许访问的角色ID列表
    :return: 权限校验依赖函数
    """

    async def check_role(
            current_user: SysUser = Depends(get_current_user)
    ):
        """
        实际的权限校验函数
        依赖 get_current_user 先完成登录校验，再进行角色校验
        """
        # 检查当前用户的角色ID是否在允许列表中
        if current_user.role_id not in allowed_roles:
            logger.warning(f"用户{current_user.id}无权限访问，角色ID: {current_user.role_id}")
            raise BusinessException(
                code=BusinessErrorCode.PERMISSION_DENIED,
                msg="无权限访问该接口"
            )
        # 校验通过，返回当前用户对象
        return current_user

    # 返回校验函数
    return check_role