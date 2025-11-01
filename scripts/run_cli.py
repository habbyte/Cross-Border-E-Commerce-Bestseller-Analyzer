#!/usr/bin/env python3
"""
命令行工具
提供統一的爬蟲執行接口
"""

import sys
import argparse
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.scrapers import (
    FirecrawlScraper,
    BeautifulSoupScraper,
    EbayScraper,
    WalmartScraper,
)


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description='Amazon 爬蟲工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
            使用範例:
            python scripts/run_cli.py --scraper beautifulsoup --search "laptop" "phone"
            python scripts/run_cli.py --scraper firecrawl --search "shoes" --no-db
            python scripts/run_cli.py --help
        """
    )
    parser.add_argument('--scraper', choices=['firecrawl', 'beautifulsoup'], default='beautifulsoup',
                       help='選擇爬蟲類型 (預設: beautifulsoup)')
    parser.add_argument('--site', choices=['amazon', 'ebay', 'walmart', 'all'], default='amazon',
                       help='選擇站點: amazon/ebay/walmart 或 all (預設: amazon)')
    parser.add_argument('--search', nargs='+', default=['men\'s t-shirt', 'women\'s dress'],
                       help='搜索關鍵詞列表 (預設: men\'s t-shirt women\'s dress)')
    parser.add_argument('--output', type=str, default='data/scraped_content',
                       help='輸出目錄 (預設: data/scraped_content)')
    parser.add_argument('--no-db', action='store_true',
                       help='不寫入數據庫，只保存到文件')
    
    args = parser.parse_args()
    
    print(f"=== 多站點爬蟲工具 ===")
    print(f"站點: {args.site}")
    print(f"爬蟲類型: {args.scraper}")
    print(f"搜索關鍵詞: {args.search}")
    print(f"輸出目錄: {args.output}")
    print(f"寫入數據庫: {'否' if args.no_db else '是'}")
    print("-" * 50)
    
    # 建立站點對應的 scraper 工廠
    def build_scraper(site: str):
        if site == 'amazon':
            if args.scraper == 'firecrawl':
                return FirecrawlScraper(args.output)
            return BeautifulSoupScraper(args.output)
        elif site == 'ebay':
            if args.scraper == 'firecrawl':
                print('注意: eBay 暫不支援 firecrawl，改用 beautifulsoup')
            return EbayScraper(args.output)
        elif site == 'walmart':
            if args.scraper == 'firecrawl':
                print('注意: Walmart 暫不支援 firecrawl，改用 beautifulsoup')
            return WalmartScraper(args.output)
        else:
            return BeautifulSoupScraper(args.output)
    
    sites = ['amazon', 'ebay', 'walmart'] if args.site == 'all' else [args.site]
    all_data = {}
    total_products = 0
    for site in sites:
        print(f"\n--- 站點: {site} ---")
        scraper = build_scraper(site)
        print("開始爬取商品...")
        products = scraper.scrape_products(args.search)
        print(f"爬取到 {len(products)} 個商品")
        total_products += len(products)

        print("開始爬取分類...")
        categories = scraper.scrape_categories()
        print(f"爬取到 {len(categories)} 個分類")

        all_data[site] = {
            'products': products,
            'categories': categories,
        }
    
    # 保存結果
    if args.site == 'all':
        result_data = {
            'sites': all_data,
            'scraper_type': args.scraper,
            'search_terms': args.search,
        }
        # 使用 Amazon BeautifulSoupScraper 的 save_results 來統一輸出
        saver = BeautifulSoupScraper(args.output)
        filename = f"multi_site_{args.scraper}.json"
        filepath = saver.save_results(result_data, filename)
        print(f"結果已保存到: {filepath}")
    else:
        result_data = {
            'products': all_data[sites[0]]['products'],
            'categories': all_data[sites[0]]['categories'],
            'scraper_type': args.scraper,
            'search_terms': args.search,
            'site': sites[0],
        }
        saver = BeautifulSoupScraper(args.output)
        filename = f"{sites[0]}_{args.scraper}.json"
        filepath = saver.save_results(result_data, filename)
        print(f"結果已保存到: {filepath}")
    
    # 統計信息
    if total_products:
        products_with_url = sum(1 for p in products if p.get('product_url'))
        products_with_desc = sum(1 for p in products if p.get('description'))
        products_with_price = sum(1 for p in products if p.get('price'))
        products_with_rating = sum(1 for p in products if p.get('rating'))
        
        print(f"\n商品信息完整性統計:")
        # 僅在單站點時輸出統計（多站點統計以匯總為主）
        if args.site != 'all':
            print(f"- 有價格的商品: {products_with_price}/{len(products)} ({products_with_price/len(products)*100:.1f}%)")
            print(f"- 有評分的商品: {products_with_rating}/{len(products)} ({products_with_rating/len(products)*100:.1f}%)")
            print(f"- 有鏈接的商品: {products_with_url}/{len(products)} ({products_with_url/len(products)*100:.1f}%)")
            print(f"- 有描述的商品: {products_with_desc}/{len(products)} ({products_with_desc/len(products)*100:.1f}%)")
    
    # 寫入數據庫（如果沒有禁用）
    if not args.no_db and args.site == 'amazon' and all_data.get('amazon', {}).get('products'):
        print("\n開始寫入數據庫...")
        try:
            from app.pipelines.amazon_adapter import extract_products_with_categories
            from app.services.product_writer import bulk_upsert_products_with_categories
            from app.services.mongodb_writer import bulk_upsert_products_mongodb
            from app.db.models import Base
            from app.db.session import engine
            
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
            affected = bulk_upsert_products_with_categories(data, actor_user_id=None, run_id=f"run-{args.scraper}")
            print(f"Upsert {affected} products to PostgreSQL")
            
            # 寫入 MongoDB
            mongo_affected = bulk_upsert_products_mongodb(data, run_id=f"run-{args.scraper}")
            print(f"Upsert {mongo_affected} products to MongoDB")
            
        except Exception as e:
            print(f"寫入數據庫時發生錯誤: {e}")
    
    print("\n=== 爬取完成 ===")


if __name__ == "__main__":
    main()
