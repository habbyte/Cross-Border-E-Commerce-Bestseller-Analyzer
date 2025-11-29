"""
DeepSeek API 服务模块
提供对话回复功能
"""

import os
import httpx
from typing import Optional, Dict, Any, List
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class DeepSeekService:
    """DeepSeek API 服务类"""
    
    def __init__(self):
        """初始化 DeepSeek 服务"""
        # 从环境变量或配置中获取 API Key
        self.api_key = os.getenv("DEEPSEEK_API_KEY", getattr(settings, "deepseek_api_key", ""))
        self.base_url = "https://api.deepseek.com/v1"
        self.model = "deepseek-chat"  # DeepSeek 的对话模型
        
        if not self.api_key:
            logger.warning("DeepSeek API Key 未配置，对话功能将不可用")
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = 2000,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        调用 DeepSeek API 进行对话
        
        Args:
            messages: 对话消息列表，格式: [{"role": "user", "content": "..."}]
            temperature: 温度参数，控制回复的随机性 (0-1)
            max_tokens: 最大生成 token 数
            stream: 是否使用流式响应
        
        Returns:
            API 响应字典，包含回复内容
        """
        if not self.api_key:
            raise ValueError("DeepSeek API Key 未配置，请在环境变量中设置 DEEPSEEK_API_KEY")
        
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        if stream:
            payload["stream"] = True
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"DeepSeek API 请求失败: {e}")
            raise Exception(f"DeepSeek API 请求失败: {str(e)}")
        except Exception as e:
            logger.error(f"DeepSeek API 调用异常: {e}")
            raise
    
    def chat_simple(self, user_message: str, system_prompt: Optional[str] = None) -> str:
        """
        简化的对话接口
        
        Args:
            user_message: 用户消息
            system_prompt: 系统提示词（可选）
        
        Returns:
            回复内容字符串
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_message})
        
        try:
            response = self.chat(messages)
            # 提取回复内容
            if "choices" in response and len(response["choices"]) > 0:
                return response["choices"][0]["message"]["content"]
            else:
                raise ValueError("API 响应格式异常")
        except Exception as e:
            logger.error(f"获取 DeepSeek 回复失败: {e}")
            raise


# 创建全局服务实例
deepseek_service = DeepSeekService()

