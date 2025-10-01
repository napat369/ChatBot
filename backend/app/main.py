import os
import logging
from datetime import datetime
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
import asyncio
import json
from dotenv import load_dotenv

from .database import engine, get_db
from .models import Base, Question, Answer, Session
from .security import limiter, get_rate_limit, validate_user_input, validate_user_id, log_security_event
from .middleware import RequestLoggingMiddleware, SecurityHeadersMiddleware, RequestSizeMiddleware

# 加载环境变量
load_dotenv()

# 配置日志
log_level = os.getenv("LOG_LEVEL", "INFO")
log_file = os.getenv("LOG_FILE", "logs/app.log")

# 创建日志目录
os.makedirs(os.path.dirname(log_file) if os.path.dirname(log_file) else "logs", exist_ok=True)

logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 安全配置
SECRET_KEY = os.getenv("SECRET_KEY", "default-secret-key")
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:8080").split(",")
MAX_REQUEST_SIZE = int(os.getenv("MAX_REQUEST_SIZE", "10485760"))  # 10MB

# 创建数据库表
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时创建表
    Base.metadata.create_all(bind=engine)
    logger.info("数据库表创建完成")
    yield
    # 关闭时的清理工作
    logger.info("应用关闭")

# 创建FastAPI应用
app = FastAPI(
    title=os.getenv("APP_NAME", "智能客服系统"),
    version=os.getenv("APP_VERSION", "1.0.0"),
    description="基于 DeepSeek AI 的智能客服系统",
    lifespan=lifespan
)

# 添加限流器到应用
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 添加自定义中间件
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestSizeMiddleware, max_size=MAX_REQUEST_SIZE)

# 安全中间件
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=ALLOWED_HOSTS
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=3600,
)

class QuestionRequest(BaseModel):
    user_id: int = Field(..., gt=0, description="用户ID，必须大于0")
    question: str = Field(..., min_length=1, max_length=1000, description="问题内容")
    session_id: Optional[int] = Field(None, description="会话ID，如果为空则创建新会话")

class SessionRequest(BaseModel):
    user_id: int = Field(..., gt=0, description="用户ID，必须大于0")
    title: str = Field(..., min_length=1, max_length=200, description="会话标题")

class SessionResponse(BaseModel):
    id: int
    user_id: int
    title: str
    create_time: str
    update_time: str
    status: int
    question_count: int = Field(description="会话中的问题数量")

class QuestionResponse(BaseModel):
    id: int
    question: str
    answer: Optional[str] = None
    create_time: str
    status: int = Field(description="状态：0-未回答，1-已回答")
    session_id: Optional[int] = None

class ErrorResponse(BaseModel):
    error: str
    message: str
    timestamp: str

# 全局异常处理器
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    logger.error(f"HTTP异常: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="HTTP_ERROR",
            message=exc.detail,
            timestamp=datetime.now().isoformat()
        ).dict()
    )

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request, exc):
    logger.error(f"数据库异常: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="DATABASE_ERROR",
            message="数据库操作失败",
            timestamp=datetime.now().isoformat()
        ).dict()
    )

