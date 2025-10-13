import os
from typing import Dict, Any, List, Optional
from firecrawl import Firecrawl
from firecrawl.v2.types import ScrapeOptions

# Prefer environment variable; fallback to placeholder (replace for production)
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "fc-fc67856032f3451bbf59bfb07d00f85e")
app = Firecrawl(api_key=FIRECRAWL_API_KEY)

# Keep a strict schema so frontend gets consistent fields
SCRAPE_FORMATS = [
    "markdown",
    {
        "type": "json",
        "prompt": "萃取商品名称、价格、评分、完整评论数（含逗号）、图片、商品链接、描述，以及类目信息。确保 review_count 为包含逗号的完整数字字符串（如 3,806）。",
        "schema": {
            "type": "object",
            "properties": {
                "products": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "price": {"type": "string"},
                            "rating": {"type": "number"},
                            "review_count": {"type": "string"},
                            "image_url": {"type": "string"},
                            "product_url": {"type": "string"},
                            "description": {"type": "string"}
                        },
                        "required": ["name", "price"]
                    }
                },
                "categories": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "category_name": {"type": "string"},
                            "product_count": {"type": "number"}
                        }
                    }
                }
            },
            "required": ["products"]
        }
    }
]

def crawl_category(category_url: str, limit: int = 100, max_discovery_depth: int = 1) -> Dict[str, Any]:
    """
    Crawl a single Amazon category/search page and return normalized structure.
    Returns:
      {
        "products": [...],
        "categories": [...],
        "metadata": {...} | None
      }
    """
    docs = app.crawl(
        url=category_url,
        limit=limit,
        max_discovery_depth=max_discovery_depth,
        scrape_options=ScrapeOptions(
            formats=SCRAPE_FORMATS,
            wait_for=2000
        ),
        poll_interval=10
    )

    result: Dict[str, Any] = {"products": [], "categories": [], "metadata": None}
    for doc in docs.data:
        d = doc.model_dump(exclude_none=True)
        j = d.get("json")
        if isinstance(j, dict):
            prods = j.get("products")
            cats = j.get("categories")
            if isinstance(prods, list):
                result["products"].extend(prods)
            if isinstance(cats, list):
                result["categories"].extend(cats)
        if result.get("metadata") is None and "metadata" in d:
            result["metadata"] = d["metadata"]
    return result

if __name__ == "__main__":
    # Quick manual test
    import json as _json
    test_url = os.getenv("TEST_CATEGORY_URL", "https://www.amazon.com/Best-Sellers/zgbs")
    payload = crawl_category(test_url, limit=5, max_discovery_depth=1)
    print(_json.dumps(payload, ensure_ascii=False, indent=2))