"""
对话历史管理服务
支持本地保存和管理多个对话会话（类似 chatbox）
"""

import json
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ChatHistoryService:
    """对话历史管理服务类"""
    
    def __init__(self, storage_dir: str = "data/chat_history"):
        """
        初始化对话历史服务
        
        Args:
            storage_dir: 存储目录路径
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.sessions_file = self.storage_dir / "sessions.json"
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.current_session_id: Optional[str] = None
        
        # 加载会话列表
        self._load_sessions()
    
    def _load_sessions(self):
        """从文件加载会话列表"""
        try:
            if self.sessions_file.exists():
                with open(self.sessions_file, 'r', encoding='utf-8') as f:
                    self.sessions = json.load(f)
                logger.info(f"已加载 {len(self.sessions)} 个会话")
            else:
                self.sessions = {}
                logger.info("未找到会话文件，创建新会话列表")
        except Exception as e:
            logger.error(f"加载会话列表失败: {e}")
            self.sessions = {}
    
    def _save_sessions(self):
        """保存会话列表到文件"""
        try:
            with open(self.sessions_file, 'w', encoding='utf-8') as f:
                json.dump(self.sessions, f, ensure_ascii=False, indent=2)
            logger.debug("会话列表已保存")
        except Exception as e:
            logger.error(f"保存会话列表失败: {e}")
            raise
    
    def _get_session_file(self, session_id: str) -> Path:
        """获取会话历史文件路径"""
        return self.storage_dir / f"session_{session_id}.json"
    
    def create_session(self, title: Optional[str] = None) -> str:
        """
        创建新会话
        
        Args:
            title: 会话标题（可选）
        
        Returns:
            会话 ID
        """
        session_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        session_info = {
            "id": session_id,
            "title": title or f"新对话 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "created_at": now,
            "updated_at": now,
            "message_count": 0
        }
        
        self.sessions[session_id] = session_info
        self.current_session_id = session_id
        
        # 创建空的会话历史文件
        session_file = self._get_session_file(session_id)
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        
        self._save_sessions()
        logger.info(f"创建新会话: {session_id} - {session_info['title']}")
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取会话信息
        
        Args:
            session_id: 会话 ID
        
        Returns:
            会话信息字典
        """
        return self.sessions.get(session_id)
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        列出所有会话
        
        Returns:
            会话列表，按更新时间倒序
        """
        sessions_list = list(self.sessions.values())
        # 按更新时间倒序排序
        sessions_list.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
        return sessions_list
    
    def delete_session(self, session_id: str) -> bool:
        """
        删除会话
        
        Args:
            session_id: 会话 ID
        
        Returns:
            是否删除成功
        """
        if session_id not in self.sessions:
            logger.warning(f"会话不存在: {session_id}")
            return False
        
        try:
            # 删除会话文件
            session_file = self._get_session_file(session_id)
            if session_file.exists():
                session_file.unlink()
            
            # 从会话列表中移除
            del self.sessions[session_id]
            
            # 如果删除的是当前会话，清空当前会话 ID
            if self.current_session_id == session_id:
                self.current_session_id = None
            
            self._save_sessions()
            logger.info(f"已删除会话: {session_id}")
            return True
        except Exception as e:
            logger.error(f"删除会话失败: {e}")
            return False
    
    def update_session_title(self, session_id: str, title: str) -> bool:
        """
        更新会话标题
        
        Args:
            session_id: 会话 ID
            title: 新标题
        
        Returns:
            是否更新成功
        """
        if session_id not in self.sessions:
            logger.warning(f"会话不存在: {session_id}")
            return False
        
        self.sessions[session_id]['title'] = title
        self.sessions[session_id]['updated_at'] = datetime.now().isoformat()
        self._save_sessions()
        logger.info(f"已更新会话标题: {session_id} - {title}")
        return True
    
    def get_current_session_id(self) -> Optional[str]:
        """获取当前会话 ID"""
        return self.current_session_id
    
    def set_current_session(self, session_id: str) -> bool:
        """
        设置当前会话
        
        Args:
            session_id: 会话 ID
        
        Returns:
            是否设置成功
        """
        if session_id not in self.sessions:
            logger.warning(f"会话不存在: {session_id}")
            return False
        
        self.current_session_id = session_id
        logger.info(f"已切换到会话: {session_id}")
        return True
    
    def load_messages(self, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        加载会话消息历史
        
        Args:
            session_id: 会话 ID，如果为 None 则使用当前会话
        
        Returns:
            消息列表
        """
        if session_id is None:
            session_id = self.current_session_id
        
        if not session_id:
            logger.warning("没有指定会话 ID 且没有当前会话")
            return []
        
        if session_id not in self.sessions:
            logger.warning(f"会话不存在: {session_id}")
            return []
        
        session_file = self._get_session_file(session_id)
        if not session_file.exists():
            logger.warning(f"会话文件不存在: {session_file}")
            return []
        
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                messages = json.load(f)
            logger.debug(f"已加载会话 {session_id} 的 {len(messages)} 条消息")
            return messages
        except Exception as e:
            logger.error(f"加载会话消息失败: {e}")
            return []
    
    def save_message(
        self,
        role: str,
        content: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        保存消息到会话历史
        
        Args:
            role: 消息角色 ("user", "assistant", "system")
            content: 消息内容
            session_id: 会话 ID，如果为 None 则使用当前会话
            metadata: 额外的元数据（可选）
        
        Returns:
            消息 ID，如果保存失败则返回 None
        """
        if session_id is None:
            session_id = self.current_session_id
        
        # 如果没有会话，创建一个
        if not session_id:
            session_id = self.create_session()
        
        if session_id not in self.sessions:
            logger.warning(f"会话不存在: {session_id}")
            return None
        
        # 构建消息对象
        message_id = str(uuid.uuid4())
        message = {
            "id": message_id,
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        # 加载现有消息
        messages = self.load_messages(session_id)
        messages.append(message)
        
        # 保存消息
        session_file = self._get_session_file(session_id)
        try:
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(messages, f, ensure_ascii=False, indent=2)
            
            # 更新会话信息
            self.sessions[session_id]['updated_at'] = datetime.now().isoformat()
            self.sessions[session_id]['message_count'] = len(messages)
            self._save_sessions()
            
            logger.debug(f"已保存消息到会话 {session_id}")
            return message_id
        except Exception as e:
            logger.error(f"保存消息失败: {e}")
            return None
    
    def clear_session_messages(self, session_id: Optional[str] = None) -> bool:
        """
        清空会话消息
        
        Args:
            session_id: 会话 ID，如果为 None 则使用当前会话
        
        Returns:
            是否清空成功
        """
        if session_id is None:
            session_id = self.current_session_id
        
        if not session_id:
            logger.warning("没有指定会话 ID 且没有当前会话")
            return False
        
        session_file = self._get_session_file(session_id)
        try:
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            
            # 更新会话信息
            self.sessions[session_id]['updated_at'] = datetime.now().isoformat()
            self.sessions[session_id]['message_count'] = 0
            self._save_sessions()
            
            logger.info(f"已清空会话 {session_id} 的消息")
            return True
        except Exception as e:
            logger.error(f"清空会话消息失败: {e}")
            return False


# 创建全局服务实例
chat_history_service = ChatHistoryService()

