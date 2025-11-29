#!/usr/bin/env python3
"""
Amazon BeautifulSoup 爬蟲測試版本
這個版本用於測試爬蟲功能，不會寫入數據庫
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import random
from pathlib import Path
from typing import List, Dict, Any, Optional
import re


class AmazonScraperTest:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
    def get_page(self, url: str) -> Optional[BeautifulSoup]:
        """獲取頁面內容並解析為 BeautifulSoup 對象"""
        try:
            print(f"正在獲取頁面: {url}")
            # 添加隨機延遲避免被封鎖
            time.sleep(random.uniform(2, 4))
            
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            print(f"成功獲取頁面，內容長度: {len(response.content)} 字節")
            return soup
        except Exception as e:
            print(f"獲取頁面失敗 {url}: {e}")
            return None
    
    def extract_product_info(self, product_element) -> Dict[str, Any]:
        """從商品元素中提取商品信息"""
        product_info = {}
        
        try:
            # 商品名稱
            name_selectors = [
                'h2 a span',
                'h2 span', 
                'h3 a span',
                'h3 span',
                'a[href*="/dp/"] span',
                'a[href*="/gp/product/"] span',
                '.a-size-base-plus',
                '.a-size-medium'
            ]
            
            for selector in name_selectors:
                name_element = product_element.select_one(selector)
                if name_element and name_element.get_text(strip=True):
                    product_info['name'] = name_element.get_text(strip=True)
                    break
            
            # 價格
            price_selectors = [
                '.a-price-whole',
                '.a-price .a-offscreen',
                '.a-price-range',
                '.a-price-symbol + span',
                '.s-price',
                '.a-color-price'
            ]
            
            for selector in price_selectors:
                price_element = product_element.select_one(selector)
                if price_element:
                    price_text = price_element.get_text(strip=True)
                    if '$' in price_text or '€' in price_text or '£' in price_text:
                        product_info['price'] = price_text
                        break
            
            # 如果沒找到價格，嘗試正則表達式
            if 'price' not in product_info:
                price_text = product_element.get_text()
                price_match = re.search(r'[\$€£¥]\s*[\d,]+\.?\d*', price_text)
                if price_match:
                    product_info['price'] = price_match.group()
            
            # 評分
            rating_selectors = [
                '.a-icon-alt',
                '[aria-label*="stars"]',
                '.a-icon-star-small .a-icon-alt',
                '.a-icon-star .a-icon-alt'
            ]
            
            for selector in rating_selectors:
                rating_element = product_element.select_one(selector)
                if rating_element:
                    rating_text = rating_element.get_text(strip=True)
                    rating_match = re.search(r'(\d+\.\d+)', rating_text)
                    if rating_match:
                        try:
                            product_info['rating'] = float(rating_match.group(1))
                            break
                        except:
                            continue
            
            # 評論數
            review_selectors = [
                '.a-size-base',
                '.a-link-normal .a-size-base',
                '[aria-label*="ratings"]',
                'a[href*="#customerReviews"]'
            ]
            
            for selector in review_selectors:
                review_element = product_element.select_one(selector)
                if review_element:
                    review_text = review_element.get_text(strip=True)
                    if re.search(r'\(\d+\)|,\d+|\d+,\d+', review_text):
                        product_info['review_count'] = review_text
                        break
            
            # 圖片URL
            img_element = product_element.find('img')
            if img_element:
                img_src = img_element.get('data-src') or img_element.get('src')
                if img_src and 'amazon' in img_src:
                    product_info['image_url'] = img_src
            
            # 商品URL
            link_element = product_element.find('a', href=True)
            if link_element:
                href = link_element['href']
                if '/dp/' in href or '/gp/product/' in href:
                    if href.startswith('/'):
                        product_info['product_url'] = f"https://www.amazon.com{href}"
                    else:
                        product_info['product_url'] = href
            
            # 描述
            desc_element = product_element.find(['span', 'div'], class_=re.compile(r'.*description.*|.*summary.*', re.I))
            if desc_element:
                desc_text = desc_element.get_text(strip=True)
                if len(desc_text) > 10:
                    product_info['description'] = desc_text
                
        except Exception as e:
            print(f"提取商品信息時發生錯誤: {e}")
        
        return product_info
    
    def test_amazon_search(self, search_term: str = "laptop") -> Dict[str, Any]:
        """測試 Amazon 搜索功能"""
        search_url = f"https://www.amazon.com/s?k={search_term.replace(' ', '+')}"
        soup = self.get_page(search_url)
        
        if not soup:
            return {"products": [], "categories": []}
        
        products = []
        
        # 尋找搜索結果
        product_containers = soup.select('[data-component-type="s-search-result"]')
        
        if not product_containers:
            product_containers = soup.find_all('div', class_=re.compile(r'.*s-result-item.*', re.I))
        
        print(f"找到 {len(product_containers)} 個商品容器")
        
        for i, container in enumerate(product_containers[:10]):  # 只處理前10個
            print(f"\n--- 處理商品 {i+1} ---")
            product_info = self.extract_product_info(container)
            
            if product_info.get('name'):
                products.append(product_info)
                print(f"商品名稱: {product_info.get('name', 'N/A')}")
                print(f"價格: {product_info.get('price', 'N/A')}")
                print(f"評分: {product_info.get('rating', 'N/A')}")
                print(f"評論數: {product_info.get('review_count', 'N/A')}")
                print(f"圖片: {product_info.get('image_url', 'N/A')[:50]}...")
                print(f"鏈接: {product_info.get('product_url', 'N/A')[:50]}...")
            else:
                print("未找到商品名稱，跳過此項目")
        
        return {"products": products, "categories": []}
    
    def test_amazon_homepage(self) -> Dict[str, Any]:
        """測試 Amazon 首頁爬取"""
        url = "https://www.amazon.com/"
        soup = self.get_page(url)
        
        if not soup:
            return {"products": [], "categories": []}
        
        products = []
        
        # 尋找首頁商品
        product_containers = soup.select('[data-component-type="s-search-result"]')
        
        if not product_containers:
            product_containers = soup.find_all('div', class_=re.compile(r'.*s-result-item.*', re.I))
        
        print(f"首頁找到 {len(product_containers)} 個商品容器")
        
        for i, container in enumerate(product_containers[:5]):  # 只處理前5個
            print(f"\n--- 處理首頁商品 {i+1} ---")
            product_info = self.extract_product_info(container)
            
            if product_info.get('name'):
                products.append(product_info)
                print(f"商品名稱: {product_info.get('name', 'N/A')}")
                print(f"價格: {product_info.get('price', 'N/A')}")
            else:
                print("未找到商品名稱，跳過此項目")
        
        return {"products": products, "categories": []}


def main():
    """主測試函數"""
    print("=== Amazon BeautifulSoup 爬蟲測試 ===\n")
    
    scraper = AmazonScraperTest()
    
    # 測試搜索功能
    print("1. 測試搜索功能...")
    search_data = scraper.test_amazon_search("laptop")
    print(f"搜索結果: 找到 {len(search_data['products'])} 個商品\n")
    
    # 測試首頁功能
    print("2. 測試首頁功能...")
    homepage_data = scraper.test_amazon_homepage()
    print(f"首頁結果: 找到 {len(homepage_data['products'])} 個商品\n")
    
    # 合併結果
    all_products = search_data['products'] + homepage_data['products']
    
    # 保存測試結果
    output_dir = Path("scraped_content")
    output_dir.mkdir(exist_ok=True)
    
    test_file = output_dir / "amazon_test_bs4.json"
    with open(test_file, "w", encoding="utf-8") as f:
        json.dump({
            "products": all_products,
            "categories": [],
            "test_info": {
                "total_products": len(all_products),
                "search_products": len(search_data['products']),
                "homepage_products": len(homepage_data['products'])
            }
        }, f, ensure_ascii=False, indent=2)
    
    print(f"測試結果已保存到: {test_file}")
    print(f"總共爬取到 {len(all_products)} 個商品")


if __name__ == "__main__":
    main()