# 创建问题并流式返回AI回答
@app.get("/api/questions/stream")
@limiter.limit(get_rate_limit())
async def create_question_stream(request: Request, user_id: int, question: str, session_id: Optional[int] = None, db: Session = Depends(get_db)):
    """
    创建问题并以流式方式返回AI回答
    """
    # 验证输入
    validate_user_id(user_id)
    validate_user_input(question)
    
    logger.info(f"收到用户 {user_id} 的流式问题: {question[:50]}...")
    
    try:
        # 获取或创建会话
        if not session_id:
            # 创建新会话
            session_title = question[:50] + "..." if len(question) > 50 else question
            db_session = Session(
                user_id=user_id,
                title=session_title,
                status=1
            )
            db.add(db_session)
            db.commit()
            db.refresh(db_session)
            session_id = db_session.id
            logger.info(f"创建新会话，ID: {session_id}")
        else:
            # 验证会话是否存在且属于该用户
            existing_session = db.query(Session).filter(
                Session.id == session_id,
                Session.user_id == user_id,
                Session.status == 1
            ).first()
            
            if not existing_session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="会话不存在或已关闭"
                )
        
        # 保存问题到数据库
        db_question = Question(
            user_id=user_id,
            question=question,
            session_id=session_id,
            status=0  # 初始状态为未回答
        )
        db.add(db_question)
        db.commit()
        db.refresh(db_question)
        logger.info(f"问题已保存，ID: {db_question.id}")
        
        # 获取对话历史上下文
        try:
            recent_questions = db.query(Question).filter(
                Question.user_id == user_id,
                Question.session_id == session_id
            ).order_by(Question.create_time.desc()).limit(100).all()
            
            context_messages = []
            total_context_length = 0
            max_context_length = 20000
            
            for q in reversed(recent_questions):
                answer = db.query(Answer).filter(Answer.question_id == q.id).first()
                if answer:
                    question_text = f"用户：{q.question}"
                    answer_text = f"助手：{answer.answer}"
                    
                    round_length = len(question_text) + len(answer_text)
                    if total_context_length + round_length > max_context_length:
                        break
                    
                    context_messages.append(question_text)
                    context_messages.append(answer_text)
                    total_context_length += round_length
            
            context_text = "\n".join(context_messages) if context_messages else ""
            context_rounds = len(context_messages) // 2
            
            if context_text:
                prompt = f"""你是一个专业、友好的智能客服助手。请根据用户的问题和对话历史提供准确、有用的回答。

对话历史（最近{context_rounds}轮）：
{context_text}

当前问题：{question}

请提供准确、专业的回答，保持友好、耐心的语调。如果当前问题与历史对话相关，请体现出连贯性。

回答："""
            else:
                prompt = f"""你是一个专业、友好的智能客服助手。请根据用户的问题提供准确、有用的回答。

用户问题：{question}

请提供准确、专业的回答，保持友好、耐心的语调。

回答："""
            
            logger.info(f"正在调用DeepSeek API流式响应，包含 {context_rounds} 轮历史对话")
            
        except Exception as e:
            logger.warning(f"获取对话历史失败，使用无上下文模式: {str(e)}")
            prompt = f"""你是一个专业、友好的智能客服助手。请根据用户的问题提供准确、有用的回答。

用户问题：{question}

请提供准确、专业的回答，保持友好、耐心的语调。

回答："""
        
        # 流式生成器函数
        async def generate_stream():
            full_answer = ""
            try:
                # 发送初始响应，包含问题信息
                initial_data = {
                    "type": "question",
                    "data": {
                        "id": db_question.id,
                        "question": db_question.question,
                        "create_time": db_question.create_time.isoformat(),
                        "session_id": session_id
                    }
                }
                yield f"data: {json.dumps(initial_data, ensure_ascii=False)}\n\n"
                
                # 使用真正的流式响应
                llm = ChatOpenAI(
                    model="deepseek-reasoner", 
                    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
                    openai_api_base=os.getenv("DEEPSEEK_API_BASE"),
                    timeout=60,
                    max_retries=0,
                    streaming=True  # 启用流式响应
                )
                message = HumanMessage(content=prompt)
                
                # 使用流式响应
                logger.info(f"开始流式生成回答，问题: {question}")
                async for chunk in llm.astream([message]):
                    if chunk.content:
                        full_answer += chunk.content
                        chunk_data = {
                            "type": "chunk",
                            "data": {
                                "chunk": chunk.content,
                                "is_final": False
                            }
                        }
                        yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
                
                logger.info(f"流式生成完成，总长度: {len(full_answer)} 字符")
                
                # 保存完整回答到数据库
                db_answer = Answer(
                    question_id=db_question.id,
                    answer=full_answer
                )
                db.add(db_answer)
                db_question.status = 1
                db.commit()
                
                # 发送完成信号
                final_data = {
                    "type": "complete",
                    "data": {
                        "question_id": db_question.id,
                        "full_answer": full_answer,
                        "session_id": session_id
                    }
                }
                yield f"data: {json.dumps(final_data, ensure_ascii=False)}\n\n"
                
                logger.info(f"流式回答完成，问题ID: {db_question.id}")
                
            except Exception as e:
                logger.error(f"流式生成回答失败: {str(e)}")
                error_data = {
                    "type": "error",
                    "data": {
                        "error": "AI服务暂时不可用，请稍后再试",
                        "question_id": db_question.id
                    }
                }
                yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"数据库操作失败: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="数据库操作失败"
        )
    except Exception as e:
        logger.error(f"创建流式问题时发生未知错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误"
        )

