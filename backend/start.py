#!/usr/bin/env python3
"""
智能客服系统启动脚本
"""
import uvicorn
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

if __name__ == "__main__":
    # 从环境变量获取配置，提供默认值
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "False").lower() == "true"
    
    print(f"🚀 启动智能客服系统...")
    print(f"📍 服务地址: http://{host}:{port}")
    print(f"🔧 调试模式: {'开启' if debug else '关闭'}")
    print(f"📚 API文档: http://{host}:{port}/docs")
    print(f"🔄 健康检查: http://{host}:{port}/api/health")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if not debug else "debug"
    )