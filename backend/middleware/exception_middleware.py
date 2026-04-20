"""
全局异常处理器
统一捕获所有异常，返回标准化的错误响应，避免服务崩溃

设计思路：
1. 分层捕获：按「业务异常 → 参数校验异常 → 全局异常」的优先级捕获
2. 统一响应：所有异常都通过 error_response 返回统一格式
3. 日志记录：所有异常都记录详细日志，便于排查问题
4. 状态码策略：
   - 业务异常：HTTP 200，通过业务码(code)区分错误
   - 参数校验异常：HTTP 200，返回详细错误字段
   - 全局异常：HTTP 500，提示系统内部错误

异常处理优先级（FastAPI 规则）：
1. 自定义业务异常 (BusinessException)
2. 请求参数校验异常 (RequestValidationError)
3. 全局异常 (Exception)
"""
# ==================== 标准库导入 ====================
# （无标准库导入）

# ==================== 第三方库导入 ====================
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# ==================== 内部模块导入 ====================
from utils.logger import logger
from utils.response import error_response, BusinessErrorCode, BusinessException


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    全局异常处理器（兜底）
    捕获所有未被其他处理器捕获的异常，避免服务直接崩溃

    触发场景：
    - 代码逻辑错误（如 IndexError、KeyError）
    - 第三方库调用异常
    - 数据库连接异常等未预期错误

    日志说明：
    - 使用 logger.error 记录
    - exc_info=exc 会记录完整的堆栈信息，便于排查

    :param request: FastAPI 请求对象，用于获取请求路径等信息
    :param exc: 捕获到的异常对象
    :return: 标准化的 JSON 错误响应，HTTP 状态码 500
    """
    # 记录详细错误日志，包含堆栈信息
    logger.error(
        f"全局异常捕获 | 请求路径: {request.url.path} | 异常: {str(exc)}",
        exc_info=exc
    )
    # 返回统一错误响应，不暴露具体错误细节给前端
    return error_response(
        code=BusinessErrorCode.SYSTEM_ERROR,
        msg="系统内部错误，请稍后重试",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    请求参数校验异常处理器
    捕获 FastAPI 自动参数校验失败的异常（如类型错误、必填字段缺失）

    触发场景：
    - 接口入参类型不匹配（如传了字符串给 int 字段）
    - 必填字段缺失
    - 参数格式不符合 Pydantic 模型定义

    日志说明：
    - 使用 logger.warning 记录（这是客户端错误，非系统错误）
    - 记录详细的校验错误信息，便于前端调试

    :param request: FastAPI 请求对象
    :param exc: Pydantic 参数校验异常对象
    :return: 标准化的 JSON 错误响应，包含详细错误字段
    """
    # 构建详细错误信息
    error_msg = f"参数校验失败: {str(exc.errors())}"
    # 记录警告日志
    logger.warning(
        f"参数校验异常 | 请求路径: {request.url.path} | 详情: {error_msg}"
    )
    # 返回统一错误响应，data 字段包含详细错误字段，便于前端定位问题
    return error_response(
        code=BusinessErrorCode.PARAM_VALID_ERROR,
        msg="请求参数格式错误，请检查输入",
        data=exc.errors()
    )


async def business_exception_handler(request: Request, exc: BusinessException) -> JSONResponse:
    """
    业务异常处理器（核心）
    捕获自定义的 BusinessException，返回业务层面的错误提示

    触发场景：
    - 用户不存在
    - 密码错误
    - 无权限访问
    - 文档不存在等业务逻辑错误

    日志说明：
    - 使用 logger.warning 记录（这是业务逻辑错误，非系统错误）
    - 记录业务码和错误信息，便于统计业务错误

    :param request: FastAPI 请求对象
    :param exc: 自定义业务异常对象
    :return: 标准化的 JSON 错误响应，使用异常中的业务码和信息
    """
    # 记录警告日志
    logger.warning(
        f"业务异常 | 请求路径: {request.url.path} | 异常码: {exc.code} | 信息: {exc.msg}"
    )
    # 返回统一错误响应，直接使用业务异常中的 code 和 msg
    return error_response(
        code=exc.code,
        msg=exc.msg
    )