# 创建问题（保留原有的非流式API）并获取回答
@app.post("/api/questions", response_model=QuestionResponse)
@limiter.limit(get_rate_limit())
async def create_question(request: Request, question_request: QuestionRequest, db: Session = Depends(get_db)):
    # 验证用户输入
    validate_user_id(question_request.user_id)
    validate_user_input(question_request.question)
    
    logger.info(f"收到用户 {question_request.user_id} 的问题: {question_request.question[:50]}...")
    
    try:
        # 处理会话逻辑
        session_id = question_request.session_id
        if session_id:
            # 验证会话是否存在且属于该用户
            session = db.query(Session).filter(
                Session.id == session_id,
                Session.user_id == question_request.user_id,
                Session.status == 1
            ).first()
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="会话不存在或已关闭"
                )
        else:
            # 创建新会话
            session_title = question_request.question[:50] + "..." if len(question_request.question) > 50 else question_request.question
            session = Session(
                user_id=question_request.user_id,
                title=session_title,
                status=1
            )
            db.add(session)
            db.commit()
            db.refresh(session)
            session_id = session.id
            logger.info(f"创建新会话，ID: {session_id}")
        
        # 保存问题
        db_question = Question(
            user_id=question_request.user_id,
            question=question_request.question,
            session_id=session_id
        )
        db.add(db_question)
        db.commit()
        db.refresh(db_question)
        logger.info(f"问题已保存，ID: {db_question.id}")
        
        # 获取当前会话的对话历史作为上下文
        try:
            recent_questions = db.query(Question).filter(
                Question.user_id == question_request.user_id,
                Question.session_id == session_id
            ).order_by(Question.create_time.desc()).limit(100).all()
            
            context_messages = []
            total_context_length = 0
            max_context_length = 20000  # 限制上下文总长度
            
            for q in reversed(recent_questions):  # 按时间正序排列
                answer = db.query(Answer).filter(Answer.question_id == q.id).first()
                if answer:
                    question_text = f"用户：{q.question}"
                    answer_text = f"助手：{answer.answer}"
                    
                    # 检查添加这轮对话是否会超过长度限制
                    round_length = len(question_text) + len(answer_text)
                    if total_context_length + round_length > max_context_length:
                        break
                    
                    context_messages.append(question_text)
                    context_messages.append(answer_text)
                    total_context_length += round_length
            
            # 构建包含上下文的提示词
            context_text = "\n".join(context_messages) if context_messages else ""
            context_rounds = len(context_messages) // 2
            
            if context_text:
                prompt = f"""你是一个专业、友好的智能客服助手。请根据用户的问题和对话历史提供准确、有用的回答。

对话历史（最近{context_rounds}轮）：
{context_text}

当前问题：{question_request.question}

请提供：
1. 准确、专业的回答
2. 如果需要，结合对话历史提供更个性化的建议
3. 保持友好、耐心的语调
4. 如果当前问题与历史对话相关，请体现出连贯性

回答："""
            else:
                prompt = f"""你是一个专业、友好的智能客服助手。请根据用户的问题提供准确、有用的回答。

用户问题：{question_request.question}

请提供：
1. 准确、专业的回答
2. 如果需要，提供相关的建议或解决方案
3. 保持友好、耐心的语调

回答："""
            
            logger.info(f"正在调用DeepSeek API，包含 {context_rounds} 轮历史对话，上下文长度: {total_context_length}")
            
        except Exception as e:
            logger.warning(f"获取对话历史失败，使用无上下文模式: {str(e)}")
            prompt = f"""你是一个专业、友好的智能客服助手。请根据用户的问题提供准确、有用的回答。

用户问题：{question_request.question}

请提供：
1. 准确、专业的回答
2. 如果需要，提供相关的建议或解决方案
3. 保持友好、耐心的语调

回答："""
        
        # 调用DeepSeek API获取回答（带重试机制）
        max_retries = 3
        retry_delay = 1  # 秒
        api_timeout = 60  # 增加到60秒
        
        for attempt in range(max_retries):
            try:
                logger.info(f"正在调用DeepSeek API（第 {attempt + 1} 次尝试）...")
                
                llm = ChatOpenAI(
                    model="deepseek-reasoner", 
                    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
                    openai_api_base=os.getenv("DEEPSEEK_API_BASE"),
                    timeout=api_timeout,
                    max_retries=0  # 禁用langchain内部重试，我们自己控制
                )
                message = HumanMessage(content=prompt)
                response = await asyncio.wait_for(
                    asyncio.to_thread(llm.invoke, [message]),
                    timeout=api_timeout
                )
                answer_text = response.content
                logger.info(f"AI回答生成成功，长度: {len(answer_text)}，尝试次数: {attempt + 1}")
                break  # 成功则跳出重试循环
                
            except asyncio.TimeoutError:
                logger.warning(f"DeepSeek API调用超时（第 {attempt + 1} 次尝试）")
                if attempt == max_retries - 1:  # 最后一次尝试
                    logger.error("DeepSeek API调用最终超时，所有重试均失败")
                    answer_text = "抱歉，AI服务响应较慢，请稍后再试。我们正在努力改善服务质量。"
                    log_security_event("API_TIMEOUT", f"用户 {question_request.user_id} 的请求超时（{max_retries}次重试后）", request)
                else:
                    # 等待后重试
                    await asyncio.sleep(retry_delay * (attempt + 1))  # 递增延迟
                    continue
                    
            except Exception as e:
                logger.warning(f"调用DeepSeek API失败（第 {attempt + 1} 次尝试）: {str(e)}")
                if attempt == max_retries - 1:  # 最后一次尝试
                    logger.error(f"DeepSeek API调用最终失败: {str(e)}")
                    answer_text = "抱歉，AI服务暂时不可用，请稍后再试。如问题持续，请联系技术支持。"
                    log_security_event("API_ERROR", f"AI服务错误（{max_retries}次重试后）: {str(e)}", request)
                else:
                    # 等待后重试
                    await asyncio.sleep(retry_delay * (attempt + 1))
                    continue
        
        # 保存回答
        try:
            db_answer = Answer(
                question_id=db_question.id,
                answer=answer_text
            )
            db.add(db_answer)
            
            # 更新问题状态
            db_question.status = 1
            db.commit()
            logger.info(f"回答已保存，问题ID: {db_question.id}")
            
        except SQLAlchemyError as e:
            logger.error(f"保存回答失败: {str(e)}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="保存回答失败"
            )
        
        return QuestionResponse(
            id=db_question.id,
            question=db_question.question,
            answer=answer_text,
            create_time=db_question.create_time.isoformat(),
            status=db_question.status,
            session_id=db_question.session_id
        )
        
    except SQLAlchemyError as e:
        logger.error(f"数据库操作失败: {str(e)}")
        db.rollback()
        log_security_event("DATABASE_ERROR", f"数据库错误: {str(e)}", request)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="数据库操作失败"
        )
    except Exception as e:
        logger.error(f"创建问题时发生未知错误: {str(e)}")
        log_security_event("UNKNOWN_ERROR", f"未知错误: {str(e)}", request)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误"
        )

