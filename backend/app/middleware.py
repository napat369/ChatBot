"""
中间件模块 - 提供请求日志、安全检查等功能
"""
import time
import logging
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # 记录请求信息
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        method = request.method
        url = str(request.url)
        
        logger.info(f"请求开始 - {method} {url} - IP: {client_ip} - User-Agent: {user_agent[:100]}")
        
        try:
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录响应信息
            logger.info(
                f"请求完成 - {method} {url} - "
                f"状态码: {response.status_code} - "
                f"处理时间: {process_time:.3f}s - "
                f"IP: {client_ip}"
            )
            
            # 添加处理时间到响应头
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"请求异常 - {method} {url} - "
                f"错误: {str(e)} - "
                f"处理时间: {process_time:.3f}s - "
                f"IP: {client_ip}"
            )
            raise

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全头中间件"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # 添加安全头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' https:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none';"
        )
        
        return response

class RequestSizeMiddleware(BaseHTTPMiddleware):
    """请求大小限制中间件"""
    
    def __init__(self, app: ASGIApp, max_size: int = 10 * 1024 * 1024):  # 默认10MB
        super().__init__(app)
        self.max_size = max_size
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 检查Content-Length头
        content_length = request.headers.get("content-length")
        if content_length:
            content_length = int(content_length)
            if content_length > self.max_size:
                logger.warning(
                    f"请求体过大 - IP: {request.client.host if request.client else 'unknown'} - "
                    f"大小: {content_length} bytes - 限制: {self.max_size} bytes"
                )
                return JSONResponse(
                    status_code=413,
                    content={
                        "error": "REQUEST_TOO_LARGE",
                        "message": f"请求体过大，最大允许 {self.max_size // (1024*1024)} MB",
                        "timestamp": time.time()
                    }
                )
        
        return await call_next(request)