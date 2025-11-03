"""
產品 API 端點
提供產品數據給前端
"""

from fastapi import APIRouter, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, and_
from typing import Optional, List
from app.db.session import SessionLocal
from app.db.models import Product, Category, ProductCategory
from pydantic import BaseModel
from typing import Dict, Any

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
    import re
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


def _db_product_to_response(db_product: Product, db: Session) -> ProductResponse:
    """將數據庫產品轉換為前端響應格式"""
    try:
        price = _parse_price(db_product.price)
        margin_rate = _calculate_margin_rate(price)
        competition_score = _calculate_competition_score(db_product.review_count, db_product.rating)
        competition_level = _get_competition_level(competition_score)
        
        # 獲取分類
        category = "Electronics"  # 默認值
        if db_product.category_path:
            # 從 category_path 提取第一個分類
            try:
                parts = [p.strip() for p in db_product.category_path.split(">") if p.strip() and p.strip() != "›"]
                if parts:
                    category = parts[0]
            except Exception:
                pass  # 如果解析失敗，使用默認值
        
        # 格式化價格
        formatted_price = db_product.price or f"${price:.2f}"
        
        # 提取標籤（從 product_details 或其他字段）
        tags = []
        if db_product.product_details and isinstance(db_product.product_details, dict):
            # 可以從 product_details 中提取關鍵信息作為標籤
            brand = db_product.product_details.get("Brand")
            if brand:
                # 清理品牌名稱（移除特殊字符）
                brand_clean = str(brand).strip("‎").strip()
                if brand_clean:
                    tags.append(brand_clean)
        
        return ProductResponse(
            id=f"prod-{db_product.id}",
            title=db_product.name or "",
            platform=db_product.platform or "amazon",
            price=price,
            formattedPrice=formatted_price,
            marginRate=margin_rate,
            competitionScore=competition_score,
            competitionLevel=competition_level,
            category=category,
            imageUrl=db_product.image_url,
            description=db_product.description,
            rating=db_product.rating,
            reviewCount=db_product.review_count,
            productUrl=db_product.product_url,
            tags=tags,
            productDetails=db_product.product_details if isinstance(db_product.product_details, dict) else None,
            aboutThisItem=db_product.about_this_item if isinstance(db_product.about_this_item, list) else None,
            colorOptions=db_product.color_options if isinstance(db_product.color_options, list) else None,
            sizeOptions=db_product.size_options if isinstance(db_product.size_options, list) else None,
        )
    except Exception as e:
        # 如果轉換失敗，返回基本信息
        import traceback
        print(f"Error converting product {db_product.id}: {e}")
        traceback.print_exc()
        price = _parse_price(db_product.price)
        return ProductResponse(
            id=f"prod-{db_product.id}",
            title=db_product.name or "",
            platform=db_product.platform or "amazon",
            price=price,
            formattedPrice=db_product.price or f"${price:.2f}",
            marginRate=0.0,
            competitionScore=50.0,
            competitionLevel="medium",
            category="Electronics",
            imageUrl=db_product.image_url,
            description=db_product.description,
            rating=db_product.rating,
            reviewCount=db_product.review_count,
            productUrl=db_product.product_url,
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
    獲取產品列表
    
    Args:
        skip: 跳過的記錄數
        limit: 返回的記錄數
        platform: 平台過濾（amazon, walmart, ebay 等）
        category: 分類過濾
        search: 搜索關鍵詞
        status: 狀態過濾（active, draft, all）
    """
    db: Session = SessionLocal()
    try:
        query = select(Product)
        
        # 狀態過濾（默認只返回 active）
        if status == "all":
            # 如果 status 是 "all"，不過濾狀態
            pass
        else:
            # 默認使用 "active"
            filter_status = status if status in ("active", "draft") else "active"
            query = query.where(Product.status == filter_status)
        
        # 平台過濾
        if platform:
            query = query.where(Product.platform == platform)
        
        # 分類過濾
        if category:
            # 通過 category_path 過濾
            query = query.where(Product.category_path.contains(category))
        
        # 搜索過濾
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    Product.name.ilike(search_pattern),
                    Product.description.ilike(search_pattern),
                )
            )
        
        # 排序（按創建時間倒序）
        query = query.order_by(Product.created_at.desc())
        
        # 分頁
        query = query.offset(skip).limit(limit)
        
        products = db.execute(query).scalars().all()
        
        # 轉換為響應格式，處理可能的錯誤
        result = []
        for p in products:
            try:
                result.append(_db_product_to_response(p, db))
            except Exception as e:
                import traceback
                print(f"Error processing product {p.id}: {e}")
                traceback.print_exc()
                # 跳過有問題的產品，繼續處理其他產品
                continue
        
        return result
    except Exception as e:
        import traceback
        print(f"Error in get_products: {e}")
        traceback.print_exc()
        raise
    finally:
        db.close()


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: str):
    """
    獲取單個產品詳情
    
    Args:
        product_id: 產品 ID（格式: prod-{id} 或直接數字）
    """
    db: Session = SessionLocal()
    try:
        # 解析產品 ID
        if product_id.startswith("prod-"):
            product_id = product_id.replace("prod-", "")
        
        try:
            product_db_id = int(product_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid product ID")
        
        product = db.execute(
            select(Product).where(Product.id == product_db_id)
        ).scalar_one_or_none()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return _db_product_to_response(product, db)
    finally:
        db.close()


@router.get("/stats/summary")
def get_stats():
    """獲取產品統計信息"""
    db: Session = SessionLocal()
    try:
        total = db.execute(select(Product)).scalars().all()
        total_count = len(total)
        
        active_count = len([p for p in total if p.status == "active"])
        
        # 按平台統計
        platforms = {}
        for p in total:
            platform = p.platform or "unknown"
            platforms[platform] = platforms.get(platform, 0) + 1
        
        return {
            "totalProducts": total_count,
            "activeProducts": active_count,
            "platforms": platforms,
        }
    finally:
        db.close()

