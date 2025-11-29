#!/usr/bin/env python3
"""
命令行工具
提供統一的爬蟲執行接口
"""

import sys
import argparse
import json
from pathlib import Path
from typing import Optional

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.scrapers import (
    FirecrawlScraper,
    BeautifulSoupScraper,
    EbayScraper,
    WalmartScraper,
    EnhancedAmazonScraper,
    EnhancedEbayScraper,
    EnhancedWalmartScraper,
    EnhancedShopeeScraper,
)
from app.config import settings


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
    parser.add_argument('--scraper', choices=['firecrawl', 'beautifulsoup', 'enhanced'], default='beautifulsoup',
                       help='選擇爬蟲類型: firecrawl/beautifulsoup/enhanced (預設: beautifulsoup)')
    parser.add_argument('--site', choices=['amazon', 'ebay', 'walmart', 'shopee', 'all'], default='amazon',
                       help='選擇站點: amazon/ebay/walmart/shopee 或 all (預設: amazon)')
    parser.add_argument('--search', nargs='+', default=['men\'s t-shirt', 'women\'s dress'],
                       help='搜索關鍵詞列表 (預設: men\'s t-shirt women\'s dress)')
    parser.add_argument('--output', type=str, default='data/scraped_content',
                       help='輸出目錄 (預設: data/scraped_content)')
    parser.add_argument('--no-db', action='store_true',
                       help='不寫入數據庫，只保存到文件')
    parser.add_argument('--proxy', type=str, default=None,
                       help='Proxy 地址，格式: http://user:pass@host:port 或 socks5://host:port')
    parser.add_argument('--cookies-file', type=str, default=None,
                       help='Cookies 文件路徑 (JSON 格式)')
    parser.add_argument('--headless', action='store_true', default=None,
                       help='使用無頭模式（僅 enhanced 爬蟲）')
    parser.add_argument('--no-headless', action='store_false', dest='headless',
                       help='顯示瀏覽器窗口（僅 enhanced 爬蟲）')
    parser.add_argument('--pause-on-verify', action='store_true',
                       help='遇到 Shopee 安全驗證時暫停並等待手動處理')
    parser.add_argument('--shopee-base-url', type=str, default=None,
                       help='Shopee 站點根網址，例如 https://shopee.tw（預設: settings 或自動偵測）')
    
    args = parser.parse_args()
    
    print(f"=== 多站點爬蟲工具 ===")
    print(f"站點: {args.site}")
    print(f"爬蟲類型: {args.scraper}")
    print(f"搜索關鍵詞: {args.search}")
    print(f"輸出目錄: {args.output}")
    print(f"寫入數據庫: {'否' if args.no_db else '是'}")
    print("-" * 50)
    
    # 建立站點對應的 scraper 工廠
    def detect_shopee_base_url(cookies_file: Optional[str]) -> Optional[str]:
        """根據 cookies 檔案推測 Shopee 站點"""
        if not cookies_file:
            return None
        try:
            with open(cookies_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            if not isinstance(cookies, list):
                return None
            for cookie in cookies:
                domain = (cookie or {}).get('domain', '')
                if not isinstance(domain, str):
                    continue
                domain = domain.lower()
                if 'shopee.tw' in domain:
                    return 'https://shopee.tw'
                if 'shopee.sg' in domain:
                    return 'https://shopee.sg'
                if 'shopee.co.id' in domain:
                    return 'https://shopee.co.id'
                if 'shopee.co.th' in domain:
                    return 'https://shopee.co.th'
                if 'shopee.vn' in domain:
                    return 'https://shopee.vn'
        except Exception:
            return None
        return None

    def resolve_default_shopee_cookies() -> Optional[str]:
        """若存在 data/shopee_cookies.json 則優先使用"""
        default_file = Path('data/shopee_cookies.json')
        if default_file.exists():
            return str(default_file)
        return None

    def build_scraper(site: str):
        # 構建增強爬蟲的參數
        enhanced_kwargs = {}
        if args.proxy:
            enhanced_kwargs['proxy'] = args.proxy
        elif settings.proxy:
            enhanced_kwargs['proxy'] = settings.proxy
        
        base_cookies_file = args.cookies_file or settings.cookies_file
        if base_cookies_file:
            enhanced_kwargs['cookies_file'] = base_cookies_file
        
        if args.headless is not None:
            enhanced_kwargs['headless'] = args.headless
        else:
            enhanced_kwargs['headless'] = settings.headless
        
        enhanced_kwargs['enable_request_monitoring'] = settings.enable_request_monitoring
        
        if site == 'amazon':
            if args.scraper == 'firecrawl':
                return FirecrawlScraper(args.output)
            elif args.scraper == 'enhanced':
                return EnhancedAmazonScraper(args.output, **enhanced_kwargs)
            return BeautifulSoupScraper(args.output)
        elif site == 'ebay':
            if args.scraper == 'firecrawl':
                print('注意: eBay 暫不支援 firecrawl，改用 beautifulsoup')
                return EbayScraper(args.output)
            elif args.scraper == 'enhanced':
                return EnhancedEbayScraper(args.output, **enhanced_kwargs)
            return EbayScraper(args.output)
        elif site == 'walmart':
            if args.scraper == 'firecrawl':
                print('注意: Walmart 暫不支援 firecrawl，改用 beautifulsoup')
                return WalmartScraper(args.output)
            elif args.scraper == 'enhanced':
                return EnhancedWalmartScraper(args.output, **enhanced_kwargs)
            return WalmartScraper(args.output)
        elif site == 'shopee':
            if args.scraper != 'enhanced':
                print('注意: Shopee 目前僅支援 enhanced 模式，將自動切換')
            # 優先使用專屬 cookies
            shopee_cookies = args.cookies_file or resolve_default_shopee_cookies() or enhanced_kwargs.get('cookies_file')
            if shopee_cookies:
                enhanced_kwargs['cookies_file'] = shopee_cookies
                print(f"Shopee 將使用 cookies 檔案: {shopee_cookies}")
            base_url = args.shopee_base_url or settings.shopee_base_url
            detected_url = detect_shopee_base_url(shopee_cookies)
            if detected_url and base_url != detected_url:
                print(f"根據 cookies 自動偵測到 Shopee 站點: {detected_url}")
                base_url = detected_url
            
            # 傳遞登入憑證（如果配置了）
            shopee_email = settings.shopee_email if hasattr(settings, 'shopee_email') and settings.shopee_email else None
            shopee_password = settings.shopee_password if hasattr(settings, 'shopee_password') and settings.shopee_password else None
            if shopee_email and shopee_password:
                print("檢測到 Shopee 登入憑證，將嘗試自動登入")
            if args.pause_on_verify:
                print("啟用驗證暫停模式：遇到安全驗證會等待人工操作")
            
            return EnhancedShopeeScraper(
                args.output, 
                region_base_url=base_url,
                shopee_email=shopee_email,
                shopee_password=shopee_password,
                pause_on_verification=args.pause_on_verify,
                **enhanced_kwargs
            )
        else:
            return BeautifulSoupScraper(args.output)
    
    sites = ['amazon', 'ebay', 'walmart', 'shopee'] if args.site == 'all' else [args.site]
    all_data = {}
    total_products = 0
    
    for site in sites:
        scraper = None
        try:
            print(f"\n--- 站點: {site} ---")
            scraper = build_scraper(site)
            if scraper is None:
                print(f"錯誤: 無法為 {site} 創建爬蟲實例，跳過此站點")
                all_data[site] = {'products': [], 'categories': []}
                continue
            
            print(f"使用爬蟲: {type(scraper).__name__}")
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
        except Exception as e:
            print(f"錯誤: 爬取 {site} 時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            # 即使某個站點失敗，也繼續處理其他站點
            all_data[site] = {
                'products': [],
                'categories': [],
            }
        finally:
            # 立即關閉當前 scraper，釋放資源（特別是 enhanced scraper 的 asyncio loop）
            # 這樣可以避免多個 enhanced scraper 之間的衝突
            if scraper and hasattr(scraper, 'close'):
                try:
                    scraper.close()
                    print(f"已關閉 {site} 的爬蟲資源")
                except Exception as e:
                    print(f"關閉 {site} 爬蟲時發生錯誤: {e}")
    
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
        print(f"\n商品信息完整性統計:")
        # 僅在單站點時輸出統計（多站點統計以匯總為主）
        if args.site != 'all' and len(sites) > 0:
            # 使用第一個站點的數據進行統計
            site_products = all_data.get(sites[0], {}).get('products', [])
            if site_products:
                products_with_url = sum(1 for p in site_products if p.get('product_url'))
                products_with_desc = sum(1 for p in site_products if p.get('description'))
                products_with_price = sum(1 for p in site_products if p.get('price'))
                products_with_rating = sum(1 for p in site_products if p.get('rating'))
                total_count = len(site_products)
                print(f"- 有價格的商品: {products_with_price}/{total_count} ({products_with_price/total_count*100:.1f}%)")
                print(f"- 有評分的商品: {products_with_rating}/{total_count} ({products_with_rating/total_count*100:.1f}%)")
                print(f"- 有鏈接的商品: {products_with_url}/{total_count} ({products_with_url/total_count*100:.1f}%)")
                print(f"- 有描述的商品: {products_with_desc}/{total_count} ({products_with_desc/total_count*100:.1f}%)")
        elif args.site == 'all':
            # 多站點統計
            print(f"- 總商品數: {total_products}")
            for site_name in sites:
                site_products = all_data.get(site_name, {}).get('products', [])
                if site_products:
                    site_count = len(site_products)
                    print(f"  - {site_name}: {site_count} 個商品")
    
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
