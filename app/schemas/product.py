from pydantic import BaseModel, HttpUrl
from typing import Optional, List


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


class CategoryIn(BaseModel):
    name: str
    source_url: Optional[HttpUrl] = None


class ProductWithCategories(BaseModel):
    product: ProductIn
    categories: List[CategoryIn]