# 获取用户历史记录
@app.get("/api/history/{user_id}", response_model=List[QuestionResponse])
@limiter.limit(get_rate_limit())
async def get_history(request: Request, user_id: int, db: Session = Depends(get_db)):
    # 验证用户ID
    validate_user_id(user_id)
    
    logger.info(f"获取用户 {user_id} 的历史记录")
    
    try:
        # 查询用户的问题和回答
        questions = db.query(Question).filter(Question.user_id == user_id).order_by(Question.create_time.desc()).all()
        
        result = []
        for question in questions:
            answer = db.query(Answer).filter(Answer.question_id == question.id).first()
            result.append(QuestionResponse(
                id=question.id,
                question=question.question,
                answer=answer.answer if answer else None,
                create_time=question.create_time.isoformat(),
                status=question.status
            ))
        
        logger.info(f"成功获取用户 {user_id} 的 {len(result)} 条历史记录")
        return result
        
    except SQLAlchemyError as e:
        logger.error(f"获取历史记录时数据库错误: {str(e)}")
        log_security_event("DATABASE_ERROR", f"获取历史记录失败: {str(e)}", request)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取历史记录失败"
        )
    except Exception as e:
        logger.error(f"获取历史记录时发生未知错误: {str(e)}")
        log_security_event("UNKNOWN_ERROR", f"获取历史记录错误: {str(e)}", request)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误"
        )

