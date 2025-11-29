#!/usr/bin/env python3
"""
調試 Amazon HTML 結構
"""

import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path


def debug_amazon_html():
    """調試 Amazon 的 HTML 結構"""
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
            
            # 保存原始 HTML 用於調試
            with open("debug_amazon.html", "w", encoding="utf-8") as f:
                f.write(soup.prettify())
            print("原始 HTML 已保存到 debug_amazon.html")
            
            # 尋找商品容器
            print("\n=== 尋找商品容器 ===")
            
            # 嘗試不同的選擇器
            selectors = [
                '[data-component-type="s-search-result"]',
                '.s-result-item',
                '[data-asin]',
                '.s-card-container',
                '.s-widget-container',
                '.s-result-list',
                '.s-search-results'
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                print(f"選擇器 '{selector}': 找到 {len(elements)} 個元素")
                
                if elements and len(elements) > 0:
                    # 檢查第一個元素的結構
                    first_element = elements[0]
                    print(f"  第一個元素的標籤: {first_element.name}")
                    print(f"  第一個元素的類名: {first_element.get('class', [])}")
                    print(f"  第一個元素的 ID: {first_element.get('id', 'N/A')}")
                    
                    # 尋找商品名稱
                    name_candidates = first_element.find_all(['h2', 'h3', 'span', 'a'], string=True)
                    print(f"  可能的商品名稱候選:")
                    for i, candidate in enumerate(name_candidates[:5]):
                        text = candidate.get_text(strip=True)
                        if text and len(text) > 10:
                            print(f"    {i+1}. {text[:50]}...")
                    
                    # 尋找價格
                    price_candidates = first_element.find_all('span', string=True)
                    print(f"  可能的價格候選:")
                    for i, candidate in enumerate(price_candidates[:5]):
                        text = candidate.get_text(strip=True)
                        if '$' in text or '€' in text or '£' in text:
                            print(f"    {i+1}. {text}")
                    
                    break
            
            # 尋找所有包含 "t-shirt" 的文字
            print("\n=== 尋找包含 't-shirt' 的文字 ===")
            tshirt_elements = soup.find_all(string=lambda text: text and 't-shirt' in text.lower())
            for i, element in enumerate(tshirt_elements[:10]):
                print(f"{i+1}. {element.strip()[:100]}...")
            
            # 尋找所有包含價格的文字
            print("\n=== 尋找包含價格的文字 ===")
            price_elements = soup.find_all(string=lambda text: text and '$' in text and any(c.isdigit() for c in text))
            for i, element in enumerate(price_elements[:10]):
                print(f"{i+1}. {element.strip()}")
                
        else:
            print(f"HTTP 錯誤: {response.status_code}")
            
    except Exception as e:
        print(f"錯誤: {e}")


if __name__ == "__main__":
    debug_amazon_html()
