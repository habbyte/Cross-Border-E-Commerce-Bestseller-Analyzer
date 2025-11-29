"""
向量化服务模块
使用 embedding 模型将文本转换为向量
"""

import os
import csv
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import logging
from app.services.deepseek_service import deepseek_service
import httpx

logger = logging.getLogger(__name__)


class VectorService:
    """向量化服务类"""
    
    def __init__(self):
        """初始化向量化服务"""
        self.api_key = os.getenv("DEEPSEEK_API_KEY", getattr(deepseek_service, "api_key", ""))
        self.base_url = "https://api.deepseek.com/v1"
        self.embedding_model = "deepseek-embedding"  # DeepSeek 的 embedding 模型
        self.embeddings_cache: Dict[str, List[float]] = {}  # 缓存已生成的向量
        
        if not self.api_key:
            logger.warning("DeepSeek API Key 未配置，向量化功能将不可用")
    
    def get_embedding(self, text: str) -> List[float]:
        """
        获取文本的向量表示
        
        Args:
            text: 输入文本
        
        Returns:
            向量列表（浮点数列表）
        """
        if not text or not text.strip():
            raise ValueError("输入文本不能为空")
        
        # 检查缓存
        text_key = text.strip()
        if text_key in self.embeddings_cache:
            return self.embeddings_cache[text_key]
        
        if not self.api_key:
            raise ValueError("DeepSeek API Key 未配置，请在环境变量中设置 DEEPSEEK_API_KEY")
        
        url = f"{self.base_url}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.embedding_model,
            "input": text
        }
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()
                
                # 提取向量
                if "data" in result and len(result["data"]) > 0:
                    embedding = result["data"][0]["embedding"]
                    # 缓存结果
                    self.embeddings_cache[text_key] = embedding
                    return embedding
                else:
                    raise ValueError("API 响应格式异常")
        except httpx.HTTPError as e:
            logger.error(f"DeepSeek Embedding API 请求失败: {e}")
            raise Exception(f"DeepSeek Embedding API 请求失败: {str(e)}")
        except Exception as e:
            logger.error(f"获取 embedding 失败: {e}")
            raise
    
    def load_categories_from_csv(self, csv_path: str) -> List[Dict[str, Any]]:
        """
        从 CSV 文件加载类别数据
        
        Args:
            csv_path: CSV 文件路径
        
        Returns:
            类别数据列表
        """
        categories = []
        csv_file = Path(csv_path)
        
        if not csv_file.exists():
            logger.warning(f"CSV 文件不存在: {csv_path}")
            return categories
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # 构建用于向量化的文本（包含 id, name, source_url）
                    text_parts = []
                    if row.get('name'):
                        text_parts.append(row['name'])
                    if row.get('source_url'):
                        text_parts.append(row['source_url'])
                    
                    if text_parts:
                        categories.append({
                            'id': row.get('id', ''),
                            'name': row.get('name', ''),
                            'source_url': row.get('source_url', ''),
                            'created_at': row.get('created_at', ''),
                            'updated_at': row.get('updated_at', ''),
                            'text': ' '.join(text_parts)  # 用于向量化的完整文本
                        })
        except Exception as e:
            logger.error(f"加载 CSV 文件失败: {e}")
            raise
        
        logger.info(f"成功加载 {len(categories)} 条类别数据")
        return categories
    
    def vectorize_categories(
        self,
        categories: List[Dict[str, Any]],
        batch_size: int = 10
    ) -> List[Dict[str, Any]]:
        """
        对类别数据进行向量化
        
        Args:
            categories: 类别数据列表
            batch_size: 批处理大小（DeepSeek API 可能支持批量请求）
        
        Returns:
            包含向量的类别数据列表
        """
        vectorized_categories = []
        
        for i, category in enumerate(categories):
            try:
                text = category.get('text', category.get('name', ''))
                if not text:
                    logger.warning(f"类别 {category.get('id')} 没有可向量化的文本，跳过")
                    continue
                
                embedding = self.get_embedding(text)
                category_with_vector = {
                    **category,
                    'embedding': embedding
                }
                vectorized_categories.append(category_with_vector)
                
                # 添加进度日志
                if (i + 1) % 10 == 0:
                    logger.info(f"已向量化 {i + 1}/{len(categories)} 条数据")
            except Exception as e:
                logger.error(f"向量化类别 {category.get('id')} 失败: {e}")
                continue
        
        logger.info(f"成功向量化 {len(vectorized_categories)} 条类别数据")
        return vectorized_categories
    
    def save_vectorized_data(
        self,
        vectorized_categories: List[Dict[str, Any]],
        output_path: str
    ):
        """
        保存向量化数据到 JSON 文件
        
        Args:
            vectorized_categories: 向量化的类别数据
            output_path: 输出文件路径
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 将 numpy 数组转换为列表（如果存在）
        data_to_save = []
        for item in vectorized_categories:
            item_copy = item.copy()
            if 'embedding' in item_copy:
                # 确保 embedding 是列表格式
                if isinstance(item_copy['embedding'], np.ndarray):
                    item_copy['embedding'] = item_copy['embedding'].tolist()
            data_to_save.append(item_copy)
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=2)
            logger.info(f"向量化数据已保存到: {output_path}")
        except Exception as e:
            logger.error(f"保存向量化数据失败: {e}")
            raise
    
    def load_vectorized_data(self, json_path: str) -> List[Dict[str, Any]]:
        """
        从 JSON 文件加载向量化数据
        
        Args:
            json_path: JSON 文件路径
        
        Returns:
            向量化的类别数据列表
        """
        json_file = Path(json_path)
        
        if not json_file.exists():
            logger.warning(f"JSON 文件不存在: {json_path}")
            return []
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"成功加载 {len(data)} 条向量化数据")
            return data
        except Exception as e:
            logger.error(f"加载向量化数据失败: {e}")
            raise


# 创建全局服务实例
vector_service = VectorService()