# 清空用户历史记录（删除数据库数据）
@app.delete("/api/history/{user_id}")
@limiter.limit(get_rate_limit())
async def clear_history(request: Request, user_id: int, db: Session = Depends(get_db)):
    # 验证用户ID
    validate_user_id(user_id)
    
    logger.info(f"开始清空用户 {user_id} 的历史记录")
    
    try:
        # 获取用户的所有问题ID
        questions = db.query(Question).filter(Question.user_id == user_id).all()
        question_ids = [q.id for q in questions]
        
        if not question_ids:
            logger.info(f"用户 {user_id} 没有历史记录需要清空")
            return {"message": "没有历史记录需要清空", "deleted_count": 0}
        
        # 删除所有相关的回答
        deleted_answers = db.query(Answer).filter(Answer.question_id.in_(question_ids)).delete(synchronize_session=False)
        
        # 删除所有问题
        deleted_questions = db.query(Question).filter(Question.user_id == user_id).delete(synchronize_session=False)
        
        # 提交事务
        db.commit()
        
        total_deleted = deleted_questions + deleted_answers
        logger.info(f"成功清空用户 {user_id} 的历史记录，删除了 {deleted_questions} 个问题和 {deleted_answers} 个回答")
        log_security_event("HISTORY_CLEARED", f"用户 {user_id} 清空了历史记录，删除 {total_deleted} 条数据", request)
        
        return {
            "message": "历史记录已成功清空",
            "deleted_count": total_deleted,
            "questions_deleted": deleted_questions,
            "answers_deleted": deleted_answers
        }
        
    except SQLAlchemyError as e:
        logger.error(f"清空历史记录时数据库错误: {str(e)}")
        db.rollback()
        log_security_event("DATABASE_ERROR", f"清空历史记录失败: {str(e)}", request)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="数据库操作失败"
        )
    except Exception as e:
        logger.error(f"清空历史记录时发生未知错误: {str(e)}")
        db.rollback()
        log_security_event("UNKNOWN_ERROR", f"清空历史记录未知错误: {str(e)}", request)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误"
        )

