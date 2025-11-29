"""
Enhanced JSON 格式適配器
將 amazon_enhanced.json 格式轉換為數據庫格式
"""

import hashlib
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from app.schemas.product import ProductIn, CategoryIn, ProductWithCategories


def _clean_url(url: str) -> str:
    """清理 URL，移除無效部分"""
    if not url or not isinstance(url, str):
        return ""
    
    url = url.strip()
    
    # 如果包含 javascript:，只保留前面的部分
    if 'javascript:' in url.lower():
        # 找到 javascript: 的位置，只保留前面的部分
        idx = url.lower().find('javascript:')
        if idx > 0:
            url = url[:idx].rstrip()
    
    # 移除 void( 相關內容
    if 'void(' in url.lower():
        idx = url.lower().find('void(')
        if idx > 0:
            url = url[:idx].rstrip()
    
    return url


def _is_valid_url(url: str) -> bool:
    """驗證 URL 是否有效"""
    if not url or not isinstance(url, str):
        return False
    
    url = url.strip()
    if not url:
        return False
    
    # 排除明顯無效的 URL 模式
    url_lower = url.lower()
    if url_lower.startswith(('javascript:', 'void(', '#', 'mailto:')):
        return False
    
    # 檢查是否包含 javascript: 或其他無效協議（可能在 URL 中間）
    if 'javascript:' in url_lower or 'void(' in url_lower:
        return False
    
    try:
        result = urlparse(url)
        # 檢查是否有有效的 scheme 和 netloc
        if result.scheme not in ('http', 'https'):
            return False
        if not result.netloc:
            return False
        # netloc 不應該包含空格
        if ' ' in result.netloc:
            return False
        # 基本域名格式檢查（允許點號、連字符、數字和字母）
        netloc_clean = result.netloc.replace('.', '').replace('-', '')
        if not netloc_clean or not netloc_clean.replace(':', '').isalnum():
            return False
        return True
    except Exception:
        return False


def _parse_int_safe(text: str | None) -> int | None:
    """安全地解析整數，處理逗號和空格"""
    if not text:
        return None
    try:
        # 移除逗號和空格
        cleaned = str(text).replace(",", "").replace(" ", "").strip()
        return int(cleaned)
    except (ValueError, AttributeError):
        return None


def _parse_price(price_str: str | None) -> Optional[str]:
    """解析價格字符串，保留原始格式"""
    if not price_str:
        return None
    # 移除末尾的點號（如 "$599." -> "$599"）
    cleaned = str(price_str).rstrip(".")
    return cleaned if cleaned else None


def _extract_price_number(price_str: str | None) -> Optional[float]:
    """從價格字符串中提取數字"""
    if not price_str:
        return None
    # 移除 $ 符號和逗號
    cleaned = re.sub(r'[$,]', '', str(price_str))
    try:
        return float(cleaned)
    except (ValueError, AttributeError):
        return None


def _compute_hash(values: List[str | None]) -> str:
    """計算內容哈希值用於去重"""
    hasher = hashlib.sha256()
    for v in values:
        hasher.update((str(v) if v is not None else "").encode("utf-8"))
        hasher.update(b"\x1f")
    return hasher.hexdigest()


def _extract_category_from_path(category_path: str | None) -> List[str]:
    """從 category_path 中提取分類層級"""
    if not category_path:
        return []
    
    # 分割路徑，移除空字符串和箭頭符號
    parts = [p.strip() for p in category_path.split(">") if p.strip() and p.strip() != "›"]
    return parts


def extract_products_from_enhanced_json(data: Dict[str, Any], source_url: Optional[str] = None, platform: Optional[str] = None) -> List[ProductWithCategories]:
    """
    從 enhanced JSON 格式中提取產品數據
    
    Args:
        data: enhanced JSON 數據（包含 products 和 categories）
        source_url: 來源 URL（可選）
        platform: 平台名稱（如 "amazon", "walmart" 等）
    
    Returns:
        List[ProductWithCategories]: 產品及其分類列表
    """
    products_data = data.get("products", [])
    if not products_data:
        return []
    
    # 提取平台信息
    detected_platform = platform or data.get("site", "amazon")
    
    # 提取分類（如果有）
    categories_data = data.get("categories", [])
    category_list = []
    for cat in categories_data:
        cat_name = cat.get("category_name") or cat.get("name")
        if cat_name:
            # 驗證並清理 URL
            cat_url = cat.get("url")
            if cat_url:
                # 清理 URL：移除 javascript: 等無效部分
                cat_url = _clean_url(cat_url)
                if not _is_valid_url(cat_url):
                    cat_url = None
            else:
                cat_url = None
            category_list.append(CategoryIn(
                name=cat_name,
                source_url=cat_url
            ))
    
    result: List[ProductWithCategories] = []
    
    for product_data in products_data:
        name = product_data.get("name")
        if not name:
            continue
        
        # 解析價格
        price_str = _parse_price(product_data.get("price"))
        price_number = _extract_price_number(price_str)
        
        # 解析評分
        rating = product_data.get("rating")
        if isinstance(rating, str):
            try:
                rating = float(rating)
            except ValueError:
                rating = None
        
        # 解析評論數
        review_count_text = product_data.get("review_count")
        review_count = _parse_int_safe(review_count_text)
        
        # 計算內容哈希
        core_values = [
            name,
            price_str,
            str(rating or ""),
            review_count_text,
            product_data.get("image_url"),
            product_data.get("product_url"),
            product_data.get("description"),
            source_url,
        ]
        content_hash = _compute_hash(core_values)
        
        # 提取分類路徑中的分類
        category_path = product_data.get("category_path")
        path_categories = _extract_category_from_path(category_path)
        
        # 合併分類
        all_categories = category_list.copy()
        for cat_name in path_categories:
            # 避免重複
            if not any(c.name == cat_name for c in all_categories):
                # 驗證 source_url 是否有效
                validated_url = source_url if source_url and _is_valid_url(source_url) else None
                all_categories.append(CategoryIn(name=cat_name, source_url=validated_url))
        
        # 構建產品對象
        product = ProductIn(
            name=name,
            price=price_str,
            rating=rating,
            review_count_text=review_count_text,
            review_count=review_count,
            image_url=product_data.get("image_url"),
            product_url=product_data.get("product_url"),
            description=product_data.get("description"),
            source_url=source_url,
            content_hash=content_hash,
            # Enhanced fields
            category_path=category_path,
            bought_in_past_month=product_data.get("bought_in_past_month"),
            product_details=product_data.get("product_details"),
            about_this_item=product_data.get("about_this_item"),
            color_options=product_data.get("color_options"),
            size_options=product_data.get("size_options"),
            platform=detected_platform,
        )
        
        result.append(ProductWithCategories(
            product=product,
            categories=all_categories
        ))
    
    return result

