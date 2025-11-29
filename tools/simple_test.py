#!/usr/bin/env python3
"""
簡單的 Amazon 商品信息提取測試
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from pathlib import Path


def test_amazon_extraction():
    """測試 Amazon 商品信息提取"""
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }
    
    url = "https://www.amazon.com/s?k=t-shirt"
    print(f"正在獲取頁面: {url}")
    
    try:
        response = session.get(url, headers=headers, timeout=15)
        print(f"狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            print(f"頁面內容長度: {len(response.content)} 字節")
            
            # 尋找商品容器
            product_containers = soup.select('[data-component-type="s-search-result"]')
            print(f"找到 {len(product_containers)} 個商品容器")
            
            if product_containers:
                # 檢查第一個商品的結構
                first_product = product_containers[0]
                print(f"\n第一個商品的 HTML 結構:")
                print(f"標籤: {first_product.name}")
                print(f"類名: {first_product.get('class', [])}")
                print(f"ID: {first_product.get('id', 'N/A')}")
                
                # 尋找商品名稱
                print(f"\n尋找商品名稱:")
                name_candidates = first_product.find_all(['h2', 'h3', 'span', 'a'], string=True)
                for i, candidate in enumerate(name_candidates[:10]):
                    text = candidate.get_text(strip=True)
                    if text and len(text) > 10:
                        print(f"  {i+1}. {text[:80]}...")
                
                # 尋找價格
                print(f"\n尋找價格:")
                price_candidates = first_product.find_all('span', string=True)
                for i, candidate in enumerate(price_candidates[:10]):
                    text = candidate.get_text(strip=True)
                    if '$' in text or '€' in text or '£' in text:
                        print(f"  {i+1}. {text}")
                
                # 尋找鏈接
                print(f"\n尋找商品鏈接:")
                link_candidates = first_product.find_all('a', href=True)
                for i, candidate in enumerate(link_candidates[:5]):
                    href = candidate.get('href')
                    if '/dp/' in href or '/gp/product/' in href:
                        print(f"  {i+1}. {href}")
                
                # 嘗試提取商品信息
                print(f"\n=== 嘗試提取商品信息 ===")
                
                # 商品名稱
                name_element = first_product.find('h2')
                if name_element:
                    name_link = name_element.find('a')
                    if name_link:
                        name_span = name_link.find('span')
                        if name_span:
                            product_name = name_span.get_text(strip=True)
                            print(f"商品名稱: {product_name}")
                
                # 價格
                price_elements = first_product.find_all('span', class_=re.compile(r'.*price.*', re.I))
                for price_element in price_elements:
                    price_text = price_element.get_text(strip=True)
                    if '$' in price_text:
                        print(f"價格: {price_text}")
                        break
                
                # 評分
                rating_elements = first_product.find_all('span', class_=re.compile(r'.*rating.*|.*star.*', re.I))
                for rating_element in rating_elements:
                    rating_text = rating_element.get_text(strip=True)
                    rating_match = re.search(r'(\d+\.\d+)', rating_text)
                    if rating_match:
                        print(f"評分: {rating_match.group(1)}")
                        break
                
                # 評論數
                review_elements = first_product.find_all('span', string=re.compile(r'\(\d+\)'))
                for review_element in review_elements:
                    review_text = review_element.get_text(strip=True)
                    print(f"評論數: {review_text}")
                    break
                
                # 圖片
                img_element = first_product.find('img')
                if img_element:
                    img_src = img_element.get('src') or img_element.get('data-src')
                    if img_src:
                        print(f"圖片: {img_src[:100]}...")
                
                # 商品鏈接
                link_element = first_product.find('a', href=re.compile(r'/dp/|/gp/product/'))
                if link_element:
                    href = link_element['href']
                    if href.startswith('/'):
                        full_url = f"https://www.amazon.com{href}"
                    else:
                        full_url = href
                    print(f"商品鏈接: {full_url}")
                
        else:
            print(f"HTTP 錯誤: {response.status_code}")
            
    except Exception as e:
        print(f"錯誤: {e}")


if __name__ == "__main__":
    test_amazon_extraction()
