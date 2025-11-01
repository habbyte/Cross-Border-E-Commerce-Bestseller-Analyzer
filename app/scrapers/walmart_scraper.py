"""
Walmart 爬蟲實作（BeautifulSoup）
僅用於教學與測試，請遵守 Walmart 服務條款與 robots.txt。
"""

from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import requests
import random
import re

from .base_scraper import BaseScraper


class WalmartScraper(BaseScraper):
    """Walmart 爬蟲（以公開頁面為目標，容錯解析）"""

    def __init__(self, output_dir: str = "data/scraped_content"):
        super().__init__(output_dir)
        self.session = requests.Session()
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        ]
        self.session.headers.update({
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,zh-TW;q=0.8',
            'Connection': 'keep-alive',
        })

    def _get_page(self, url: str) -> Optional[BeautifulSoup]:
        try:
            self.add_delay(2, 5)
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            if any(k in resp.url.lower() for k in ['captcha', 'robot']):
                return None
            return BeautifulSoup(resp.content, 'html.parser')
        except Exception:
            return None

    def scrape_products(self, search_terms: List[str]) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for term in search_terms:
            url = f"https://www.walmart.com/search?q={term.replace(' ', '+')}"
            soup = self._get_page(url)
            if not soup:
                continue

            # 常見結果卡片容器
            candidates = soup.select('[data-automation-id="search-result-gridview-item"]')
            if not candidates:
                candidates = soup.select('div.search-result-gridview-item')
            if not candidates:
                candidates = soup.select('[data-item-id]')

            for card in candidates[:20]:
                info: Dict[str, Any] = {}

                # 名稱
                title_el = card.select_one('[data-automation-id="product-title"] a') or card.find('a', href=True)
                if title_el:
                    name_text = title_el.get_text(strip=True)
                    if name_text:
                        info['name'] = name_text

                # 價格
                price_el = card.select_one('[data-automation-id="product-price"] span') or card.find('span', string=True)
                if price_el:
                    text = price_el.get_text(strip=True)
                    m = re.search(r'\$[\d,.]+', text)
                    if m:
                        info['price'] = m.group()

                # 評分與評論
                rating_el = card.select_one('[aria-label*="out of 5"]')
                if rating_el:
                    m = re.search(r'(\d+\.?\d*) out of 5', rating_el.get('aria-label', ''))
                    if m:
                        try:
                            info['rating'] = float(m.group(1))
                        except Exception:
                            pass
                reviews_el = card.find('span', string=re.compile(r'Reviews|ratings', re.I))
                if reviews_el:
                    info['review_count'] = reviews_el.get_text(strip=True)

                # 圖片
                img_el = card.find('img')
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

                if info.get('name'):
                    results.append(info)

        return results

    def scrape_categories(self) -> List[Dict[str, Any]]:
        soup = self._get_page('https://www.walmart.com/')
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


