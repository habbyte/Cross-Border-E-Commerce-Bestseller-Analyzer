"""
向量搜索 API 端点
基于向量相似度进行信息检索
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Optional
from app.services.retrieval_service import get_retrieval_service
from app.services.vector_service import vector_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/search", tags=["search"])


class SearchResult(BaseModel):
    """搜索结果模型"""
    id: str
    name: str
    source_url: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    similarity: float


class SearchResponse(BaseModel):
    """搜索响应模型"""
    query: str
    results: List[SearchResult]
    total: int


@router.get("/vector", response_model=SearchResponse)
async def vector_search(
    query: str = Query(..., description="搜索查询文本"),
    top_k: int = Query(5, ge=1, le=50, description="返回前 k 个结果"),
    min_similarity: float = Query(0.0, ge=0.0, le=1.0, description="最小相似度阈值")
):
    """
    向量搜索接口
    
    根据用户输入的查询文本，返回最相关的类别数据
    """
    try:
        retrieval_service = get_retrieval_service()
        results = retrieval_service.search(
            query=query,
            top_k=top_k,
            min_similarity=min_similarity
        )
        
        # 转换为响应格式
        search_results = [
            SearchResult(
                id=str(result.get('id', '')),
                name=result.get('name', ''),
                source_url=result.get('source_url'),
                created_at=result.get('created_at'),
                updated_at=result.get('updated_at'),
                similarity=result.get('similarity', 0.0)
            )
            for result in results
        ]
        
        return SearchResponse(
            query=query,
            results=search_results,
            total=len(search_results)
        )
    
    except Exception as e:
        logger.error(f"向量搜索错误: {e}")
        raise HTTPException(status_code=500, detail=f"搜索服务错误: {str(e)}")


@router.post("/vectorize")
async def vectorize_categories(
    csv_path: Optional[str] = Query(None, description="CSV 文件路径，默认为 categories.csv"),
    output_path: Optional[str] = Query(None, description="输出 JSON 文件路径")
):
    """
    向量化类别数据接口
    
    从 CSV 文件加载数据，进行向量化，并保存结果
    """
    try:
        # 默认路径
        if not csv_path:
            csv_path = "categories.csv"
        if not output_path:
            output_path = "data/vectorized_categories.json"
        
        # 加载数据
        categories = vector_service.load_categories_from_csv(csv_path)
        if not categories:
            raise HTTPException(status_code=404, detail=f"未找到类别数据或文件为空: {csv_path}")
        
        # 向量化
        vectorized_categories = vector_service.vectorize_categories(categories)
        if not vectorized_categories:
            raise HTTPException(status_code=500, detail="向量化失败，未生成任何向量")
        
        # 保存结果
        vector_service.save_vectorized_data(vectorized_categories, output_path)
        
        # 重新加载检索服务
        from app.services.retrieval_service import RetrievalService, _retrieval_service
        import app.services.retrieval_service as retrieval_module
        retrieval_module._retrieval_service = RetrievalService(vectorized_categories)
        
        return {
            "message": "向量化完成",
            "total": len(vectorized_categories),
            "output_path": output_path
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"向量化错误: {e}")
        raise HTTPException(status_code=500, detail=f"向量化服务错误: {str(e)}")

