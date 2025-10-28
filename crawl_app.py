from firecrawl import Firecrawl
from firecrawl.v2.types import ScrapeOptions
import json
import pprint
from pathlib import Path
from app.config import settings
from app.db.models import Base
from app.db.session import engine
from app.pipelines.amazon_adapter import extract_products_from_result, extract_products_with_categories
from app.services.product_writer import bulk_upsert_products, bulk_upsert_products_with_categories
from app.services.mongodb_writer import bulk_upsert_products_mongodb

app = Firecrawl(api_key=settings.firecrawl_api_key)

try:
    result = app.crawl(
        url="https://www.amazon.com/",
        limit=1,
        max_discovery_depth=1,
        scrape_options=ScrapeOptions(
            formats=[
                "markdown",
                {
                    "type": "json",
                    "prompt": "從 Amazon 首頁萃取商品資訊，包含商品名稱、價格、評分、完整評論數（包含逗號，如 3,806）、圖片連結、商品介紹。確保評論數是完整的數字格式，不要截斷。",
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
            ],
            wait_for=2000
        ),
        poll_interval=10
    )
except Exception:
    # 點數不足或其他錯誤時，回退使用本地 JSON
    class _ResultWrapper:
        def __init__(self, d):
            self._d = d
        def model_dump(self, exclude_none=True, mode="json"):
            return self._d

    fallback_path = Path("scraped_content") / "amazon_content.json"
    if not fallback_path.exists():
        raise
    with open(fallback_path, "r", encoding="utf-8") as rf:
        result = _ResultWrapper(json.load(rf))
output_dir = Path("scraped_content")
output_dir.mkdir(exist_ok=True)

filepath = output_dir / "amazon_content.json"
with open(filepath, "w", encoding="utf-8") as f:
    json.dump(result.model_dump(exclude_none=True, mode='json'), f, ensure_ascii=False, indent=2)

# 建表（若不存在）
Base.metadata.create_all(bind=engine)

# 轉換 Firecrawl 結果並寫入 Postgres（含分類）
data = extract_products_with_categories(result)
affected = bulk_upsert_products_with_categories(data, actor_user_id=None, run_id="run-1")
print(f"Upsert {affected} products (with categories) to PostgreSQL")

# 同時寫入 MongoDB Atlas
mongo_affected = bulk_upsert_products_mongodb(data, run_id="run-1")
print(f"Upsert {mongo_affected} products to MongoDB Atlas")