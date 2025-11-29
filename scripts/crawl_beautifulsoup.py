#!/usr/bin/env python3
"""
BeautifulSoup 爬蟲主腳本
"""

import sys
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.scrapers import BeautifulSoupScraper
from app.pipelines.amazon_adapter import extract_products_with_categories
from app.services.product_writer import bulk_upsert_products_with_categories
from app.services.mongodb_writer import bulk_upsert_products_mongodb
from app.db.models import Base
from app.db.session import engine


def main():
    """主函數"""
    print("=== BeautifulSoup Amazon 爬蟲 ===")
    
    # 初始化爬蟲
    scraper = BeautifulSoupScraper()
    
    # 搜索詞列表
    search_terms = [
        "men's t-shirt",
        "women's dress", 
        "jeans",
        "sneakers",
        "jacket"
    ]
    
    # 爬取商品
    print("開始爬取商品...")
    products = scraper.scrape_products(search_terms)
    print(f"爬取到 {len(products)} 個商品")
    
    # 爬取分類
    print("開始爬取分類...")
    categories = scraper.scrape_categories()
    print(f"爬取到 {len(categories)} 個分類")
    
    # 保存結果
    result_data = {
        "products": products,
        "categories": categories
    }
    
    filepath = scraper.save_results(result_data, "beautifulsoup_products.json")
    print(f"結果已保存到: {filepath}")
    
    # 轉換為數據庫格式並寫入
    if products:
        print("開始寫入數據庫...")
        
        # 建表
        Base.metadata.create_all(bind=engine)
        
        # 創建兼容格式的數據
        class ResultWrapper:
            def __init__(self, data):
                self._data = data
            def model_dump(self, exclude_none=True, mode="json"):
                return {
                    "data": [{
                        "json": self._data,
                        "metadata": {"url": "https://www.amazon.com/"}
                    }]
                }
        
        result = ResultWrapper(result_data)
        
        # 寫入 PostgreSQL
        data = extract_products_with_categories(result)
        affected = bulk_upsert_products_with_categories(data, actor_user_id=None, run_id="run-beautifulsoup")
        print(f"Upsert {affected} products to PostgreSQL")
        
        # 寫入 MongoDB
        mongo_affected = bulk_upsert_products_mongodb(data, run_id="run-beautifulsoup")
        print(f"Upsert {mongo_affected} products to MongoDB")


if __name__ == "__main__":
    main()
