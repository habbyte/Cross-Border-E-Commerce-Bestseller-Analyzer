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

app = Firecrawl(api_key=settings.firecrawl_api_key)

result = app.crawl(
    url="https://www.amazon.com/",
    limit=3,
    max_discovery_depth=1,
    scrape_options=ScrapeOptions(
        formats=[
            "markdown",  # 保留原始 Markdown
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
                                    "review_count": {
                                        "type": "string",
                                        "description": "完整的評論數，包含逗號分隔符（如 3,806）"
                                    },
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
    poll_interval=10 # 每 10 秒檢查一次狀態
)
output_dir = Path("scraped_content")
output_dir.mkdir(exist_ok=True)

filepath = output_dir / "amazon_content.json"
with open(filepath, "w", encoding="utf-8") as f:
    json.dump(result.model_dump(exclude_none=True, mode='json'), f, ensure_ascii=False, indent=2)

# 建表（若不存在）
Base.metadata.create_all(bind=engine)

# 轉換 Firecrawl 結果並寫入 Postgres（含分類）
data = extract_products_with_categories(result)
affected = bulk_upsert_products_with_categories(data)
print(f"Upsert {affected} products (with categories) to PostgreSQL")