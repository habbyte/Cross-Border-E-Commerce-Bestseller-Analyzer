#!/usr/bin/env python3
"""
測試增強版爬蟲
用於驗證修復是否有效
"""

import sys
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.scrapers import EnhancedAmazonScraper, EnhancedEbayScraper, EnhancedWalmartScraper


def test_amazon():
    """測試 Amazon 增強爬蟲"""
    print("=" * 50)
    print("測試 Amazon 增強爬蟲")
    print("=" * 50)
    
    try:
        scraper = EnhancedAmazonScraper(
            output_dir="data/scraped_content",
            headless=True,
            enable_request_monitoring=True
        )
        
        # 測試獲取首頁
        print("\n1. 測試獲取 Amazon 首頁...")
        soup = scraper.get_page("https://www.amazon.com/", timeout=60000)
        if soup:
            print(f"✅ 成功獲取首頁，內容長度: {len(str(soup))} 字節")
        else:
            print("❌ 獲取首頁失敗")
        
        # 測試搜索
        print("\n2. 測試搜索商品...")
        products = scraper.scrape_products(["laptop"], fetch_details=False)
        print(f"✅ 找到 {len(products)} 個商品")
        
        scraper.close()
        print("\n✅ Amazon 測試完成")
        
    except Exception as e:
        print(f"❌ Amazon 測試失敗: {e}")
        import traceback
        traceback.print_exc()


def test_ebay():
    """測試 eBay 增強爬蟲"""
    print("\n" + "=" * 50)
    print("測試 eBay 增強爬蟲")
    print("=" * 50)
    
    try:
        scraper = EnhancedEbayScraper(
            output_dir="data/scraped_content",
            headless=True
        )
        
        # 測試獲取首頁
        print("\n1. 測試獲取 eBay 首頁...")
        soup = scraper.get_page("https://www.ebay.com/", timeout=60000)
        if soup:
            print(f"✅ 成功獲取首頁，內容長度: {len(str(soup))} 字節")
        else:
            print("❌ 獲取首頁失敗")
        
        # 測試搜索
        print("\n2. 測試搜索商品...")
        products = scraper.scrape_products(["laptop"], fetch_details=False)
        print(f"✅ 找到 {len(products)} 個商品")
        
        scraper.close()
        print("\n✅ eBay 測試完成")
        
    except Exception as e:
        print(f"❌ eBay 測試失敗: {e}")
        import traceback
        traceback.print_exc()


def test_walmart():
    """測試 Walmart 增強爬蟲"""
    print("\n" + "=" * 50)
    print("測試 Walmart 增強爬蟲")
    print("=" * 50)
    
    try:
        scraper = EnhancedWalmartScraper(
            output_dir="data/scraped_content",
            headless=True
        )
        
        # 測試獲取首頁
        print("\n1. 測試獲取 Walmart 首頁...")
        soup = scraper.get_page("https://www.walmart.com/", timeout=60000)
        if soup:
            print(f"✅ 成功獲取首頁，內容長度: {len(str(soup))} 字節")
        else:
            print("❌ 獲取首頁失敗")
        
        # 測試搜索
        print("\n2. 測試搜索商品...")
        products = scraper.scrape_products(["laptop"], fetch_details=False)
        print(f"✅ 找到 {len(products)} 個商品")
        
        scraper.close()
        print("\n✅ Walmart 測試完成")
        
    except Exception as e:
        print(f"❌ Walmart 測試失敗: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函數"""
    print("開始測試增強版爬蟲...")
    print("請確保已安裝依賴: pip install -r requirements.txt")
    print("請確保已安裝 Playwright 瀏覽器: playwright install chromium\n")
    
    # 測試各個站點
    test_amazon()
    test_ebay()
    test_walmart()
    
    print("\n" + "=" * 50)
    print("所有測試完成！")
    print("=" * 50)


if __name__ == "__main__":
    main()

