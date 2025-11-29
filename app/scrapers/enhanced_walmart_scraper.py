"""
增強版 Walmart 爬蟲（使用 Playwright）
繼承 EnhancedScraper 並實現 Walmart 特定的提取邏輯
"""

from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import re
import random
import requests
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
        # 透過 r.jina.ai 代理取得靜態 Markdown，繞過 Walmart 封鎖頁
        self.proxy_base = "https://r.jina.ai/"
        self.proxy_session = requests.Session()
        self.proxy_session.headers.update({
            'User-Agent': self.user_agent or random.choice(self.user_agents),
            'Accept': 'text/plain,text/markdown;q=0.9,*/*;q=0.8',
        })

    def _fetch_proxy_text(self, url: str) -> str:
        """透過 r.jina.ai 取得 Walmart 頁面 Markdown 內容"""
        try:
            proxied_url = f"{self.proxy_base}{url}"
            print(f"嘗試透過 r.jina.ai 取得內容: {proxied_url}")
            resp = self.proxy_session.get(proxied_url, timeout=30)
            resp.raise_for_status()
            text = resp.text
            if "Markdown Content" in text:
                return text
        except Exception as e:
            print(f"透過 r.jina.ai 取得 Walmart 內容失敗: {e}")
        return ""

    def _parse_proxy_products(self, markdown_text: str, limit: int = 10) -> List[Dict[str, Any]]:
        """從 r.jina.ai 轉換的 Markdown 解析商品資訊"""
        products: List[Dict[str, Any]] = []
        if not markdown_text:
            return products

        seen_urls = set()
        product_pattern = re.finditer(
            r'\[(?P<name>[^\]]{5,200})\]\((?P<url>https://www\.walmart\.com/ip/[^\)]+)\)',
            markdown_text
        )

        for match in product_pattern:
            name = match.group('name').strip()
            url = match.group('url').strip()

            if url in seen_urls:
                continue
            seen_urls.add(url)

            snippet = markdown_text[match.end():match.end() + 1200]
            price_match = re.search(r'\$[\d,.]+', snippet)
            rating_match = re.search(r'(\d+\.?\d*)\s*out of 5', snippet, re.I)
            review_match = re.search(r'([\d,]+)\s+(reviews|ratings)', snippet, re.I)
            image_match = re.search(r'!\[[^\]]*?\]\((https://i5\.walmartimages\.com[^\)]+)\)', snippet)

            info = {
                'name': name,
                'product_url': url,
                'source': 'walmart_proxy'
            }

            if price_match:
                info['price'] = price_match.group()

            if rating_match:
                try:
                    info['rating'] = float(rating_match.group(1))
                except ValueError:
                    pass

            if review_match:
                info['review_count'] = review_match.group(1)

            if image_match:
                info['image_url'] = image_match.group(1)

            features = self.extract_product_features(name)
            info['description'] = self.create_description(name, features)

            products.append(info)

            if len(products) >= limit:
                break

        return products

    def _parse_proxy_categories(self, markdown_text: str, limit: int = 10) -> List[Dict[str, str]]:
        """從 Markdown 內容解析分類連結"""
        categories: List[Dict[str, str]] = []
        if not markdown_text:
            return categories

        seen = set()
        cat_pattern = re.finditer(
            r'\[(?P<label>[^\]]{3,50})\]\((?P<url>https://www\.walmart\.com/(?:browse|shop)[^\)]+)\)',
            markdown_text
        )
        for match in cat_pattern:
            label = match.group('label').strip()
            url = match.group('url').strip()
            if not label or label.lower() in seen:
                continue
            seen.add(label.lower())
            categories.append({
                'category_name': label,
                'url': url
            })
            if len(categories) >= limit:
                break

        return categories
    
    def _extract_next_data(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """從 __NEXT_DATA__ 提取商品數據"""
        import json
        products = []
        try:
            script_el = soup.find('script', id='__NEXT_DATA__')
            if not script_el:
                return products
            
            data = json.loads(script_el.get_text())
            # 導航路徑: props -> pageProps -> initialData -> searchResult -> itemStacks
            initial_data = data.get('props', {}).get('pageProps', {}).get('initialData', {})
            search_result = initial_data.get('searchResult', {})
            item_stacks = search_result.get('itemStacks', [])
            
            for stack in item_stacks:
                items = stack.get('items', [])
                for item in items:
                    # 排除非商品項目 (例如廣告或 banner)
                    if item.get('__typename') != 'Product' and 'name' not in item:
                        continue
                        
                    # 提取欄位
                    info = {}
                    info['name'] = item.get('name')
                    
                    # 連結
                    canonical_url = item.get('canonicalUrl', '')
                    if canonical_url:
                        info['product_url'] = f"https://www.walmart.com{canonical_url}"
                    
                    # 圖片
                    image_info = item.get('image', {})
                    if image_info:
                        info['image_url'] = image_info.get('src')
                    
                    # 價格
                    price_info = item.get('priceInfo', {})
                    current_price = price_info.get('currentPrice', {})
                    if current_price:
                        price_val = current_price.get('price')
                        if price_val:
                            info['price'] = f"${price_val}"
                            
                    # 評分與評論
                    rating = item.get('averageRating')
                    if rating:
                        info['rating'] = float(rating)
                        
                    review_count = item.get('numberOfReviews')
                    if review_count:
                        info['review_count'] = review_count
                        
                    # 描述 (如果有簡短描述)
                    if 'description' in item:
                        info['description'] = item['description']
                    elif info.get('name'):
                        features = self.extract_product_features(info['name'])
                        info['description'] = self.create_description(info['name'], features)
                        
                    info['source'] = 'walmart_next_data'
                    
                    if info.get('name'):
                        products.append(info)
                        
        except Exception as e:
            print(f"解析 __NEXT_DATA__ 失敗: {e}")
            
        return products

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
                
                proxy_used = False
                
                # 策略 1: 嘗試解析 __NEXT_DATA__ JSON
                if soup:
                    next_data_products = self._extract_next_data(soup)
                    if next_data_products:
                        print(f"成功從 __NEXT_DATA__ 提取 {len(next_data_products)} 筆商品")
                        results.extend(next_data_products)
                        continue  # JSON 解析成功，跳過後續 DOM 解析與代理

                if not soup:
                    proxy_text = self._fetch_proxy_text(url)
                    proxy_results = self._parse_proxy_products(proxy_text)
                    if proxy_results:
                        print(f"透過 r.jina.ai 取得 {len(proxy_results)} 筆商品")
                        results.extend(proxy_results)
                        proxy_used = True
                    continue

                # 常見結果卡片容器
                candidates = soup.select('[data-automation-id="search-result-gridview-item"]')
                if not candidates:
                    candidates = soup.select('div.search-result-gridview-item')
                if not candidates:
                    candidates = soup.select('[data-item-id]')

                if not candidates:
                    proxy_text = self._fetch_proxy_text(url)
                    proxy_results = self._parse_proxy_products(proxy_text)
                    if proxy_results:
                        print(f"透過 r.jina.ai 取得 {len(proxy_results)} 筆商品（HTML 無結果）")
                        results.extend(proxy_results)
                        proxy_used = True

                if proxy_used:
                    continue

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
            proxy_used = False
            soup = self.get_page('https://www.walmart.com/', wait_selector='nav', timeout=30000)
            
            if not soup:
                proxy_text = self._fetch_proxy_text('https://www.walmart.com/')
                return self._parse_proxy_categories(proxy_text)

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

            if not cats:
                proxy_text = self._fetch_proxy_text('https://www.walmart.com/')
                cats = self._parse_proxy_categories(proxy_text)

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

