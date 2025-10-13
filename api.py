from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import json, pathlib, os

# Import the reusable crawler from crawl_amazon.py
from crawl_amazon import crawl_category as crawl_category_core

class Product(BaseModel):
    name: str = Field(..., example="LEGO Star Wars Set")
    price: str = Field(..., example="$59.99")
    rating: Optional[float] = Field(None, example=4.6)
    review_count: Optional[str] = Field(None, example="3,806")
    image_url: Optional[str] = Field(None, example="https://images-na.ssl-images-amazon.com/...")
    product_url: Optional[str] = Field(None, example="https://www.amazon.com/dp/...")
    description: Optional[str] = Field(None, example="Great gift for kids...")

class CategoryInfo(BaseModel):
    category_name: Optional[str] = Field(None, example="Kitchen & Dining")
    product_count: Optional[int] = Field(None, example=120)

class CrawlResult(BaseModel):
    products: List[Product]
    categories: Optional[List[CategoryInfo]] = None
    metadata: Optional[Dict[str, Any]] = None

class BatchRequest(BaseModel):
    category_urls: List[str] = Field(..., example=[
        "https://www.amazon.com/Best-Sellers/zgbs",
        "https://www.amazon.com/b/?node=1055398"
    ])
    limit: int = Field(80, ge=1, le=500, example=80)

app = FastAPI(
    title="Amazon Category Crawler API",
    version="1.0.0",
    description="API for crawling Amazon category pages and returning normalized product data.",
    openapi_tags=[
        {"name": "crawler", "description": "Amazon category crawling endpoints"},
        {"name": "cache", "description": "Read local cached results"},
        {"name": "health", "description": "Service health"},
    ]
)

@app.get("/health", tags=["health"])
def health():
    return {"ok": True}

@app.post("/crawl/category", response_model=CrawlResult, tags=["crawler"], summary="Crawl a single category")
def crawl_category(
    category_url: str = Query(..., description="Amazon category URL"),
    limit: int = Query(100, ge=1, le=500),
    max_discovery_depth: int = Query(1, ge=0, le=3)
):
    try:
        data = crawl_category_core(category_url, limit=limit, max_discovery_depth=max_discovery_depth)
        # Ensure defaults
        data.setdefault("products", [])
        data.setdefault("categories", [])
        data.setdefault("metadata", None)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/crawl/batch", tags=["crawler"], summary="Batch crawl multiple categories")
def crawl_batch(req: BatchRequest):
    out: Dict[str, Any] = {}
    for url in req.category_urls:
        try:
            out[url] = crawl_category_core(url, limit=req.limit, max_discovery_depth=1)
        except Exception as e:
            out[url] = {"error": str(e)}
    return out

@app.get("/cache/products", response_model=CrawlResult, tags=["cache"], summary="Read cached products")
def get_cached_products(category_keyword: Optional[str] = Query(None)):
    path = pathlib.Path("scraped_content/amazon_content.json")
    if not path.exists():
        raise HTTPException(status_code=404, detail="No cache file found")
    data = json.loads(path.read_text(encoding="utf-8"))

    # Normalize to CrawlResult shape
    result = {"products": [], "categories": [], "metadata": None}

    def _ingest(doc: Dict[str, Any]):
        j = doc.get("json")
        if isinstance(j, dict):
            if isinstance(j.get("products"), list):
                result["products"].extend(j["products"])
            if isinstance(j.get("categories"), list):
                result["categories"].extend(j["categories"])
        if result["metadata"] is None and "metadata" in doc:
            result["metadata"] = doc["metadata"]

    if isinstance(data, dict) and "data" in data:
        for d in data["data"]:
            _ingest(d)
    elif isinstance(data, list):
        for d in data:
            _ingest(d)
    elif isinstance(data, dict):
        _ingest(data)

    if category_keyword and result["categories"]:
        kw = category_keyword.lower()
        result["categories"] = [c for c in result["categories"] if (c.get("category_name") or "").lower().find(kw) >= 0]

    return result