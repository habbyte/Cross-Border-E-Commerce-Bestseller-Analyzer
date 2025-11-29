"""
对话 API 端点
集成 DeepSeek API 提供对话回复功能
支持对话历史管理（类似 chatbox）
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict
from app.services.deepseek_service import deepseek_service
from app.services.chat_history_service import chat_history_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatMessage(BaseModel):
    """聊天消息模型"""
    role: str  # "user", "assistant", "system"
    content: str


class ChatRequest(BaseModel):
    """聊天请求模型"""
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2000


class ChatResponse(BaseModel):
    """聊天响应模型"""
    reply: str
    model: str
    usage: Optional[Dict] = None
    session_id: Optional[str] = None
    message_id: Optional[str] = None


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    session_id: Optional[str] = Query(None, description="会话 ID，如果不提供则创建新会话"),
    save_history: bool = Query(True, description="是否保存对话历史")
):
    """
    对话接口
    
    接收用户消息，调用 DeepSeek API 生成回复
    支持对话历史管理
    """
    try:
        # 如果没有提供 session_id，创建新会话
        if not session_id:
            session_id = chat_history_service.create_session()
        else:
            # 检查会话是否存在
            if not chat_history_service.get_session(session_id):
                session_id = chat_history_service.create_session()
            else:
                chat_history_service.set_current_session(session_id)
        
        # 转换消息格式
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        # 如果保存历史，加载历史消息（用于上下文）
        if save_history:
            history_messages = chat_history_service.load_messages(session_id)
            # 将历史消息添加到消息列表前面（保留上下文）
            if history_messages:
                # 只保留最近的对话历史（避免 token 过多）
                recent_history = history_messages[-10:]  # 保留最近 10 条
                history_for_api = [
                    {"role": msg["role"], "content": msg["content"]}
                    for msg in recent_history
                ]
                # 合并历史消息和当前消息（避免重复最后一条用户消息）
                if messages and history_for_api:
                    last_history = history_for_api[-1]
                    first_current = messages[0]
                    if last_history["role"] == first_current["role"] and last_history["content"] == first_current["content"]:
                        messages = history_for_api + messages[1:]
                    else:
                        messages = history_for_api + messages
                else:
                    messages = history_for_api + messages
        
        # 调用 DeepSeek API
        response = deepseek_service.chat(
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        # 提取回复内容
        if "choices" in response and len(response["choices"]) > 0:
            reply = response["choices"][0]["message"]["content"]
            model = response.get("model", "deepseek-chat")
            usage = response.get("usage")
            
            # 保存对话历史
            message_id = None
            if save_history:
                # 保存用户消息（取最后一条）
                if request.messages:
                    last_user_msg = request.messages[-1]
                    if last_user_msg.role == "user":
                        chat_history_service.save_message(
                            role="user",
                            content=last_user_msg.content,
                            session_id=session_id
                        )
                
                # 保存助手回复
                message_id = chat_history_service.save_message(
                    role="assistant",
                    content=reply,
                    session_id=session_id,
                    metadata={"model": model, "usage": usage}
                )
            
            return ChatResponse(
                reply=reply,
                model=model,
                usage=usage,
                session_id=session_id,
                message_id=message_id
            )
        else:
            raise HTTPException(status_code=500, detail="API 响应格式异常")
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"对话接口错误: {e}")
        raise HTTPException(status_code=500, detail=f"对话服务错误: {str(e)}")


@router.post("/simple")
async def chat_simple(
    message: str,
    system_prompt: Optional[str] = None,
    session_id: Optional[str] = Query(None, description="会话 ID"),
    save_history: bool = Query(True, description="是否保存对话历史")
):
    """
    简化的对话接口
    
    直接接收用户消息字符串，返回回复
    支持对话历史管理
    """
    try:
        # 如果没有提供 session_id，创建新会话
        if not session_id:
            session_id = chat_history_service.create_session()
        else:
            if not chat_history_service.get_session(session_id):
                session_id = chat_history_service.create_session()
            else:
                chat_history_service.set_current_session(session_id)
        
        # 构建消息列表（包含历史消息）
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        if save_history:
            history_messages = chat_history_service.load_messages(session_id)
            if history_messages:
                recent_history = history_messages[-10:]
                for msg in recent_history:
                    messages.append({"role": msg["role"], "content": msg["content"]})
        
        messages.append({"role": "user", "content": message})
        
        # 调用 DeepSeek API
        response = deepseek_service.chat(messages)
        if "choices" in response and len(response["choices"]) > 0:
            reply = response["choices"][0]["message"]["content"]
            
            # 保存对话历史
            if save_history:
                chat_history_service.save_message(
                    role="user",
                    content=message,
                    session_id=session_id
                )
                chat_history_service.save_message(
                    role="assistant",
                    content=reply,
                    session_id=session_id
                )
            
            return {
                "reply": reply,
                "session_id": session_id
            }
        else:
            raise HTTPException(status_code=500, detail="API 响应格式异常")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"简化对话接口错误: {e}")
        raise HTTPException(status_code=500, detail=f"对话服务错误: {str(e)}")


# ========== 对话历史管理 API ==========

@router.get("/sessions")
async def list_sessions():
    """
    获取所有会话列表
    """
    try:
        sessions = chat_history_service.list_sessions()
        return {"sessions": sessions, "total": len(sessions)}
    except Exception as e:
        logger.error(f"获取会话列表错误: {e}")
        raise HTTPException(status_code=500, detail=f"获取会话列表失败: {str(e)}")


@router.post("/sessions")
async def create_session(title: Optional[str] = None):
    """
    创建新会话
    """
    try:
        session_id = chat_history_service.create_session(title)
        session = chat_history_service.get_session(session_id)
        return {"session_id": session_id, "session": session}
    except Exception as e:
        logger.error(f"创建会话错误: {e}")
        raise HTTPException(status_code=500, detail=f"创建会话失败: {str(e)}")


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """
    获取会话信息和消息历史
    """
    try:
        session = chat_history_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        messages = chat_history_service.load_messages(session_id)
        return {
            "session": session,
            "messages": messages,
            "message_count": len(messages)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取会话错误: {e}")
        raise HTTPException(status_code=500, detail=f"获取会话失败: {str(e)}")


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """
    删除会话
    """
    try:
        success = chat_history_service.delete_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="会话不存在")
        return {"message": "会话已删除", "session_id": session_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除会话错误: {e}")
        raise HTTPException(status_code=500, detail=f"删除会话失败: {str(e)}")


@router.patch("/sessions/{session_id}/title")
async def update_session_title(session_id: str, title: str):
    """
    更新会话标题
    """
    try:
        success = chat_history_service.update_session_title(session_id, title)
        if not success:
            raise HTTPException(status_code=404, detail="会话不存在")
        session = chat_history_service.get_session(session_id)
        return {"message": "标题已更新", "session": session}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新会话标题错误: {e}")
        raise HTTPException(status_code=500, detail=f"更新会话标题失败: {str(e)}")


@router.delete("/sessions/{session_id}/messages")
async def clear_session_messages(session_id: str):
    """
    清空会话消息
    """
    try:
        success = chat_history_service.clear_session_messages(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="会话不存在")
        return {"message": "消息已清空", "session_id": session_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"清空会话消息错误: {e}")
        raise HTTPException(status_code=500, detail=f"清空会话消息失败: {str(e)}")

