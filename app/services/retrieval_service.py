"""
信息检索服务模块
基于向量相似度进行搜索
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import logging
from app.services.vector_service import vector_service

logger = logging.getLogger(__name__)


class RetrievalService:
    """信息检索服务类"""
    
    def __init__(self, vectorized_data: Optional[List[Dict[str, Any]]] = None):
        """
        初始化检索服务
        
        Args:
            vectorized_data: 已向量化的数据列表
        """
        self.vectorized_data = vectorized_data or []
        self._build_index()
    
    def _build_index(self):
        """构建索引（这里使用简单的内存索引）"""
        if not self.vectorized_data:
            logger.warning("没有向量化数据，索引为空")
            return
        
        # 验证数据格式
        valid_data = []
        for item in self.vectorized_data:
            if 'embedding' in item and item['embedding']:
                valid_data.append(item)
        
        self.vectorized_data = valid_data
        logger.info(f"索引构建完成，包含 {len(self.vectorized_data)} 条数据")
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        计算两个向量的余弦相似度
        
        Args:
            vec1: 向量1
            vec2: 向量2
        
        Returns:
            相似度分数 (0-1)
        """
        vec1_array = np.array(vec1)
        vec2_array = np.array(vec2)
        
        # 计算点积
        dot_product = np.dot(vec1_array, vec2_array)
        
        # 计算向量长度
        norm1 = np.linalg.norm(vec1_array)
        norm2 = np.linalg.norm(vec2_array)
        
        # 避免除零
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        # 余弦相似度
        similarity = dot_product / (norm1 * norm2)
        return float(similarity)
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        min_similarity: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        基于向量相似度搜索最相关的内容
        
        Args:
            query: 查询文本
            top_k: 返回前 k 个最相关的结果
            min_similarity: 最小相似度阈值
        
        Returns:
            搜索结果列表，每个结果包含原始数据和相似度分数
        """
        if not self.vectorized_data:
            logger.warning("没有向量化数据，无法进行搜索")
            return []
        
        if not query or not query.strip():
            logger.warning("查询文本为空")
            return []
        
        try:
            # 将查询文本向量化
            query_embedding = vector_service.get_embedding(query.strip())
        except Exception as e:
            logger.error(f"查询文本向量化失败: {e}")
            return []
        
        # 计算与所有数据的相似度
        results = []
        for item in self.vectorized_data:
            if 'embedding' not in item or not item['embedding']:
                continue
            
            similarity = self.cosine_similarity(query_embedding, item['embedding'])
            
            if similarity >= min_similarity:
                # 创建结果项（不包含 embedding，减少返回数据量）
                result_item = {
                    'id': item.get('id'),
                    'name': item.get('name'),
                    'source_url': item.get('source_url'),
                    'created_at': item.get('created_at'),
                    'updated_at': item.get('updated_at'),
                    'similarity': similarity
                }
                results.append(result_item)
        
        # 按相似度降序排序
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        # 返回前 top_k 个结果
        top_results = results[:top_k]
        
        logger.info(f"搜索完成，找到 {len(top_results)} 个相关结果")
        return top_results
    
    def load_data(self, data: List[Dict[str, Any]]):
        """
        加载向量化数据
        
        Args:
            data: 向量化的数据列表
        """
        self.vectorized_data = data
        self._build_index()
    
    def add_data(self, item: Dict[str, Any]):
        """
        添加新的向量化数据项
        
        Args:
            item: 包含 embedding 的数据项
        """
        if 'embedding' in item and item['embedding']:
            self.vectorized_data.append(item)
            logger.info(f"已添加新数据项: {item.get('id', 'unknown')}")


# 全局检索服务实例（延迟初始化）
_retrieval_service: Optional[RetrievalService] = None


def get_retrieval_service() -> RetrievalService:
    """获取全局检索服务实例"""
    global _retrieval_service
    if _retrieval_service is None:
        # 尝试从文件加载向量化数据
        try:
            vectorized_data = vector_service.load_vectorized_data("data/vectorized_categories.json")
            _retrieval_service = RetrievalService(vectorized_data)
        except Exception as e:
            logger.warning(f"加载向量化数据失败，使用空索引: {e}")
            _retrieval_service = RetrievalService()
    return _retrieval_service

