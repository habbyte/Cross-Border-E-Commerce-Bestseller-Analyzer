"""
eBay 爬蟲實作（BeautifulSoup）
僅用於教學與測試，請遵守 eBay 服務條款與 robots.txt。
"""

from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import requests
import random
import re

from .base_scraper import BaseScraper


class EbayScraper(BaseScraper):
    """eBay 爬蟲（以公開頁面為目標，容錯解析）"""

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
            self.session.headers['User-Agent'] = self.session.headers.get('User-Agent', '')
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
            url = f"https://www.ebay.com/sch/i.html?_nkw={term.replace(' ', '+')}"
            soup = self._get_page(url)
            if not soup:
                continue

            # 常見結果卡片容器
            candidates = soup.select("li.s-item")
            if not candidates:
                candidates = soup.select('[data-view*="mi:1686|iid:"]')

            for card in candidates[:20]:
                info: Dict[str, Any] = {}

                # 名稱
                title_el = card.select_one('h3.s-item__title') or card.select_one('.s-item__title')
                if title_el:
                    title_text = title_el.get_text(strip=True)
                    if title_text and title_text.lower() != 'shop on ebay':
                        info['name'] = title_text

                # 價格
                price_el = card.select_one('.s-item__price')
                if price_el:
                    price_text = price_el.get_text(strip=True)
                    m = re.search(r'\$[\d,.]+', price_text)
                    if m:
                        info['price'] = m.group()

                # 評分與評論
                rating_el = card.select_one('.x-star-rating span[aria-label]')
                if rating_el:
                    m = re.search(r'(\d+\.?\d*) out of 5', rating_el.get('aria-label', ''))
                    if m:
                        try:
                            info['rating'] = float(m.group(1))
                        except Exception:
                            pass
                reviews_el = card.select_one('.s-item__reviews-count span')
                if reviews_el:
                    info['review_count'] = reviews_el.get_text(strip=True)

                # 圖片
                img_el = card.select_one('img.s-item__image-img') or card.find('img')
                if img_el:
                    info['image_url'] = img_el.get('src') or img_el.get('data-src')

                # 連結
                link_el = card.select_one('a.s-item__link') or card.find('a', href=True)
                if link_el and link_el.get('href'):
                    info['product_url'] = link_el['href']

                # 描述
                if 'name' in info:
                    features = self.extract_product_features(info['name'])
                    info['description'] = self.create_description(info['name'], features)

                if info.get('name'):
                    results.append(info)

        return results

    def scrape_categories(self) -> List[Dict[str, Any]]:
        soup = self._get_page('https://www.ebay.com/')
        if not soup:
            return []

        cats: List[Dict[str, Any]] = []
        # 嘗試常見導覽與分類區塊
        selectors = [
            '#gh-top .gh-nav a',
            'nav[role="navigation"] a',
            'a[role="menuitem"]',
            '.hl-cat-nav__container a',
        ]
        for sel in selectors:
            for a in soup.select(sel):
                text = a.get_text(strip=True)
                href = a.get('href') or ''
                if not text or not href:
                    continue
                if len(text) < 2 or len(text) > 40:
                    continue
                if any(bad in text.lower() for bad in ['sign', 'daily deals', 'sell', 'help', 'watchlist', 'cart']):
                    continue
                cats.append({
                    'category_name': text,
                    'url': href if href.startswith('http') else f"https://www.ebay.com{href}"
                })

        # 去重後取前20
        seen = set()
        uniq = []
        for c in cats:
            if c['category_name'] not in seen:
                seen.add(c['category_name'])
                uniq.append(c)
        return uniq[:20]


