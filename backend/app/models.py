from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    title = Column(String(200), nullable=False)  # 会话标题（基于第一个问题生成）
    create_time = Column(DateTime, default=func.now())
    update_time = Column(DateTime, default=func.now(), onupdate=func.now())
    status = Column(Integer, default=1)  # 1-活跃，0-已结束

class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=True, index=True)  # 关联会话
    question = Column(Text(1000), nullable=False)
    create_time = Column(DateTime, default=func.now())
    status = Column(Integer, default=0)  # 0-未回答，1-已回答

class Answer(Base):
    __tablename__ = "answers"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    question_id = Column(Integer, ForeignKey("questions.id"), index=True)
    answer = Column(Text(2000), nullable=False)
    create_time = Column(DateTime, default=func.now())