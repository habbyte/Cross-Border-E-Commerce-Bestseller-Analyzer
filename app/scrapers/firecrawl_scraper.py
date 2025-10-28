"""
Firecrawl 爬蟲實現
"""

from typing import List, Dict, Any
from firecrawl import Firecrawl
from firecrawl.v2.types import ScrapeOptions
from .base_scraper import BaseScraper
from app.config import settings


class FirecrawlScraper(BaseScraper):
    """Firecrawl 爬蟲"""
    
    def __init__(self, output_dir: str = "data/scraped_content"):
        super().__init__(output_dir)
        self.app = Firecrawl(api_key=settings.firecrawl_api_key)
    
    def scrape_products(self, search_terms: List[str]) -> List[Dict[str, Any]]:
        """爬取商品信息"""
        all_products = []
        
        for search_term in search_terms:
            try:
                result = self.app.crawl(
                    url=f"https://www.amazon.com/s?k={search_term.replace(' ', '+')}",
                    limit=1,
                    max_discovery_depth=1,
                    scrape_options=ScrapeOptions(
                        formats=[
                            "markdown",
                            {
                                "type": "json",
                                "prompt": f"從 Amazon 搜索結果中萃取 '{search_term}' 相關的商品資訊，包含商品名稱、價格、評分、完整評論數（包含逗號，如 3,806）、圖片連結、商品介紹。確保評論數是完整的數字格式，不要截斷。",
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
                
                # 處理結果
                result_dict = result.model_dump(exclude_none=True, mode="json")
                items = result_dict.get("data", [])
                
                for item in items:
                    js = (item or {}).get("json") or {}
                    products = js.get("products", [])
                    
                    for product in products:
                        if product.get("name"):
                            # 提取特徵並創建描述
                            features = self.extract_product_features(product["name"])
                            if not product.get("description"):
                                product["description"] = self.create_description(product["name"], features)
                            
                            all_products.append(product)
                
                self.add_delay(2, 5)  # 添加延遲
                
            except Exception as e:
                print(f"爬取 {search_term} 時發生錯誤: {e}")
                continue
        
        return all_products
    
    def scrape_categories(self) -> List[Dict[str, Any]]:
        """爬取分類信息"""
        try:
            result = self.app.crawl(
                url="https://www.amazon.com/",
                limit=1,
                max_discovery_depth=1,
                scrape_options=ScrapeOptions(
                    formats=[
                        "markdown",
                        {
                            "type": "json",
                            "prompt": "從 Amazon 首頁萃取分類資訊，包含分類名稱和相關信息。",
                            "schema": {
                                "type": "object",
                                "properties": {
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
                                "required": ["categories"]
                            }
                        }
                    ],
                    wait_for=2000
                ),
                poll_interval=10
            )
            
            result_dict = result.model_dump(exclude_none=True, mode="json")
            items = result_dict.get("data", [])
            
            categories = []
            for item in items:
                js = (item or {}).get("json") or {}
                categories.extend(js.get("categories", []))
            
            return categories
            
        except Exception as e:
            print(f"爬取分類時發生錯誤: {e}")
            return []
