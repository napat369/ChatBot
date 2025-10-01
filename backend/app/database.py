from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import os
from dotenv import load_dotenv

load_dotenv()

# 数据库连接配置 - 从环境变量读取
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "sqlite:///./chatbot.db"  # 默认使用SQLite作为fallback
)

# 根据数据库类型配置不同的参数
if DATABASE_URL.startswith("mysql"):
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600,
        connect_args={"charset": "utf8mb4"}
    )
else:
    # SQLite配置
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# 获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()