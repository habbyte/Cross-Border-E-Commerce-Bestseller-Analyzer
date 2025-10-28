#!/usr/bin/env python3
"""
Amazon 衣服 BeautifulSoup 爬蟲測試版本
專門測試衣服商品的爬取功能
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import random
from pathlib import Path
from typing import List, Dict, Any, Optional
import re


class AmazonClothingScraperTest:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
    def get_page(self, url: str) -> Optional[BeautifulSoup]:
        """獲取頁面內容並解析為 BeautifulSoup 對象"""
        try:
            print(f"正在獲取頁面: {url}")
            time.sleep(random.uniform(3, 6))
            
            # 添加更多請求頭來模擬真實瀏覽器
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0'
            }
            
            response = self.session.get(url, headers=headers, timeout=20)
            
            if response.status_code == 503:
                print(f"收到 503 錯誤，可能是被 Amazon 封鎖，嘗試使用備用方法...")
                return self.get_page_with_retry(url)
            
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            print(f"成功獲取頁面，內容長度: {len(response.content)} 字節")
            return soup
        except Exception as e:
            print(f"獲取頁面失敗 {url}: {e}")
            return None
    
    def get_page_with_retry(self, url: str, max_retries: int = 3) -> Optional[BeautifulSoup]:
        """重試機制獲取頁面"""
        for attempt in range(max_retries):
            try:
                print(f"重試第 {attempt + 1} 次...")
                time.sleep(random.uniform(5, 10))  # 更長的延遲
                
                # 更換 User-Agent
                user_agents = [
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
                ]
                
                headers = {
                    'User-Agent': random.choice(user_agents),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                }
                
                response = self.session.get(url, headers=headers, timeout=25)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    print(f"重試成功，內容長度: {len(response.content)} 字節")
                    return soup
                else:
                    print(f"重試失敗，狀態碼: {response.status_code}")
                    
            except Exception as e:
                print(f"重試第 {attempt + 1} 次失敗: {e}")
                
        print("所有重試都失敗了")
        return None
    
    def extract_product_info(self, product_element) -> Dict[str, Any]:
        """從商品元素中提取商品信息 - 針對衣服商品優化"""
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
                '.a-size-medium',
                '.a-link-normal .a-text-normal'
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
                '.a-color-price',
                '.a-price .a-text-price'
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
                'a[href*="#customerReviews"]',
                '.a-size-small .a-link-normal'
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
                img_src = img_element.get('data-src') or img_element.get('src') or img_element.get('data-old-hires')
                if img_src and ('amazon' in img_src or 'media-amazon' in img_src):
                    if '?' in img_src:
                        img_src = img_src.split('?')[0]
                    product_info['image_url'] = img_src
            
            # 商品URL
            link_selectors = [
                'h2 a',
                'h3 a',
                'a[href*="/dp/"]',
                'a[href*="/gp/product/"]',
                '.s-link-style',
                '.a-link-normal'
            ]
            
            for selector in link_selectors:
                link_element = product_element.select_one(selector)
                if link_element and link_element.get('href'):
                    href = link_element['href']
                    if '/dp/' in href or '/gp/product/' in href:
                        if href.startswith('/'):
                            product_info['product_url'] = f"https://www.amazon.com{href}"
                        else:
                            product_info['product_url'] = href
                        break
            
            # 描述
            desc_selectors = [
                '.a-size-base-plus',
                '.a-size-base',
                '.s-size-mini',
                '.a-color-secondary',
                '.a-size-small',
                '.a-text-normal'
            ]
            
            for selector in desc_selectors:
                desc_element = product_element.select_one(selector)
                if desc_element:
                    desc_text = desc_element.get_text(strip=True)
                    if (len(desc_text) > 10 and 
                        'price' not in desc_text.lower() and 
                        'rating' not in desc_text.lower() and
                        'review' not in desc_text.lower()):
                        product_info['description'] = desc_text
                        break
            
            # 如果沒有找到描述，嘗試從商品名稱中提取關鍵信息
            if 'description' not in product_info and 'name' in product_info:
                name = product_info['name']
                # 提取尺寸、顏色、材質等信息
                size_match = re.search(r'(XS|S|M|L|XL|XXL|XXXL|\d+\.?\d*[xX]\d+\.?\d*)', name)
                color_match = re.search(r'(Black|White|Red|Blue|Green|Yellow|Pink|Purple|Orange|Brown|Gray|Grey|Navy|Beige|Cream)', name, re.I)
                material_match = re.search(r'(Cotton|Polyester|Wool|Silk|Leather|Denim|Linen|Rayon|Spandex|Nylon)', name, re.I)
                
                desc_parts = []
                if size_match:
                    desc_parts.append(f"Size: {size_match.group(1)}")
                if color_match:
                    desc_parts.append(f"Color: {color_match.group(1)}")
                if material_match:
                    desc_parts.append(f"Material: {material_match.group(1)}")
                
                if desc_parts:
                    product_info['description'] = " | ".join(desc_parts)
                
        except Exception as e:
            print(f"提取商品信息時發生錯誤: {e}")
        
        return product_info
    
    def test_clothing_search(self, search_term: str = "men's t-shirt") -> Dict[str, Any]:
        """測試衣服搜索功能"""
        # 構建衣服搜索URL
        search_url = f"https://www.amazon.com/s?k={search_term.replace(' ', '+')}&i=fashion"
        soup = self.get_page(search_url)
        
        if not soup:
            return {"products": [], "categories": []}
        
        products = []
        
        # 尋找搜索結果
        product_containers = soup.select('[data-component-type="s-search-result"]')
        
        if not product_containers:
            product_containers = soup.find_all('div', class_=re.compile(r'.*s-result-item.*', re.I))
        
        print(f"找到 {len(product_containers)} 個衣服商品容器")
        
        for i, container in enumerate(product_containers[:15]):  # 只處理前15個
            print(f"\n--- 處理衣服商品 {i+1} ---")
            product_info = self.extract_product_info(container)
            
            if product_info.get('name'):
                products.append(product_info)
                print(f"商品名稱: {product_info.get('name', 'N/A')[:60]}...")
                print(f"價格: {product_info.get('price', 'N/A')}")
                print(f"評分: {product_info.get('rating', 'N/A')}")
                print(f"評論數: {product_info.get('review_count', 'N/A')}")
                print(f"圖片: {'有' if product_info.get('image_url') else '無'}")
                print(f"鏈接: {'有' if product_info.get('product_url') else '無'}")
                print(f"描述: {product_info.get('description', 'N/A')[:50]}...")
            else:
                print("未找到商品名稱，跳過此項目")
        
        return {"products": products, "categories": []}
    
    def test_multiple_clothing_searches(self) -> Dict[str, Any]:
        """測試多個衣服搜索"""
        search_terms = [
            "men's t-shirt",
            "women's dress", 
            "jeans",
            "sneakers",
            "jacket"
        ]
        
        all_products = []
        
        for term in search_terms:
            print(f"\n=== 測試搜索: {term} ===")
            search_data = self.test_clothing_search(term)
            all_products.extend(search_data['products'])
            
            # 添加延遲
            time.sleep(random.uniform(2, 4))
        
        # 去重
        seen_products = set()
        unique_products = []
        for product in all_products:
            product_key = product.get('name', '') + product.get('price', '')
            if product_key not in seen_products:
                seen_products.add(product_key)
                unique_products.append(product)
        
        return {"products": unique_products, "categories": []}


def main():
    """主測試函數"""
    print("=== Amazon 衣服 BeautifulSoup 爬蟲測試 ===\n")
    
    scraper = AmazonClothingScraperTest()
    
    # 測試多個衣服搜索
    print("測試多個衣服搜索...")
    test_data = scraper.test_multiple_clothing_searches()
    
    print(f"\n總共找到 {len(test_data['products'])} 個衣服商品")
    
    # 統計信息
    total_products = len(test_data['products'])
    products_with_url = sum(1 for p in test_data['products'] if p.get('product_url'))
    products_with_desc = sum(1 for p in test_data['products'] if p.get('description'))
    products_with_price = sum(1 for p in test_data['products'] if p.get('price'))
    products_with_rating = sum(1 for p in test_data['products'] if p.get('rating'))
    products_with_image = sum(1 for p in test_data['products'] if p.get('image_url'))
    
    if total_products > 0:
        print(f"\n商品信息完整性統計:")
        print(f"- 有價格的商品: {products_with_price}/{total_products} ({products_with_price/total_products*100:.1f}%)")
        print(f"- 有評分的商品: {products_with_rating}/{total_products} ({products_with_rating/total_products*100:.1f}%)")
        print(f"- 有鏈接的商品: {products_with_url}/{total_products} ({products_with_url/total_products*100:.1f}%)")
        print(f"- 有描述的商品: {products_with_desc}/{total_products} ({products_with_desc/total_products*100:.1f}%)")
        print(f"- 有圖片的商品: {products_with_image}/{total_products} ({products_with_image/total_products*100:.1f}%)")
    else:
        print("\n沒有找到任何商品，可能是被 Amazon 封鎖或網絡問題")
    
    # 保存測試結果
    output_dir = Path("scraped_content")
    output_dir.mkdir(exist_ok=True)
    
    test_file = output_dir / "amazon_clothing_test_bs4.json"
    with open(test_file, "w", encoding="utf-8") as f:
        json.dump({
            "products": test_data['products'],
            "categories": test_data['categories'],
            "test_info": {
                "total_products": len(test_data['products']),
                "products_with_url": products_with_url,
                "products_with_desc": products_with_desc,
                "products_with_price": products_with_price,
                "products_with_rating": products_with_rating,
                "products_with_image": products_with_image
            }
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n測試結果已保存到: {test_file}")


if __name__ == "__main__":
    main()
