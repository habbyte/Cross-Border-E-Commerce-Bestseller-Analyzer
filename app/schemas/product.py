from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any


class ProductIn(BaseModel):
    name: str
    price: Optional[str] = None
    rating: Optional[float] = None
    review_count_text: Optional[str] = None
    review_count: Optional[int] = None
    image_url: Optional[HttpUrl] = None
    product_url: Optional[HttpUrl] = None
    description: Optional[str] = None
    source_url: Optional[HttpUrl] = None
    content_hash: Optional[str] = None
    # Enhanced fields
    category_path: Optional[str] = None
    bought_in_past_month: Optional[str] = None
    product_details: Optional[Dict[str, Any]] = None
    about_this_item: Optional[List[str]] = None
    color_options: Optional[List[Dict[str, Any]]] = None
    size_options: Optional[List[str]] = None
    platform: Optional[str] = None


class CategoryIn(BaseModel):
    name: str
    source_url: Optional[str] = None  # 使用 str 而不是 HttpUrl，允許更寬鬆的 URL 格式


class ProductWithCategories(BaseModel):
    product: ProductIn
    categories: List[CategoryIn]


