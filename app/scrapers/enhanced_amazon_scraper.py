"""
增強版 Amazon 爬蟲（使用 Playwright）
繼承 EnhancedScraper 並實現 Amazon 特定的提取邏輯
"""

from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import re
import random
from .enhanced_scraper import EnhancedScraper


class EnhancedAmazonScraper(EnhancedScraper):
    """增強版 Amazon 爬蟲"""
    
    def __init__(self, output_dir: str = "data/scraped_content", **kwargs):
        """
        初始化增強版 Amazon 爬蟲
        
        Args:
            output_dir: 輸出目錄
            **kwargs: 傳遞給 EnhancedScraper 的其他參數（proxy, cookies_file, headless 等）
        """
        super().__init__(output_dir, **kwargs)
    
    def extract_product_info(self, product_element) -> Dict[str, Any]:
        """從商品元素中提取商品信息（搜索結果頁面）"""
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
    
    def scrape_product_detail(self, product_url: str) -> Dict[str, Any]:
        """爬取商品詳情頁面的完整信息"""
        detail_info = {}
        
        try:
            print(f"正在獲取商品詳情頁面: {product_url}")
            # 使用 wait_selector 等待關鍵元素加載
            soup = self.get_page(product_url, wait_selector='#productTitle', timeout=30000)
            
            if not soup:
                return detail_info
            
            # 1. 分類路徑 (Breadcrumbs)
            breadcrumbs = []
            breadcrumb_selectors = [
                '#wayfinding-breadcrumbs_feature_div ul.a-unordered-list li span',
                '.a-breadcrumb li span a',
                '#wayfinding-breadcrumbs li span',
                '[aria-label*="breadcrumb"] a'
            ]
            for selector in breadcrumb_selectors:
                breadcrumb_links = soup.select(selector)
                if breadcrumb_links:
                    for link in breadcrumb_links:
                        text = link.get_text(strip=True)
                        if text and text.lower() != 'home':
                            breadcrumbs.append(text)
                    if breadcrumbs:
                        break
            
            if breadcrumbs:
                detail_info['category_path'] = ' > '.join(breadcrumbs)
            
            # 2. 商品名稱（詳情頁面的更準確）
            title_selectors = [
                '#productTitle',
                'h1.a-size-large',
                'span#productTitle',
                'h1.a-product-title'
            ]
            for selector in title_selectors:
                title_el = soup.select_one(selector)
                if title_el:
                    detail_info['name'] = title_el.get_text(strip=True)
                    break
            
            # 3. 評分和評論數
            rating_selectors = [
                '[data-hook="rating-out-of-text"]',
                'span.a-icon-alt',
                '#acrPopover span',
                '.a-icon-alt'
            ]
            for selector in rating_selectors:
                rating_el = soup.select_one(selector)
                if rating_el:
                    rating_text = rating_el.get_text(strip=True)
                    # 提取評分數字 (如 "4.5 out of 5 stars")
                    rating_match = re.search(r'(\d+\.?\d*)\s*out of 5', rating_text, re.I)
                    if rating_match:
                        try:
                            detail_info['rating'] = float(rating_match.group(1))
                        except:
                            pass
                    break
            
            # 評論數
            review_count_selectors = [
                '#acrCustomerReviewText',
                '#acrCustomerReviewLink',
                '[data-hook="total-review-count"]',
                'a[href*="#customerReviews"]'
            ]
            for selector in review_count_selectors:
                review_el = soup.select_one(selector)
                if review_el:
                    review_text = review_el.get_text(strip=True)
                    # 提取數字 (如 "2,317 ratings" 或 "2,317")
                    review_match = re.search(r'([\d,]+)', review_text)
                    if review_match:
                        detail_info['review_count'] = review_match.group(1)
                    break
            
            # 4. 過去一個月購買數量
            all_text = soup.get_text()
            bought_match = re.search(r'([\d,]+[KMBkkmb]?\+?)\s*bought in past month', all_text, re.I)
            if bought_match:
                detail_info['bought_in_past_month'] = bought_match.group(1)
            
            # 5. 價格（當前選擇的價格）
            price_selectors = [
                '.a-price-whole',
                '#priceblock_ourprice',
                '#priceblock_dealprice',
                '.a-price .a-offscreen',
                'span.a-price-whole',
                '.a-color-price'
            ]
            for selector in price_selectors:
                price_el = soup.select_one(selector)
                if price_el:
                    price_text = price_el.get_text(strip=True)
                    price_match = re.search(r'\$?([\d,]+\.?\d*)', price_text)
                    if price_match:
                        detail_info['price'] = f"${price_match.group(1)}"
                        break
            
            # 6. 顏色選項
            color_options = []
            color_selectors = [
                '#variation_color_name ul li',
                '#color_name_0 .a-button-inner',
                '[data-csa-c-content-id="twister"] .a-button-inner',
                '.swatchElement span[data-asin]'
            ]
            for selector in color_selectors:
                color_elements = soup.select(selector)
                if color_elements:
                    for color_el in color_elements:
                        color_info = {}
                        # 顏色名稱
                        color_name_el = color_el.select_one('span, img[alt], .a-button-text')
                        if color_name_el:
                            color_name = color_name_el.get('alt') or color_name_el.get_text(strip=True)
                            if color_name:
                                color_info['color_name'] = color_name
                        # 顏色價格
                        color_price_text = color_el.get_text()
                        color_price_match = re.search(r'\$([\d,]+\.?\d*)', color_price_text)
                        if color_price_match:
                            color_info['color_price'] = f"${color_price_match.group(1)}"
                        if color_info:
                            color_options.append(color_info)
                    if color_options:
                        break
            
            if color_options:
                detail_info['color_options'] = color_options
            
            # 7. 尺寸選項
            size_options = []
            size_selectors = [
                '#variation_size_name select option',
                '#size_name_0 .a-button-text',
                '[data-csa-c-content-id="twister_size_name"] .a-button-text',
                'select[name*="size"] option'
            ]
            for selector in size_selectors:
                size_elements = soup.select(selector)
                if size_elements:
                    for size_el in size_elements:
                        size_text = size_el.get_text(strip=True)
                        if size_text and size_text.lower() not in ['select', 'choose', 'size']:
                            size_options.append(size_text)
                    if size_options:
                        break
            
            if size_options:
                detail_info['size_options'] = size_options
            
            # 8. 商品詳情 (Product Details)
            product_details = {}
            detail_rows = soup.select('#productDetails_detailBullets_sections1 tr, .prodDetTable tr')
            for row in detail_rows:
                th = row.find('th')
                td = row.find('td')
                if th and td:
                    key = th.get_text(strip=True)
                    value = td.get_text(strip=True)
                    if key and value:
                        product_details[key] = value
            
            # 也嘗試其他詳情格式
            if not product_details:
                detail_sections = soup.select('#feature-bullets ul li span.a-list-item, #productDescription p')
                if detail_sections:
                    details_text = ' | '.join([s.get_text(strip=True) for s in detail_sections[:5]])
                    if details_text:
                        product_details['description'] = details_text
            
            if product_details:
                detail_info['product_details'] = product_details
            
            # 9. 關於商品的內容 (About This Item)
            about_selectors = [
                '#feature-bullets',
                '#productDescription',
                '[data-feature-name="productDescription"]',
                '.a-section.a-spacing-medium'
            ]
            about_items = []
            for selector in about_selectors:
                about_section = soup.select_one(selector)
                if about_section:
                    items = about_section.select('li span, p')
                    for item in items[:10]:  # 限制前10項
                        text = item.get_text(strip=True)
                        if text and len(text) > 20:  # 過濾太短的內容
                            about_items.append(text)
                    if about_items:
                        break
            
            if about_items:
                detail_info['about_this_item'] = about_items
            
            # 10. 圖片URL（高分辨率）
            img_selectors = [
                '#landingImage',
                '#main-image',
                '[data-main-image]',
                'img[data-a-dynamic-image]'
            ]
            for selector in img_selectors:
                img_el = soup.select_one(selector)
                if img_el:
                    img_src = img_el.get('src') or img_el.get('data-src')
                    if img_src:
                        detail_info['image_url'] = img_src
                        break
            
        except Exception as e:
            print(f"爬取商品詳情時發生錯誤: {e}")
        
        return detail_info
    
    def scrape_products(self, search_terms: List[str], fetch_details: bool = True) -> List[Dict[str, Any]]:
        """爬取商品信息"""
        all_products = []
        
        try:
            for search_term in search_terms:
                search_url = f"https://www.amazon.com/s?k={search_term.replace(' ', '+')}"
                # 等待搜索結果加載
                soup = self.get_page(search_url, wait_selector='[data-component-type="s-search-result"]', timeout=30000)
                
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
                
                for i, container in enumerate(product_containers[:10]):  # 限制處理前10個（詳情頁面會增加請求）
                    print(f"處理商品 {i+1}/{min(10, len(product_containers))}")
                    product_info = self.extract_product_info(container)
                    
                    if product_info.get('name'):
                        # 如果需要獲取詳情，且有商品URL，則訪問詳情頁面
                        if fetch_details and product_info.get('product_url'):
                            try:
                                detail_info = self.scrape_product_detail(product_info['product_url'])
                                # 合併詳情信息（詳情頁面的信息優先）
                                product_info.update(detail_info)
                                # 保留原始的商品URL
                                product_info['product_url'] = product_info.get('product_url')
                                self.add_delay(2, 4)  # 詳情頁面請求後延遲
                            except Exception as e:
                                print(f"獲取商品詳情失敗: {e}")
                                # 即使詳情獲取失敗，仍保留搜索結果的基本信息
                        
                        all_products.append(product_info)
                
                self.add_delay(3, 6)  # 添加延遲避免被封鎖
        finally:
            # 保存 Cookies 和請求日誌
            self.save_cookies()
            if self.enable_request_monitoring:
                self.save_request_logs()
        
        return all_products
    
    def scrape_categories(self) -> List[Dict[str, Any]]:
        """爬取分類信息"""
        try:
            soup = self.get_page("https://www.amazon.com/", wait_selector='#nav-xshop', timeout=30000)
            
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
        finally:
            # 保存 Cookies
            self.save_cookies()

