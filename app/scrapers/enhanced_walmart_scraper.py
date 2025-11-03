"""
增強版 Walmart 爬蟲（使用 Playwright）
繼承 EnhancedScraper 並實現 Walmart 特定的提取邏輯
"""

from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import re
import random
from .enhanced_scraper import EnhancedScraper


class EnhancedWalmartScraper(EnhancedScraper):
    """增強版 Walmart 爬蟲"""
    
    def __init__(self, output_dir: str = "data/scraped_content", **kwargs):
        """
        初始化增強版 Walmart 爬蟲
        
        Args:
            output_dir: 輸出目錄
            **kwargs: 傳遞給 EnhancedScraper 的其他參數（proxy, cookies_file, headless 等）
        """
        super().__init__(output_dir, **kwargs)
    
    def extract_product_info(self, product_element) -> Dict[str, Any]:
        """從商品元素中提取商品信息（搜索結果頁面）"""
        info: Dict[str, Any] = {}

        try:
            # 名稱
            title_el = product_element.select_one('[data-automation-id="product-title"] a') or product_element.find('a', href=True)
            if title_el:
                name_text = title_el.get_text(strip=True)
                if name_text:
                    info['name'] = name_text

            # 價格
            price_el = product_element.select_one('[data-automation-id="product-price"] span') or product_element.find('span', string=True)
            if price_el:
                text = price_el.get_text(strip=True)
                m = re.search(r'\$[\d,.]+', text)
                if m:
                    info['price'] = m.group()

            # 評分與評論
            rating_el = product_element.select_one('[aria-label*="out of 5"]')
            if rating_el:
                m = re.search(r'(\d+\.?\d*) out of 5', rating_el.get('aria-label', ''))
                if m:
                    try:
                        info['rating'] = float(m.group(1))
                    except Exception:
                        pass
            reviews_el = product_element.find('span', string=re.compile(r'Reviews|ratings', re.I))
            if reviews_el:
                info['review_count'] = reviews_el.get_text(strip=True)

            # 圖片
            img_el = product_element.find('img')
            if img_el:
                info['image_url'] = img_el.get('src') or img_el.get('data-src')

            # 連結
            if title_el and title_el.get('href'):
                href = title_el['href']
                info['product_url'] = href if href.startswith('http') else f"https://www.walmart.com{href}"

            # 描述
            if 'name' in info:
                features = self.extract_product_features(info['name'])
                info['description'] = self.create_description(info['name'], features)
                
        except Exception as e:
            print(f"提取商品信息時發生錯誤: {e}")
        
        return info
    
    def scrape_product_detail(self, product_url: str) -> Dict[str, Any]:
        """爬取 Walmart 商品詳情頁面的完整信息"""
        detail_info = {}
        
        try:
            print(f"正在獲取 Walmart 商品詳情頁面: {product_url}")
            # 等待關鍵元素加載
            soup = self.get_page(product_url, wait_selector='h1[itemprop="name"]', timeout=30000)
            
            if not soup:
                return detail_info
            
            # 1. 分類路徑 (Breadcrumbs)
            breadcrumbs = []
            breadcrumb_selectors = [
                'nav[aria-label="Breadcrumb"] ol li a',
                '.breadcrumb-list a',
                'ol[class*="breadcrumb"] a',
                'nav ol li a'
            ]
            for selector in breadcrumb_selectors:
                breadcrumb_links = soup.select(selector)
                if breadcrumb_links:
                    for link in breadcrumb_links:
                        text = link.get_text(strip=True)
                        if text:
                            breadcrumbs.append(text)
                    if breadcrumbs:
                        break
            
            if breadcrumbs:
                detail_info['category_path'] = ' > '.join(breadcrumbs)
            
            # 2. 商品名稱
            title_selectors = [
                'h1[itemprop="name"]',
                'h1.prod-ProductTitle',
                'h1[data-automation-id="product-title"]',
                'h1'
            ]
            for selector in title_selectors:
                title_el = soup.select_one(selector)
                if title_el:
                    detail_info['name'] = title_el.get_text(strip=True)
                    break
            
            # 3. 評分和評論數
            rating_selectors = [
                '[aria-label*="out of 5"]',
                '.rating-number',
                '[data-automation-id="product-rating"]'
            ]
            for selector in rating_selectors:
                rating_el = soup.select_one(selector)
                if rating_el:
                    rating_text = rating_el.get('aria-label') or rating_el.get_text(strip=True)
                    rating_match = re.search(r'(\d+\.?\d*)\s*out of 5', rating_text, re.I)
                    if rating_match:
                        try:
                            detail_info['rating'] = float(rating_match.group(1))
                        except:
                            pass
                    break
            
            # 評論數
            review_selectors = [
                '[data-automation-id="product-review-count"]',
                'a[href*="reviews"]',
                '.prod-ReviewsHeader-count'
            ]
            for selector in review_selectors:
                review_el = soup.select_one(selector)
                if review_el:
                    review_text = review_el.get_text(strip=True)
                    review_match = re.search(r'([\d,]+)', review_text)
                    if review_match:
                        detail_info['review_count'] = review_match.group(1)
                    break
            
            # 4. 價格
            price_selectors = [
                'span[itemprop="price"]',
                '[data-automation-id="product-price"]',
                '.price-characteristic',
                '[class*="price"]'
            ]
            for selector in price_selectors:
                price_el = soup.select_one(selector)
                if price_el:
                    price_text = price_el.get_text(strip=True)
                    price_match = re.search(r'\$?([\d,]+\.?\d*)', price_text)
                    if price_match:
                        detail_info['price'] = f"${price_match.group(1)}"
                        break
            
            # 5. 顏色選項
            color_options = []
            color_selectors = [
                '[data-automation-id="product-color-option"]',
                '.product-color-option',
                'button[aria-label*="Color"]',
                'select[name*="color"] option'
            ]
            for selector in color_selectors:
                color_elements = soup.select(selector)
                if color_elements:
                    for color_el in color_elements:
                        color_text = color_el.get_text(strip=True) or color_el.get('aria-label', '')
                        if color_text and color_text.lower() not in ['select', 'choose']:
                            color_info = {'color_name': color_text}
                            # 嘗試獲取顏色價格
                            color_price_text = color_el.get_text()
                            color_price_match = re.search(r'\$([\d,]+\.?\d*)', color_price_text)
                            if color_price_match:
                                color_info['color_price'] = f"${color_price_match.group(1)}"
                            color_options.append(color_info)
                    if color_options:
                        break
            
            if color_options:
                detail_info['color_options'] = color_options
            
            # 6. 尺寸選項
            size_options = []
            size_selectors = [
                '[data-automation-id="product-size-option"]',
                '.product-size-option',
                'button[aria-label*="Size"]',
                'select[name*="size"] option'
            ]
            for selector in size_selectors:
                size_elements = soup.select(selector)
                if size_elements:
                    for size_el in size_elements:
                        size_text = size_el.get_text(strip=True) or size_el.get('aria-label', '')
                        if size_text and size_text.lower() not in ['select', 'choose', 'size']:
                            size_options.append(size_text)
                    if size_options:
                        break
            
            if size_options:
                detail_info['size_options'] = size_options
            
            # 7. 商品詳情
            product_details = {}
            detail_selectors = [
                '[data-automation-id="product-details"] table tr',
                '.product-details-table tr',
                '[class*="specifications"] table tr'
            ]
            for selector in detail_selectors:
                detail_rows = soup.select(selector)
                if detail_rows:
                    for row in detail_rows:
                        cells = row.select('td, th')
                        if len(cells) >= 2:
                            key = cells[0].get_text(strip=True)
                            value = cells[1].get_text(strip=True)
                            if key and value:
                                product_details[key] = value
                    if product_details:
                        break
            
            if product_details:
                detail_info['product_details'] = product_details
            
            # 8. 關於商品的內容
            about_selectors = [
                '[data-automation-id="product-description"]',
                '.product-description',
                '#about-product-section',
                '[class*="description"]'
            ]
            about_items = []
            for selector in about_selectors:
                about_section = soup.select_one(selector)
                if about_section:
                    items = about_section.select('p, li, div')
                    for item in items[:10]:
                        text = item.get_text(strip=True)
                        if text and len(text) > 20:
                            about_items.append(text)
                    if about_items:
                        break
            
            if about_items:
                detail_info['about_this_item'] = about_items
            
            # 9. 圖片URL
            img_selectors = [
                '[data-automation-id="product-image"] img',
                '[itemprop="image"]',
                '.product-hero-image img',
                'img[alt*="product"]'
            ]
            for selector in img_selectors:
                img_el = soup.select_one(selector)
                if img_el:
                    img_src = img_el.get('src') or img_el.get('data-src')
                    if img_src:
                        detail_info['image_url'] = img_src
                        break
            
        except Exception as e:
            print(f"爬取 Walmart 商品詳情時發生錯誤: {e}")
        
        return detail_info
    
    def scrape_products(self, search_terms: List[str], fetch_details: bool = True) -> List[Dict[str, Any]]:
        """爬取商品信息"""
        results: List[Dict[str, Any]] = []
        
        try:
            for term in search_terms:
                url = f"https://www.walmart.com/search?q={term.replace(' ', '+')}"
                # 等待搜索結果加載
                soup = self.get_page(url, wait_selector='[data-automation-id="search-result-gridview-item"]', timeout=30000)
                
                if not soup:
                    continue

                # 常見結果卡片容器
                candidates = soup.select('[data-automation-id="search-result-gridview-item"]')
                if not candidates:
                    candidates = soup.select('div.search-result-gridview-item')
                if not candidates:
                    candidates = soup.select('[data-item-id]')

                for card in candidates[:10]:  # 限制處理前10個
                    info = self.extract_product_info(card)

                    if info.get('name'):
                        # 如果需要獲取詳情，且有商品URL，則訪問詳情頁面
                        if fetch_details and info.get('product_url'):
                            try:
                                detail_info = self.scrape_product_detail(info['product_url'])
                                # 合併詳情信息（詳情頁面的信息優先）
                                info.update(detail_info)
                                self.add_delay(2, 4)  # 詳情頁面請求後延遲
                            except Exception as e:
                                print(f"獲取 Walmart 商品詳情失敗: {e}")
                        
                        results.append(info)
        finally:
            # 保存 Cookies 和請求日誌
            self.save_cookies()
            if self.enable_request_monitoring:
                self.save_request_logs()
        
        return results

    def scrape_categories(self) -> List[Dict[str, Any]]:
        """爬取分類信息"""
        try:
            soup = self.get_page('https://www.walmart.com/', wait_selector='nav', timeout=30000)
            
            if not soup:
                return []

            cats: List[Dict[str, Any]] = []
            selectors = [
                'nav a',
                'header a',
                'a[aria-label*="Shop"]',
                'a[role="menuitem"]',
            ]
            for sel in selectors:
                for a in soup.select(sel):
                    text = a.get_text(strip=True)
                    href = a.get('href') or ''
                    if not text or not href:
                        continue
                    if len(text) < 2 or len(text) > 40:
                        continue
                    if any(bad in text.lower() for bad in ['sign', 'account', 'cart', 'pickup', 'reorder', 'registry']):
                        continue
                    cats.append({
                        'category_name': text,
                        'url': href if href.startswith('http') else f"https://www.walmart.com{href}"
                    })

            seen = set()
            uniq = []
            for c in cats:
                if c['category_name'] not in seen:
                    seen.add(c['category_name'])
                    uniq.append(c)
            
            return uniq[:20]
        finally:
            # 保存 Cookies
            self.save_cookies()