# 健康检查接口
# 获取用户会话列表
@app.get("/api/sessions/{user_id}", response_model=List[SessionResponse])
@limiter.limit(get_rate_limit())
async def get_sessions(request: Request, user_id: int, db: Session = Depends(get_db)):
    validate_user_id(user_id)
    logger.info(f"获取用户 {user_id} 的会话列表")
    
    try:
        # 获取用户的所有会话，按更新时间倒序
        sessions = db.query(Session).filter(
            Session.user_id == user_id,
            Session.status == 1
        ).order_by(Session.update_time.desc()).all()
        
        # 为每个会话计算问题数量
        session_responses = []
        for session in sessions:
            question_count = db.query(Question).filter(
                Question.session_id == session.id
            ).count()
            
            session_responses.append(SessionResponse(
                id=session.id,
                user_id=session.user_id,
                title=session.title,
                create_time=session.create_time.isoformat(),
                update_time=session.update_time.isoformat(),
                status=session.status,
                question_count=question_count
            ))
        
        logger.info(f"返回 {len(session_responses)} 个会话记录")
        return session_responses
        
    except SQLAlchemyError as e:
        logger.error(f"获取会话列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取会话列表失败"
        )

# 获取指定会话的对话历史
@app.get("/api/sessions/{session_id}/history", response_model=List[QuestionResponse])
@limiter.limit(get_rate_limit())
async def get_session_history(request: Request, session_id: int, user_id: int, db: Session = Depends(get_db)):
    validate_user_id(user_id)
    logger.info(f"获取会话 {session_id} 的对话历史")
    
    try:
        # 验证会话是否存在且属于该用户
        session = db.query(Session).filter(
            Session.id == session_id,
            Session.user_id == user_id,
            Session.status == 1
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在或已关闭"
            )
        
        # 获取会话的所有问题和答案
        questions = db.query(Question).filter(
            Question.session_id == session_id
        ).order_by(Question.create_time.asc()).all()
        
        history = []
        for question in questions:
            answer = db.query(Answer).filter(Answer.question_id == question.id).first()
            history.append(QuestionResponse(
                id=question.id,
                question=question.question,
                answer=answer.answer if answer else None,
                create_time=question.create_time.isoformat(),
                status=question.status,
                session_id=question.session_id
            ))
        
        logger.info(f"返回会话 {session_id} 的 {len(history)} 条对话记录")
        return history
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"获取会话历史失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取会话历史失败"
        )

# 关闭会话
@app.put("/api/sessions/{session_id}/close")
@limiter.limit(get_rate_limit())
async def close_session(request: Request, session_id: int, user_id: int, db: Session = Depends(get_db)):
    validate_user_id(user_id)
    logger.info(f"关闭会话 {session_id}")
    
    try:
        # 验证会话是否存在且属于该用户
        session = db.query(Session).filter(
            Session.id == session_id,
            Session.user_id == user_id,
            Session.status == 1
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在或已关闭"
            )
        
        # 关闭会话
        session.status = 0
        session.update_time = datetime.now()
        db.commit()
        
        logger.info(f"会话 {session_id} 已关闭")
        return {"message": "会话已关闭", "session_id": session_id}
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"关闭会话失败: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="关闭会话失败"
        )

# 删除会话
@app.delete("/api/sessions/{session_id}")
@limiter.limit(get_rate_limit())
async def delete_session(request: Request, session_id: int, user_id: int, db: Session = Depends(get_db)):
    validate_user_id(user_id)
    logger.info(f"删除会话 {session_id}")
    
    try:
        # 验证会话是否存在且属于该用户
        session = db.query(Session).filter(
            Session.id == session_id,
            Session.user_id == user_id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )
        
        # 删除会话相关的所有答案
        questions = db.query(Question).filter(Question.session_id == session_id).all()
        for question in questions:
            # 删除答案
            db.query(Answer).filter(Answer.question_id == question.id).delete()
        
        # 删除会话相关的所有问题
        db.query(Question).filter(Question.session_id == session_id).delete()
        
        # 删除会话
        db.delete(session)
        db.commit()
        
        logger.info(f"会话 {session_id} 及其相关数据已删除")
        return {"message": "会话已删除", "session_id": session_id}
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"删除会话失败: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除会话失败"
        )

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}