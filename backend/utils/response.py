"""
统一响应体工具
定义标准化的成功/异常响应格式，对应第二阶段的接口规范

设计原则：
1. 统一格式：所有接口返回统一的 JSON 结构 {code, msg, data}
2. 自动序列化：深度处理 Pydantic 模型、datetime 等特殊类型
3. 业务异常：通过 BusinessException 统一抛出业务错误
4. 状态码分离：业务码(code)与 HTTP 状态码分离，便于前端处理

响应格式说明：
- 成功：{code: 0, msg: "success", data: {...}}
- 失败：{code: 非0, msg: "错误提示", data: 可选详情}
"""
# ==================== 标准库导入 ====================
from typing import Any, Optional, TypeVar, Generic
from datetime import datetime

# ==================== 第三方库导入 ====================
from pydantic import BaseModel
from fastapi import status
from fastapi.responses import JSONResponse

# ==================== 泛型定义 ====================
T = TypeVar("T")  # 泛型T，用于响应体data的类型注解


def deep_serialize(obj: Any) -> Any:
    """
    深度序列化器：递归处理所有嵌套的对象
    解决 FastAPI 默认 JSON 序列化无法处理的类型问题

    处理规则：
    1. Pydantic模型 → 调用 model_dump() 转为字典
    2. datetime → 转为 ISO 格式字符串（如 "2026-04-10T12:00:00"）
    3. 列表/字典 → 递归处理内部每个元素
    4. 其他类型 → 直接返回

    :param obj: 待序列化的任意对象
    :return: 可直接 JSON 序列化的对象
    """
    # 处理 Pydantic 模型（v2 版本）
    if hasattr(obj, "model_dump"):
        return deep_serialize(obj.model_dump())

    # 处理 datetime 时间对象
    if isinstance(obj, datetime):
        return obj.isoformat()

    # 处理列表（递归处理每个元素）
    if isinstance(obj, list):
        return [deep_serialize(item) for item in obj]

    # 处理字典（递归处理每个值）
    if isinstance(obj, dict):
        return {key: deep_serialize(value) for key, value in obj.items()}

    # 其他基础类型（int/str/bool/float等）直接返回
    return obj


class ApiResponse(BaseModel, Generic[T]):
    """
    统一响应体模型（Pydantic）
    用于规范所有接口的返回格式，同时支持 OpenAPI 文档生成

    泛型说明：
    - T 为 data 字段的类型，可通过 ApiResponse[List[User]] 方式指定具体类型

    兼容性说明：
    - 同时保留了 Pydantic v1 的 Config 类与 v2 的兼容写法
    - 生产环境建议统一使用 Pydantic v2 的 model_config
    """
    code: int = 0  # 业务状态码，0表示成功，非0表示失败
    msg: str = "success"  # 提示信息，成功时为"success"，失败时为错误原因
    data: Optional[T] = None  # 响应数据，可为空（如删除操作）

    # Pydantic v1 配置（兼容旧版本）
    class Config:
        from_attributes = True  # 允许从 ORM 对象直接转换
        json_encoders = {
            datetime: lambda v: v.isoformat()  # datetime 序列化方式
        }


def success_response(
    data: Any = None,
    msg: str = "success",
    code: int = 0
) -> JSONResponse:
    """
    成功响应封装函数
    所有接口成功返回时都应调用此函数，保证格式统一

    :param data: 响应数据（可选），如查询结果、创建的对象等
    :param msg: 提示信息（可选），默认为"success"
    :param code: 业务状态码（可选），默认为0（成功）
    :return: FastAPI JSONResponse 对象
    """
    # 第一步：深度序列化所有数据，解决特殊类型无法序列化的问题
    serialized_data = deep_serialize(data)

    # 第二步：构建统一响应体
    response = ApiResponse(code=code, msg=msg, data=serialized_data)

    # 第三步：返回 JSON 响应，HTTP 状态码固定为 200
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=response.model_dump()
    )


def error_response(
    code: int,
    msg: str,
    data: Any = None,
    status_code: int = status.HTTP_200_OK
) -> JSONResponse:
    """
    异常响应封装函数
    用于手动返回错误响应，通常由全局异常中间件自动调用

    :param code: 业务状态码（必填），从 BusinessErrorCode 中选取
    :param msg: 错误提示信息（必填），告知用户错误原因
    :param data: 错误详情（可选），如参数校验错误的具体字段
    :param status_code: HTTP 状态码（可选），默认为 200
    :return: FastAPI JSONResponse 对象
    """
    # 深度序列化错误详情
    serialized_data = deep_serialize(data)

    # 构建统一错误响应体
    response = ApiResponse(code=code, msg=msg, data=serialized_data)

    # 返回 JSON 响应
    return JSONResponse(
        status_code=status_code,
        content=response.model_dump()
    )


# ==================== 业务异常码枚举 ====================
class BusinessErrorCode:
    """
    业务异常码枚举类
    所有业务错误的状态码都在此定义，便于统一管理与前端处理

    码段规划：
    - 10000-19999：通用错误（系统、参数、权限等）
    - 20000-29999：用户模块错误
    - 30000-39999：知识库模块错误
    - 40000-49999：审核模块错误
    - 50000-59999：AI/向量模块错误
    """
    # 通用错误码段 (10000-19999)
    SYSTEM_ERROR = 10000  # 系统内部错误
    PARAM_VALID_ERROR = 10001  # 参数校验错误
    UNAUTHORIZED = 10002  # 未登录/登录过期
    PERMISSION_DENIED = 10003  # 无权限访问

    # 用户模块错误码段 (20000-29999)
    USER_NOT_EXIST = 20001  # 用户不存在
    USER_PASSWORD_ERROR = 20002  # 密码错误
    USERNAME_EXIST = 20003  # 用户名已存在
    USER_DISABLED = 20004  # 用户已被禁用

    # 知识库模块错误码段 (30000-39999)
    DOC_NOT_EXIST = 30001  # 文档不存在
    FILE_TYPE_NOT_SUPPORT = 30002  # 文件类型不支持
    DOC_PARSE_ERROR = 30003  # 文档解析失败
    CATEGORY_NOT_EXIST = 30004  # 分类不存在

    # 审核模块错误码段 (40000-49999)
    AUDIT_RECORD_NOT_EXIST = 40001  # 审核记录不存在
    AUDIT_STATUS_ERROR = 40002  # 审核状态错误

    # AI/向量模块错误码段 (50000-59999)
    LLM_CALL_ERROR = 50001  # 大模型调用失败
    VECTOR_SEARCH_ERROR = 50002  # 向量检索失败
    KNOWLEDGE_EMPTY = 50003  # 知识库为空


# ==================== 自定义业务异常 ====================
class BusinessException(Exception):
    """
    自定义业务异常类
    用于在业务逻辑中抛出错误，由全局异常中间件统一捕获并返回 error_response

    使用方式：
    raise BusinessException(
        code=BusinessErrorCode.USER_NOT_EXIST,
        msg="用户不存在"
    )

    设计说明：
    - 继承自 Python 基础 Exception 类
    - 包含 code（业务码）和 msg（错误信息）两个核心属性
    - 全局异常中间件会自动捕获并转换为统一错误响应
    """
    def __init__(self, code: int, msg: str):
        """
        初始化业务异常
        :param code: 业务状态码，从 BusinessErrorCode 中选取
        :param msg: 错误提示信息
        """
        self.code = code  # 业务状态码
        self.msg = msg    # 错误提示信息
        # 调用父类 Exception 的初始化方法
        super().__init__(msg)