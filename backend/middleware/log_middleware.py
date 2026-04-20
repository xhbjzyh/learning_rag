"""
请求日志中间件
记录所有请求的URL、方法、参数、响应状态、处理耗时
"""
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from utils.logger import logger


class RequestLogMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""
    async def dispatch(self, request: Request, call_next):
        # 请求开始时间
        start_time = time.time()
        # 获取请求信息
        method = request.method
        url = request.url.path
        client_ip = request.client.host if request.client else "unknown"

        # 🔥 修复：Loguru 原生语法，彻底规避格式化错误
        logger.info("请求开始 | {} {} | 客户端IP: {}", method, url, client_ip)

        try:
            # 执行请求
            response = await call_next(request)
            # 计算处理耗时
            process_time = round((time.time() - start_time) * 1000, 2)
            # 🔥 修复：Loguru 原生语法
            logger.info("请求完成 | {} {} | 状态码: {} | 耗时: {}ms", method, url, response.status_code, process_time)
            return response

        except Exception as e:
            process_time = round((time.time() - start_time) * 1000, 2)
            # 🔥 终极修复：只用Loguru原生语法，不传任何冲突参数
            logger.error("请求异常 | {} {} | 耗时: {}ms | 异常: {}", method, url, process_time, str(e), exc_info=True)
            raise e