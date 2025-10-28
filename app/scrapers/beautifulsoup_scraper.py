"""
BeautifulSoup 爬蟲實現
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
import re
import random
from .base_scraper import BaseScraper


class BeautifulSoupScraper(BaseScraper):
    """BeautifulSoup 爬蟲"""
    
    def __init__(self, output_dir: str = "data/scraped_content"):
        super().__init__(output_dir)
        self.session = requests.Session()
        
        # 隨機 User-Agent 列表
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        ]
        
        self.session.headers.update({
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        })
    
    def get_page(self, url: str) -> Optional[BeautifulSoup]:
        """獲取頁面內容"""
        try:
            print(f"正在獲取頁面: {url}")
            
            # 增加隨機延遲
            delay = random.uniform(3, 8)
            print(f"等待 {delay:.1f} 秒...")
            self.add_delay(delay, delay + 1)
            
            # 隨機更新 User-Agent
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            ]
            self.session.headers['User-Agent'] = random.choice(user_agents)
            
            # 添加 Referer
            if 'amazon.com' in url:
                self.session.headers['Referer'] = 'https://www.amazon.com/'
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # 檢查是否被重定向到驗證頁面
            if 'captcha' in response.url.lower() or 'robot' in response.url.lower():
                print("檢測到驗證頁面，跳過此 URL")
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            print(f"成功獲取頁面，內容長度: {len(response.content)} 字節")
            return soup
        except Exception as e:
            print(f"獲取頁面失敗: {e}")
            return None
    
    def extract_product_info(self, product_element) -> Dict[str, Any]:
        """從商品元素中提取商品信息"""
        product_info = {}
        
        try:
            # 商品名稱
            name_element = product_element.find('h2')
            if name_element:
                name_link = name_element.find('a')
                if name_link:
                    name_span = name_link.find('span')
                    if name_span:
                        product_info['name'] = name_span.get_text(strip=True)
            
            # 如果沒找到，嘗試其他方法
            if 'name' not in product_info:
                name_candidates = product_element.find_all(['h2', 'h3'], string=True)
                for candidate in name_candidates:
                    text = candidate.get_text(strip=True)
                    if text and len(text) > 10 and 'Featured' not in text:
                        product_info['name'] = text
                        break
            
            # 價格
            price_found = False
            all_spans = product_element.find_all('span', string=True)
            for span in all_spans:
                text = span.get_text(strip=True)
                if '$' in text and any(c.isdigit() for c in text):
                    product_info['price'] = text
                    price_found = True
                    break
            
            # 如果沒找到價格，嘗試從所有文字中提取
            if not price_found:
                all_text = product_element.get_text()
                price_match = re.search(r'\$[\d,]+\.?\d*', all_text)
                if price_match:
                    product_info['price'] = price_match.group()
            
            # 評分
            for span in all_spans:
                text = span.get_text(strip=True)
                if 'out of 5 stars' in text:
                    rating_match = re.search(r'(\d+\.\d+)', text)
                    if rating_match:
                        try:
                            product_info['rating'] = float(rating_match.group(1))
                            break
                        except:
                            continue
            
            # 評論數
            for span in all_spans:
                text = span.get_text(strip=True)
                if re.search(r'\(\d+\)', text):
                    product_info['review_count'] = text
                    break
            
            # 圖片URL
            img_element = product_element.find('img')
            if img_element:
                img_src = img_element.get('src') or img_element.get('data-src')
                if img_src and 'amazon' in img_src:
                    product_info['image_url'] = img_src
            
            # 商品URL
            link_element = product_element.find('a', href=re.compile(r'/dp/|/gp/product/'))
            if link_element:
                href = link_element['href']
                if href.startswith('/'):
                    product_info['product_url'] = f"https://www.amazon.com{href}"
                else:
                    product_info['product_url'] = href
            
            # 描述 - 使用基礎類的方法
            if 'name' in product_info:
                features = self.extract_product_features(product_info['name'])
                product_info['description'] = self.create_description(product_info['name'], features)
                
        except Exception as e:
            print(f"提取商品信息時發生錯誤: {e}")
        
        return product_info
    
    def scrape_products(self, search_terms: List[str]) -> List[Dict[str, Any]]:
        """爬取商品信息"""
        all_products = []
        
        for search_term in search_terms:
            search_url = f"https://www.amazon.com/s?k={search_term.replace(' ', '+')}"
            soup = self.get_page(search_url)
            
            if not soup:
                continue
            
            # 尋找商品容器 - 嘗試多種選擇器
            product_containers = soup.select('[data-component-type="s-search-result"]')
            if not product_containers:
                # 嘗試其他可能的選擇器
                product_containers = soup.select('.s-result-item')
            if not product_containers:
                product_containers = soup.select('[data-asin]')
            
            print(f"找到 {len(product_containers)} 個商品容器")
            
            # 調試：檢查頁面內容
            if len(product_containers) == 0:
                print("未找到商品容器，檢查頁面內容...")
                # 檢查是否有驗證頁面
                if soup.find('title') and 'captcha' in soup.find('title').get_text().lower():
                    print("檢測到驗證頁面")
                # 檢查是否有搜索結果
                search_results = soup.find('div', {'id': 'search'})
                if search_results:
                    print(f"搜索結果區域存在，內容長度: {len(search_results.get_text())}")
                else:
                    print("未找到搜索結果區域")
            
            for i, container in enumerate(product_containers[:20]):  # 限制處理前20個
                print(f"處理商品 {i+1}")
                product_info = self.extract_product_info(container)
                
                if product_info.get('name'):
                    all_products.append(product_info)
            
            self.add_delay(3, 6)  # 添加延遲避免被封鎖
        
        return all_products
    
    def scrape_categories(self) -> List[Dict[str, Any]]:
        """爬取分類信息"""
        soup = self.get_page("https://www.amazon.com/")
        
        if not soup:
            return []
        
        categories = []
        
        # 尋找分類鏈接
        category_selectors = [
            '#nav-xshop a',
            '.nav-a',
            '#nav-main a',
            '.nav-logo-base + .nav-sprite .nav-a',
            '.nav-flyout-content a',
            '.nav-panel a'
        ]
        
        for selector in category_selectors:
            links = soup.select(selector)
            for link in links:
                text = link.get_text(strip=True)
                href = link.get('href', '')
                
                if (text and len(text) > 2 and len(text) < 50 and 
                    'search' not in text.lower() and 
                    'sign' not in text.lower() and
                    'account' not in text.lower() and
                    'cart' not in text.lower()):
                    
                    categories.append({
                        'category_name': text,
                        'url': href if href.startswith('http') else f"https://www.amazon.com{href}"
                    })
        
        # 去重
        seen = set()
        unique_categories = []
        for cat in categories:
            if cat['category_name'] not in seen:
                seen.add(cat['category_name'])
                unique_categories.append(cat)
        
        return unique_categories[:20]  # 限制返回前20個分類
