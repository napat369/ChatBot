"""
安全模块 - 提供限流、输入验证等安全功能
"""
import os
import re
from typing import Optional
from fastapi import HTTPException, Request, status
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging

logger = logging.getLogger(__name__)

# 创建限流器
limiter = Limiter(key_func=get_remote_address)

def get_rate_limit() -> str:
    """获取限流配置"""
    rate_limit = os.getenv("RATE_LIMIT_PER_MINUTE", "60")
    return f"{rate_limit}/minute"

def validate_user_input(text: str, max_length: int = 1000) -> bool:
    """
    验证用户输入
    - 检查长度
    - 检查是否包含恶意内容
    - 基本的XSS防护
    """
    if not text or len(text.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="输入内容不能为空"
        )
    
    if len(text) > max_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"输入内容过长，最大长度为 {max_length} 字符"
        )
    
    # 检查潜在的恶意脚本
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe[^>]*>.*?</iframe>',
        r'<object[^>]*>.*?</object>',
        r'<embed[^>]*>.*?</embed>',
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, text, re.IGNORECASE | re.DOTALL):
            logger.warning(f"检测到潜在恶意输入: {text[:100]}...")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="输入内容包含不安全的字符"
            )
    
    return True

def sanitize_output(text: str) -> str:
    """
    清理输出内容，防止XSS攻击
    """
    if not text:
        return ""
    
    # 转义HTML特殊字符
    html_escape_table = {
        "&": "&amp;",
        '"': "&quot;",
        "'": "&#x27;",
        ">": "&gt;",
        "<": "&lt;",
    }
    
    for char, escape in html_escape_table.items():
        text = text.replace(char, escape)
    
    return text

def validate_user_id(user_id: int) -> bool:
    """验证用户ID"""
    if user_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户ID必须大于0"
        )
    
    if user_id > 999999999:  # 限制用户ID的最大值
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户ID超出有效范围"
        )
    
    return True

def log_security_event(event_type: str, details: str, request: Optional[Request] = None):
    """记录安全事件"""
    client_ip = "unknown"
    user_agent = "unknown"
    
    if request:
        client_ip = get_remote_address(request)
        user_agent = request.headers.get("user-agent", "unknown")
    
    logger.warning(
        f"安全事件 - 类型: {event_type}, "
        f"详情: {details}, "
        f"IP: {client_ip}, "
        f"User-Agent: {user_agent}"
    )