"""
產品 API 端點
提供產品數據給前端
從 MongoDB Atlas 的 products collection 獲取數據
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from app.db.mongodb import mongodb
from app.config import settings
from bson import ObjectId
import re

router = APIRouter(prefix="/api/products", tags=["products"])


class ProductResponse(BaseModel):
    """產品響應模型（適配前端格式）"""
    id: str
    title: str
    platform: str
    price: float
    formattedPrice: str
    marginRate: float
    competitionScore: float
    competitionLevel: str
    category: str
    imageUrl: Optional[str] = None
    description: Optional[str] = None
    rating: Optional[float] = None
    reviewCount: Optional[int] = None
    productUrl: Optional[str] = None
    tags: List[str] = []
    productDetails: Optional[Dict[str, Any]] = None
    aboutThisItem: Optional[List[str]] = None
    colorOptions: Optional[List[Dict[str, Any]]] = None
    sizeOptions: Optional[List[str]] = None
    
    class Config:
        from_attributes = True


def _parse_price(price_str: Optional[str]) -> float:
    """解析價格字符串為數字"""
    if not price_str:
        return 0.0
    # 移除 $ 符號和逗號
    cleaned = re.sub(r'[$,]', '', str(price_str))
    try:
        return float(cleaned)
    except (ValueError, AttributeError):
        return 0.0


def _calculate_margin_rate(price: float) -> float:
    """計算利潤率（簡化版本，實際應該基於成本）"""
    # 這裡使用簡化邏輯，實際應該從數據庫或配置中獲取成本
    if price <= 0:
        return 0.0
    # 假設成本為價格的 60%，利潤率 = (價格 - 成本) / 成本 * 100
    cost = price * 0.6
    margin = ((price - cost) / cost) * 100
    return round(margin, 2)


def _calculate_competition_score(review_count: Optional[int], rating: Optional[float]) -> float:
    """計算競爭度分數（基於評論數和評分）"""
    score = 50.0  # 基礎分數
    
    # 評論數越多，競爭度越高
    if review_count:
        if review_count > 10000:
            score += 30
        elif review_count > 5000:
            score += 20
        elif review_count > 1000:
            score += 10
    
    # 評分越高，競爭度越高
    if rating:
        if rating >= 4.5:
            score += 20
        elif rating >= 4.0:
            score += 10
    
    return min(100.0, max(0.0, score))


def _get_competition_level(score: float) -> str:
    """根據競爭度分數返回等級"""
    if score < 30:
        return "low"
    elif score < 70:
        return "medium"
    else:
        return "high"


def _mongodb_product_to_response(mongo_product: Dict[str, Any]) -> ProductResponse:
    """將 MongoDB 產品文檔轉換為前端響應格式"""
    try:
        # 獲取產品 ID（可能是 _id 或 id 字段）
        product_id = str(mongo_product.get("_id", mongo_product.get("id", "")))
        
        # 解析價格
        price = _parse_price(mongo_product.get("price"))
        margin_rate = _calculate_margin_rate(price)
        
        # 處理 NaN 值
        import math
        review_count = mongo_product.get("review_count")
        if review_count is not None and (isinstance(review_count, float) and math.isnan(review_count)):
            review_count = None
        
        rating = mongo_product.get("rating")
        if rating is not None and (isinstance(rating, float) and math.isnan(rating)):
            rating = None
        
        competition_score = _calculate_competition_score(review_count, rating)
        competition_level = _get_competition_level(competition_score)
        
        # 獲取分類
        category = "Electronics"  # 默認值
        # 優先從 categories 數組獲取
        categories = mongo_product.get("categories", [])
        if categories and isinstance(categories, list) and len(categories) > 0:
            category = str(categories[0])
        # 如果沒有 categories，嘗試從 category_path 提取
        elif mongo_product.get("category_path"):
            try:
                parts = [p.strip() for p in str(mongo_product.get("category_path")).split(">") if p.strip() and p.strip() != "›"]
                if parts:
                    category = parts[0]
            except Exception:
                pass  # 如果解析失敗，使用默認值
        
        # 格式化價格
        price_str = mongo_product.get("price", "")
        formatted_price = price_str if price_str else f"${price:.2f}"
        
        # 提取標籤（從 product_details 或其他字段）
        tags = []
        product_details = mongo_product.get("product_details")
        if product_details and isinstance(product_details, dict):
            # 可以從 product_details 中提取關鍵信息作為標籤
            brand = product_details.get("Brand")
            if brand:
                # 清理品牌名稱（移除特殊字符）
                brand_clean = str(brand).strip("‎").strip()
                if brand_clean:
                    tags.append(brand_clean)
        
        # 處理可能為 NaN 的字符串字段
        import math
        product_url = mongo_product.get("product_url")
        if product_url is not None and (isinstance(product_url, float) and math.isnan(product_url)):
            product_url = None
        
        # 從 source_url 推斷平台（如果沒有 platform 字段）
        platform = mongo_product.get("platform", "amazon")
        if not platform or (isinstance(platform, float) and math.isnan(platform)):
            source_url = mongo_product.get("source_url", "")
            if isinstance(source_url, float) and math.isnan(source_url):
                source_url = ""
            if "amazon" in str(source_url).lower():
                platform = "amazon"
            elif "walmart" in str(source_url).lower():
                platform = "walmart"
            elif "ebay" in str(source_url).lower():
                platform = "ebay"
            elif "shopee" in str(source_url).lower():
                platform = "shopee"
            else:
                platform = "amazon"  # 默認值
        
        return ProductResponse(
            id=f"prod-{product_id}",
            title=mongo_product.get("name", ""),
            platform=platform,
            price=price,
            formattedPrice=formatted_price,
            marginRate=margin_rate,
            competitionScore=competition_score,
            competitionLevel=competition_level,
            category=category,
            imageUrl=mongo_product.get("image_url"),
            description=mongo_product.get("description"),
            rating=rating,
            reviewCount=review_count,
            productUrl=product_url,
            tags=tags,
            productDetails=product_details if isinstance(product_details, dict) else None,
            aboutThisItem=mongo_product.get("about_this_item") if isinstance(mongo_product.get("about_this_item"), list) else None,
            colorOptions=mongo_product.get("color_options") if isinstance(mongo_product.get("color_options"), list) else None,
            sizeOptions=mongo_product.get("size_options") if isinstance(mongo_product.get("size_options"), list) else None,
        )
    except Exception as e:
        # 如果轉換失敗，返回基本信息
        import traceback
        product_id = str(mongo_product.get("_id", mongo_product.get("id", "unknown")))
        print(f"Error converting product {product_id}: {e}")
        traceback.print_exc()
        price = _parse_price(mongo_product.get("price"))
        return ProductResponse(
            id=f"prod-{product_id}",
            title=mongo_product.get("name", ""),
            platform=mongo_product.get("platform", "amazon"),
            price=price,
            formattedPrice=mongo_product.get("price", f"${price:.2f}"),
            marginRate=0.0,
            competitionScore=50.0,
            competitionLevel="medium",
            category="Electronics",
            imageUrl=mongo_product.get("image_url"),
            description=mongo_product.get("description"),
            rating=mongo_product.get("rating"),
            reviewCount=mongo_product.get("review_count"),
            productUrl=mongo_product.get("product_url"),
            tags=[],
            productDetails=None,
            aboutThisItem=None,
            colorOptions=None,
            sizeOptions=None,
        )


@router.get("/", response_model=List[ProductResponse])
def get_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    platform: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    status: str = Query("active", regex="^(active|draft|all)$"),
):
    """
    獲取產品列表（從 MongoDB Atlas）
    
    Args:
        skip: 跳過的記錄數
        limit: 返回的記錄數
        platform: 平台過濾（amazon, walmart, ebay 等）
        category: 分類過濾
        search: 搜索關鍵詞
        status: 狀態過濾（active, draft, all）
    """
    # 連接到 MongoDB
    db = mongodb.connect()
    if db is None:
        raise HTTPException(status_code=500, detail="MongoDB connection failed. Please check MONGODB_URL configuration.")
    
    try:
        collection = db["products"]
        
        # 構建查詢過濾條件
        query_filter = {}
        
        # 狀態過濾（默認只返回 active）
        if status != "all":
            filter_status = status if status in ("active", "draft") else "active"
            # 如果過濾 active，也包含沒有 status 字段的文檔（兼容舊數據）
            if filter_status == "active":
                query_filter["$or"] = [
                    {"status": "active"},
                    {"status": {"$exists": False}}  # 沒有 status 字段的文檔視為 active
                ]
            else:
                query_filter["status"] = filter_status
        
        # 平台過濾
        if platform:
            query_filter["platform"] = platform
        
        # 構建分類和搜索的組合查詢
        or_conditions = []
        
        # 分類過濾
        if category:
            # 支持從 categories 數組或 category_path 字符串中搜索
            or_conditions.extend([
                {"categories": {"$in": [category]}},
                {"category_path": {"$regex": category, "$options": "i"}}
            ])
        
        # 搜索過濾（在 name 和 description 中搜索）
        if search:
            or_conditions.extend([
                {"name": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}}
            ])
        
        # 如果有分類或搜索條件，添加到查詢中
        if or_conditions:
            if category and search:
                # 同時有分類和搜索時，使用 $and 確保兩個條件都滿足
                query_filter["$and"] = [
                    {"$or": or_conditions[:2]},  # 分類條件
                    {"$or": or_conditions[2:]}  # 搜索條件
                ]
            else:
                # 只有分類或只有搜索時，使用 $or
                query_filter["$or"] = or_conditions
        
        # 執行查詢（按創建時間倒序，支持分頁）
        cursor = collection.find(query_filter).sort("created_at", -1).skip(skip).limit(limit)
        products = list(cursor)
        
        # 轉換為響應格式，處理可能的錯誤
        result = []
        for p in products:
            try:
                result.append(_mongodb_product_to_response(p))
            except Exception as e:
                import traceback
                product_id = str(p.get("_id", "unknown"))
                print(f"Error processing product {product_id}: {e}")
                traceback.print_exc()
                # 跳過有問題的產品，繼續處理其他產品
                continue
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error in get_products: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch products: {str(e)}")
    # 注意：不在這裡關閉連接，保持連接池打開以便重用


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: str):
    """
    獲取單個產品詳情（從 MongoDB Atlas）
    
    Args:
        product_id: 產品 ID（格式: prod-{id} 或 MongoDB ObjectId 字符串）
    """
    # 連接到 MongoDB
    db = mongodb.connect()
    if db is None:
        raise HTTPException(status_code=500, detail="MongoDB connection failed. Please check MONGODB_URL configuration.")
    
    try:
        collection = db["products"]
        
        # 解析產品 ID
        if product_id.startswith("prod-"):
            product_id = product_id.replace("prod-", "")
        
        # 嘗試使用 ObjectId 查找
        try:
            product = collection.find_one({"_id": ObjectId(product_id)})
        except Exception:
            # 如果不是有效的 ObjectId，嘗試使用 id 字段（數字）
            try:
                product_id_int = int(product_id)
                product = collection.find_one({"id": product_id_int})
            except ValueError:
                # 如果都不是，嘗試直接使用字符串作為 _id
                product = collection.find_one({"_id": product_id})
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return _mongodb_product_to_response(product)
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error in get_product: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch product: {str(e)}")
    # 注意：不在這裡關閉連接，保持連接池打開以便重用


@router.get("/stats/summary")
def get_stats():
    """獲取產品統計信息（從 MongoDB Atlas）"""
    # 連接到 MongoDB
    db = mongodb.connect()
    if db is None:
        raise HTTPException(status_code=500, detail="MongoDB connection failed. Please check MONGODB_URL configuration.")
    
    try:
        collection = db["products"]
        
        # 獲取總數
        total_count = collection.count_documents({})
        
        # 獲取 active 狀態的產品數
        active_count = collection.count_documents({"status": "active"})
        
        # 按平台統計（使用聚合管道）
        pipeline = [
            {"$group": {
                "_id": {"$ifNull": ["$platform", "unknown"]},
                "count": {"$sum": 1}
            }},
            {"$project": {
                "platform": {"$ifNull": ["$_id", "unknown"]},
                "count": 1,
                "_id": 0
            }}
        ]
        
        platforms = {}
        for result in collection.aggregate(pipeline):
            platform = result.get("platform", "unknown")
            # 處理 NaN 值
            if isinstance(platform, float):
                import math
                if math.isnan(platform):
                    platform = "unknown"
            platforms[str(platform)] = result.get("count", 0)
        
        return {
            "totalProducts": total_count,
            "activeProducts": active_count,
            "platforms": platforms,
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error in get_stats: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch stats: {str(e)}")
    # 注意：不在這裡關閉連接，保持連接池打開以便重用

