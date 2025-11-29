"""
增強版 Shopee 爬蟲（使用 Playwright）
繼承 EnhancedScraper 並實現 Shopee 特定的提取邏輯
"""

from typing import List, Dict, Any, Optional, Union, Tuple
from bs4 import BeautifulSoup
from pathlib import Path
import re
import json
import random
from .enhanced_scraper import EnhancedScraper


class EnhancedShopeeScraper(EnhancedScraper):
    """增強版 Shopee 爬蟲"""

    BASE_URL = "https://shopee.sg"

    def __init__(self, output_dir: str = "data/scraped_content", region_base_url: Optional[str] = None, 
                 shopee_email: Optional[str] = None, shopee_password: Optional[str] = None,
                 pause_on_verification: bool = False, **kwargs):
        """
        初始化增強版 Shopee 爬蟲

        Args:
            output_dir: 輸出目錄
            region_base_url: 地區站點，例如 https://shopee.tw
            shopee_email: Shopee 登入郵箱
            shopee_password: Shopee 登入密碼
            **kwargs: 傳遞給 EnhancedScraper 的其他參數
        """
        super().__init__(output_dir, **kwargs)
        if region_base_url:
            self.BASE_URL = region_base_url.rstrip("/")
        self.shopee_email = shopee_email
        self.shopee_password = shopee_password
        self.pause_on_verification = pause_on_verification
        self._is_logged_in = False  # 追蹤登入狀態
        self._login_attempts = 0    # 控制登入重試次數
        self._just_logged_in = False  # 標記剛完成登入

    def extract_product_info(self, product_element) -> Dict[str, Any]:
        """從 Shopee 搜索結果元素中提取商品資訊"""
        info: Dict[str, Any] = {}

        try:
            # 嘗試多種標題選擇器
            title_selectors = [
                '[data-sqe="name"]',
                '.Cve6sh',
                'h1', 'h2', 'h3',
                '[class*="product-name"]',
                '[class*="item-name"]',
                '[class*="title"]',
                'a[href*="/product/"]'
            ]
            for selector in title_selectors:
                title_el = product_element.select_one(selector)
                if title_el:
                    title_text = title_el.get_text(strip=True)
                    if title_text and len(title_text) > 3:
                        info["name"] = title_text
                        break
            
            # 如果還是沒找到，從所有文字中提取最長的一段作為名稱
            if "name" not in info:
                all_text = product_element.get_text(strip=True)
                # 嘗試找到最長的有意義的文字段
                lines = [line.strip() for line in all_text.split('\n') if line.strip() and len(line.strip()) > 10]
                if lines:
                    info["name"] = lines[0][:200]  # 限制長度

            # 價格提取 - 嘗試多種選擇器
            price_selectors = [
                ".currency-value",
                '[class*="price"]',
                '[class*="Price"]',
                'span[class*="currency"]',
                'div[class*="price"]'
            ]
            prices = []
            for selector in price_selectors:
                price_candidates = product_element.select(selector)
                if price_candidates:
                    for span in price_candidates[:3]:
                        price_text = span.get_text(strip=True)
                        match = re.search(r'([\d.,]+)', price_text)
                        if match:
                            try:
                                price_val = float(match.group(1).replace(",", ""))
                                if price_val > 0:
                                    prices.append(price_val)
                            except Exception:
                                pass
                    if prices:
                        break
            
            # 如果沒找到，從所有文字中提取價格
            if not prices:
                all_text = product_element.get_text()
                price_matches = re.findall(r'[\$S\$NT\$RM]?\s*([\d,]+\.?\d*)', all_text)
                for match in price_matches:
                    try:
                        price_val = float(match.replace(",", ""))
                        if price_val > 0:
                            prices.append(price_val)
                    except Exception:
                        pass
            
            if prices:
                try:
                    min_price = min(prices)
                    currency_symbol = self._detect_currency_symbol(product_element.get_text())
                    info["price"] = f"{currency_symbol}{min_price:,.2f}"
                except Exception:
                    pass

            # 銷量
            sold_text = product_element.get_text()
            sold_match = re.search(r'([\d,]+[KMBkkmb]?\+?)\s*sold', sold_text, re.I)
            if sold_match:
                info["sold"] = sold_match.group(1)

            # 評分
            rating_selectors = [
                '.rating__rating',
                '.shopee-rating-stars__light-val',
                '[class*="rating"]',
                '[class*="star"]'
            ]
            for selector in rating_selectors:
                rating_el = product_element.select_one(selector)
                if rating_el:
                    rating_match = re.search(r'(\d+\.?\d*)', rating_el.get_text(strip=True))
                    if rating_match:
                        try:
                            info["rating"] = float(rating_match.group(1))
                            break
                        except Exception:
                            pass

            # 評論數
            reviews_text = product_element.get_text()
            reviews_match = re.search(r'([\d,]+)\s*reviews?', reviews_text, re.I)
            if reviews_match:
                info["review_count"] = reviews_match.group(1)

            # 圖片
            img_selectors = ['img', '[class*="image"]', '[class*="img"]']
            for selector in img_selectors:
                img_el = product_element.select_one(selector)
                if img_el:
                    img_src = img_el.get("src") or img_el.get("data-src") or img_el.get("data-lazy-src")
                    if img_src and 'shopee' in img_src.lower():
                        info["image_url"] = img_src
                        break

            # 鏈接
            link_el = product_element.find("a", href=re.compile(r"/product/"))
            if link_el:
                href = link_el.get("href", "")
                if href:
                    if href.startswith("/"):
                        info["product_url"] = f"{self.BASE_URL}{href}"
                    elif href.startswith("http"):
                        info["product_url"] = href
                    else:
                        info["product_url"] = f"{self.BASE_URL}/{href}"

            # 描述
            if "name" in info:
                features = self.extract_product_features(info["name"])
                info["description"] = self.create_description(info["name"], features)

        except Exception as exc:
            print(f"Shopee 搜索結果解析錯誤: {exc}")
            import traceback
            traceback.print_exc()

        return info

    def scrape_product_detail(self, product_url: str, fetch_reviews: bool = True, max_reviews: int = 20) -> Dict[str, Any]:
        """爬取 Shopee 詳情頁完整資訊（包含評論）"""
        detail_info: Dict[str, Any] = {}

        try:
            soup = self.get_page(product_url, wait_selector='div[data-sqe="name"]', timeout=35000)
            if not soup:
                return detail_info

            # 提取商品 ID 和店鋪 ID（用於獲取評論）
            shop_id, item_id = self._extract_product_ids(product_url, soup)
            if shop_id and item_id:
                detail_info["shop_id"] = shop_id
                detail_info["item_id"] = item_id

            ld_product = self._extract_ld_json(soup)
            if ld_product:
                self._fill_detail_from_ld(detail_info, ld_product)

            name_el = soup.select_one('h1') or soup.select_one('div[data-sqe="name"]')
            if name_el and not detail_info.get("name"):
                detail_info["name"] = name_el.get_text(strip=True)

            breadcrumb_selectors = [
                'a[data-sqe="breadcrumb"]',
                '.breadcrumb__item-text',
                'nav[aria-label="breadcrumb"] a'
            ]
            breadcrumbs = self._collect_texts(soup, breadcrumb_selectors, limit=6)
            if breadcrumbs:
                detail_info["category_path"] = " > ".join(breadcrumbs)

            price_el = soup.select_one('div[data-sqe="price"]') or soup.select_one('.pmmxKx')
            if price_el and "price" not in detail_info:
                price_match = re.search(r'([\d.,]+)', price_el.get_text())
                if price_match:
                    symbol = self._detect_currency_symbol(price_el.get_text())
                    detail_info["price"] = f"{symbol}{price_match.group(1)}"

            # 提取更多商品信息
            # 店鋪名稱
            shop_selectors = [
                'a[data-sqe="shop-name"]',
                '.shop-name',
                '[class*="shop-name"]',
                'a[href*="/shop/"]'
            ]
            for selector in shop_selectors:
                shop_el = soup.select_one(selector)
                if shop_el:
                    shop_name = shop_el.get_text(strip=True)
                    if shop_name and len(shop_name) > 0:
                        detail_info["shop_name"] = shop_name
                        break

            # 已售數量
            sold_selectors = [
                '[data-sqe="sold"]',
                '.product-sold',
                '[class*="sold"]'
            ]
            for selector in sold_selectors:
                sold_el = soup.select_one(selector)
                if sold_el:
                    sold_text = sold_el.get_text(strip=True)
                    sold_match = re.search(r'([\d,]+[KMBkkmb]?\+?)', sold_text)
                    if sold_match:
                        detail_info["sold_count"] = sold_match.group(1)
                        break

            # 評分和評論數（詳情頁）
            rating_selectors = [
                '.rating__rating',
                '.shopee-rating-stars__light-val',
                '[class*="rating"]',
                '[data-sqe="rating"]'
            ]
            for selector in rating_selectors:
                rating_el = soup.select_one(selector)
                if rating_el:
                    rating_text = rating_el.get_text(strip=True)
                    rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                    if rating_match:
                        try:
                            detail_info["rating"] = float(rating_match.group(1))
                            break
                        except:
                            pass

            review_count_selectors = [
                '[data-sqe="review-count"]',
                '.review-count',
                '[class*="review"]'
            ]
            for selector in review_count_selectors:
                review_el = soup.select_one(selector)
                if review_el:
                    review_text = review_el.get_text(strip=True)
                    review_match = re.search(r'([\d,]+)', review_text)
                    if review_match:
                        detail_info["review_count"] = review_match.group(1)
                        break

            about_items = self._collect_texts(
                soup,
                ['.product-briefing__content p', '.product-briefing__content li', '.N19H5'],
                limit=10,
                min_length=15
            )
            if about_items:
                detail_info["about_this_item"] = about_items

            # 商品圖片（多張）
            img_selectors = [
                'img._3oDm6_',
                'img[data-sqe="image"]',
                '.product-briefing__images img',
                '[class*="product-image"] img'
            ]
            images = []
            for selector in img_selectors:
                img_elements = soup.select(selector)
                for img_el in img_elements[:5]:  # 最多取5張
                    img_src = img_el.get("src") or img_el.get("data-src") or img_el.get("data-lazy-src")
                    if img_src and 'shopee' in img_src.lower() and img_src not in images:
                        images.append(img_src)
                if images:
                    break
            
            if images:
                detail_info["image_url"] = images[0]  # 主圖
                if len(images) > 1:
                    detail_info["image_urls"] = images  # 所有圖片

            color_options = self._extract_variations(soup, variation_selector='button[aria-label*="color"], button[aria-label*="Colour"]')
            if color_options:
                detail_info["color_options"] = color_options

            size_options = self._extract_variations(
                soup,
                variation_selector='button[aria-label*="size"], button[aria-label*="Size"]',
                extract_price=False
            )
            if size_options:
                detail_info["size_options"] = [s["label"] for s in size_options if s.get("label")]

            # 爬取評論（如果提供了 shop_id 和 item_id）
            if fetch_reviews and shop_id and item_id:
                try:
                    reviews = self.scrape_product_reviews(shop_id, item_id, max_reviews=max_reviews)
                    if reviews:
                        detail_info["reviews"] = reviews
                        detail_info["review_count_actual"] = len(reviews)
                        print(f"成功爬取 {len(reviews)} 條評論")
                except Exception as review_exc:
                    print(f"爬取評論時發生錯誤: {review_exc}")

        except Exception as exc:
            print(f"爬取 Shopee 詳情頁失敗: {exc}")
            import traceback
            traceback.print_exc()

        return detail_info

    def _login_to_shopee(self) -> bool:
        """自動登入 Shopee"""
        if not self.shopee_email or not self.shopee_password:
            print("未提供 Shopee 登入憑證，跳過自動登入")
            return False
        
        if self._is_logged_in:
            print("已經登入，跳過登入流程")
            return True
        
        try:
            print(f"正在嘗試登入 Shopee ({self.BASE_URL})...")
            
            # 確保瀏覽器已設置
            if self.page is None:
                self._setup_browser()
            
            # 訪問登入頁面
            login_url = f"{self.BASE_URL}/buyer/login"
            print(f"訪問登入頁面: {login_url}")
            self.page.goto(login_url, wait_until='domcontentloaded', timeout=30000)
            
            # 模擬人類行為（在登入前）
            self._simulate_human_behavior()
            self.add_delay(2, 4)  # 增加延遲，模擬閱讀頁面
            
            # 等待登入表單加載
            try:
                # 嘗試多種登入表單選擇器
                email_selectors = [
                    'input[type="email"]',
                    'input[name="loginKey"]',
                    'input[placeholder*="email"]',
                    'input[placeholder*="Email"]',
                    'input[placeholder*="電子郵件"]',
                    'input[id*="email"]',
                    'input[id*="login"]'
                ]
                
                password_selectors = [
                    'input[type="password"]',
                    'input[name="password"]',
                    'input[placeholder*="password"]',
                    'input[placeholder*="Password"]',
                    'input[placeholder*="密碼"]',
                    'input[id*="password"]'
                ]
                
                email_input = None
                password_input = None
                
                for selector in email_selectors:
                    try:
                        email_input = self.page.wait_for_selector(selector, timeout=5000, state='visible')
                        if email_input:
                            print(f"找到郵箱輸入框: {selector}")
                            break
                    except:
                        continue
                
                for selector in password_selectors:
                    try:
                        password_input = self.page.wait_for_selector(selector, timeout=5000, state='visible')
                        if password_input:
                            print(f"找到密碼輸入框: {selector}")
                            break
                    except:
                        continue
                
                if not email_input or not password_input:
                    print("無法找到登入表單，可能需要手動登入")
                    return False
                
                # 輸入郵箱和密碼（模擬真實打字速度）
                print("正在輸入登入資訊...")
                
                # 模擬真實打字（逐字符輸入）
                email_input.click()
                self.add_delay(0.3, 0.5)
                for char in self.shopee_email:
                    email_input.type(char, delay=random.uniform(50, 150))  # 50-150ms 每個字符
                self.add_delay(0.5, 1.0)
                
                # 切換到密碼框
                password_input.click()
                self.add_delay(0.3, 0.5)
                
                # 模擬真實打字（逐字符輸入）
                for char in self.shopee_password:
                    password_input.type(char, delay=random.uniform(50, 150))
                self.add_delay(1, 2)
                
                # 模擬人類行為（輸入完成後的短暫停頓）
                self._simulate_human_behavior()
                
                # 等待頁面完全加載
                self.page.wait_for_load_state('domcontentloaded', timeout=10000)
                self.add_delay(1, 2)
                
                # 尋找並點擊登入按鈕
                login_button_selectors = [
                    'button[type="submit"]',
                    'button:has-text("登入")',
                    'button:has-text("Login")',
                    'button:has-text("登錄")',
                    'button.login-button',
                    'button[class*="login"]',
                    'button[class*="Login"]',
                    'form button[type="submit"]',
                    'form button',
                    'button.wyhvVD',  # Shopee 可能的按鈕類名
                    'button._1ruZ5a',  # Shopee 可能的按鈕類名
                ]
                
                login_button = None
                for selector in login_button_selectors:
                    try:
                        # 先嘗試等待元素出現
                        try:
                            self.page.wait_for_selector(selector, timeout=3000, state='visible')
                        except:
                            pass
                        
                        login_button = self.page.query_selector(selector)
                        if login_button:
                            # 檢查按鈕是否可見和可點擊
                            is_visible = login_button.is_visible()
                            if is_visible:
                                print(f"找到登入按鈕: {selector}")
                                break
                    except Exception as e:
                        continue
                
                # 點擊登入按鈕並等待導航
                if not login_button:
                    # 嘗試按 Enter 鍵
                    print("未找到登入按鈕，嘗試按 Enter 鍵...")
                    try:
                        password_input.press('Enter')
                        self.add_delay(2, 3)
                    except Exception as e:
                        print(f"按 Enter 鍵失敗: {e}")
                        return False
                else:
                    # 使用 wait_for_navigation 來處理頁面跳轉
                    print("點擊登入按鈕...")
                    try:
                        # 等待導航完成（最多等待 15 秒）
                        with self.page.expect_navigation(timeout=15000, wait_until='domcontentloaded'):
                            login_button.click()
                        print("頁面導航完成")
                    except Exception as nav_error:
                        # 如果沒有發生導航，繼續等待
                        print(f"等待導航時發生錯誤（可能已跳轉）: {nav_error}")
                        self.add_delay(2, 3)
                
                # 等待登入完成（檢查是否跳轉或出現錯誤）
                print("等待登入完成...")
                self.add_delay(2, 4)
                
                # 等待頁面穩定
                try:
                    self.page.wait_for_load_state('networkidle', timeout=10000)
                except:
                    pass  # 忽略超時，繼續檢查
                
                # 檢查當前 URL 是否已離開登入頁面
                current_url = self.page.url
                print(f"當前 URL: {current_url}")
                
                if '/buyer/login' not in current_url and '/verify' not in current_url:
                    print(f"登入成功！當前 URL: {current_url}")
                    self._is_logged_in = True
                    
                    # 保存 cookies
                    self.save_cookies()
                    return True
                elif '/verify' in current_url:
                    print("檢測到驗證頁面，等待驗證完成...")
                    
                    if self._prompt_manual_verification("登入過程中觸發 Shopee 安全驗證，請在視窗中完成驗證。"):
                        try:
                            self.page.wait_for_load_state('domcontentloaded', timeout=20000)
                            self.page.wait_for_load_state('networkidle', timeout=20000)
                            current_url = self.page.url
                        except Exception as wait_exc:
                            print(f"等待驗證完成時發生錯誤: {wait_exc}")
                    
                    # 等待驗證完成（可能需要更長時間）
                    max_wait = 15  # 最多等待 15 秒
                    waited = 0
                    while waited < max_wait:
                        self.add_delay(2, 3)
                        waited += 3
                        current_url = self.page.url
                        print(f"等待驗證中... ({waited}/{max_wait}秒) 當前 URL: {current_url[:100]}...")
                        
                        # 如果離開了驗證頁面和登入頁面，說明驗證通過
                        if '/verify' not in current_url and '/buyer/login' not in current_url:
                            print(f"驗證通過，登入成功！當前 URL: {current_url}")
                            self._is_logged_in = True
                            self.save_cookies()
                            return True
                        
                        # 如果回到登入頁面，說明驗證失敗
                        if '/buyer/login' in current_url:
                            print("驗證失敗，回到登入頁面")
                            return False
                    
                    # 如果超時仍在驗證頁面，嘗試繼續（可能驗證需要手動處理）
                    print("驗證等待超時，當前仍在驗證頁面。")
                    if self._prompt_manual_verification("仍在驗證頁面，請確認是否已通過驗證（可重試）。"):
                        try:
                            self.page.wait_for_load_state('domcontentloaded', timeout=20000)
                            self.page.wait_for_load_state('networkidle', timeout=20000)
                            current_url = self.page.url
                        except Exception:
                            pass
                        if '/verify' not in current_url:
                            print(f"驗證通過，登入成功！當前 URL: {current_url}")
                            self._is_logged_in = True
                            self.save_cookies()
                            return True
                    
                    print("仍未通過驗證，登入流程中止。")
                    return False
                else:
                    # 檢查是否有錯誤訊息
                    try:
                        error_selectors = [
                            '.error-message',
                            '[class*="error"]',
                            '[class*="Error"]',
                            '.alert-danger',
                            '[role="alert"]'
                        ]
                        for selector in error_selectors:
                            error_el = self.page.query_selector(selector)
                            if error_el:
                                error_text = error_el.inner_text()
                                if error_text and len(error_text.strip()) > 0:
                                    print(f"登入失敗: {error_text}")
                                    return False
                    except Exception as e:
                        print(f"檢查錯誤訊息時發生問題: {e}")
                    
                    print("登入可能失敗，仍在登入頁面")
                    return False
                    
            except Exception as e:
                print(f"登入過程中發生錯誤: {e}")
                import traceback
                traceback.print_exc()
                return False
                
        except Exception as e:
            print(f"登入失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _check_and_login_if_needed(self, soup: BeautifulSoup) -> bool:
        """檢查是否需要登入，如果需要則執行登入"""
        if self._is_logged_in:
            return True
        
        current_url = ""
        if self.page:
            current_url = (self.page.url or "").lower()
            print(f"目前頁面 URL: {self.page.url}")
        
        # 優先檢查是否有有效的 cookies（避免重複登入）
        if self.cookies_file and Path(self.cookies_file).exists():
            try:
                with open(self.cookies_file, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                    # 檢查是否有有效的 session cookies
                    has_valid_session = any(
                        'SPC_' in cookie.get('name', '') or 
                        'shopee' in cookie.get('name', '').lower()
                        for cookie in cookies
                    )
                    if has_valid_session:
                        print("檢測到已保存的 cookies，嘗試使用...")
                        # 重新加載 cookies（修復格式）
                        if self.context:
                            try:
                                # 修復 cookies 格式
                                fixed_cookies = []
                                for cookie in cookies:
                                    fixed_cookie = dict(cookie)
                                    if 'sameSite' in fixed_cookie:
                                        same_site = fixed_cookie['sameSite']
                                        if same_site not in ['Strict', 'Lax', 'None']:
                                            if same_site in ['strict', 'STRICT']:
                                                fixed_cookie['sameSite'] = 'Strict'
                                            elif same_site in ['lax', 'LAX']:
                                                fixed_cookie['sameSite'] = 'Lax'
                                            elif same_site in ['none', 'NONE']:
                                                fixed_cookie['sameSite'] = 'None'
                                            else:
                                                fixed_cookie['sameSite'] = 'Lax'
                                    else:
                                        fixed_cookie['sameSite'] = 'Lax'
                                    
                                    if 'domain' in fixed_cookie and fixed_cookie['domain']:
                                        fixed_cookies.append(fixed_cookie)
                                
                                if fixed_cookies:
                                    self.context.add_cookies(fixed_cookies)
                                    print(f"已重新加載 {len(fixed_cookies)} 個 cookies")
                            except Exception as e:
                                print(f"重新加載 cookies 失敗: {e}")
                        # 給一個機會，如果還是被重定向到登入頁，再執行登入
                        self.add_delay(1, 2)
            except Exception as e:
                print(f"檢查 cookies 時發生錯誤: {e}")
        
        # 檢查 URL 是否指向登入或驗證頁面
        if current_url:
            if '/buyer/login' in current_url:
                print("根據 URL 判斷目前在登入頁面，嘗試自動登入...")
                return self._attempt_login()
            if '/verify' in current_url or 'traffic/error' in current_url:
                print("根據 URL 判斷目前在驗證頁面。")
                if self._prompt_manual_verification("偵測到 Shopee 驗證頁面，請手動完成驗證後繼續。"):
                    print("已等待使用者完成驗證，嘗試重載頁面...")
                    try:
                        if self.page:
                            self.page.reload(wait_until='domcontentloaded', timeout=30000)
                            self.page.wait_for_load_state('networkidle', timeout=20000)
                        return True
                    except Exception as reload_exc:
                        print(f"驗證後重載頁面失敗: {reload_exc}")
                # 驗證頁有時候需要人工處理，這裡再嘗試登入流程
                return self._attempt_login()
        
        # 檢查頁面內容是否顯示登入提示
        title = soup.find('title')
        if title:
            title_text = title.get_text(strip=True).lower()
            if 'login' in title_text or '登入' in title_text or '登錄' in title_text:
                print("檢測到登入頁面標題，嘗試自動登入...")
                return self._attempt_login()
        
        # 檢查是否存在登入表單元素
        login_form_indicators = [
            soup.select_one('input[name="loginKey"]'),
            soup.select_one('input[name="loginid"]'),
            soup.select_one('input[id*="login"]'),
            soup.select_one('input[type="email"]'),
            soup.select_one('input[type="password"]'),
            soup.find('button', string=re.compile('登入|Login|登錄', re.IGNORECASE))
        ]
        if any(login_form_indicators):
            print("檢測到登入表單元素，嘗試自動登入...")
            return self._attempt_login()
        
        # 檢查頁面是否顯示「立即登入」等文字
        page_text_snippet = soup.get_text(" ", strip=True)[:500].lower()
        login_keywords = ['立即登入', 'login to', '登入以繼續', 'login now', '請登入']
        if any(keyword in page_text_snippet for keyword in login_keywords):
            print("檢測到登入提示文字，嘗試自動登入...")
            return self._attempt_login()
        
        return True
    
    def _attempt_login(self) -> bool:
        """封裝登入流程，包含重試與限制"""
        if not self.shopee_email or not self.shopee_password:
            print("尚未配置 Shopee 帳號密碼，無法自動登入")
            return False
        
        if self._login_attempts >= 3:
            print("登入嘗試已達上限（3 次），請手動處理或稍後再試")
            return False
        
        self._login_attempts += 1
        print(f"開始第 {self._login_attempts} 次登入嘗試...")
        self._just_logged_in = False
        success = self._login_to_shopee()
        if success:
            print("登入流程完成")
            self._just_logged_in = True
        else:
            print("登入流程失敗")
        return success
    
    def _prompt_manual_verification(self, reason: str) -> bool:
        """提示使用者手動處理驗證"""
        if not self.pause_on_verification:
            return False
        
        print("\n=== Shopee 安全驗證提醒 ===")
        print(reason)
        
        if self.headless:
            print("目前為無頭模式，無法手動操作。請使用 --no-headless 或取消 pause-on-verify。")
            return False
        
        print("請在已開啟的瀏覽器視窗中完成驗證。")
        print("完成後按 Enter 繼續，或輸入 skip 取消本次手動驗證。")
        
        try:
            user_input = input("操作完成後按 Enter 繼續（skip 取消）: ").strip().lower()
        except EOFError:
            print("無法讀取輸入，跳過手動驗證。")
            return False
        
        if user_input == 'skip':
            print("使用者選擇跳過手動驗證。")
            return False
        
        print("收到確認，繼續執行爬蟲流程。")
        self.add_delay(2, 3)
        return True
    
    def _handle_verification_page(self, current_url: str) -> bool:
        """覆寫基礎方法，在遇到驗證頁面時提供人工介入機會"""
        if not self.pause_on_verification:
            return False
        
        message = f"目前頁面被重定向到驗證頁 ({current_url})，請在瀏覽器中完成驗證。"
        if self._prompt_manual_verification(message):
            try:
                if self.page:
                    self.page.wait_for_load_state('domcontentloaded', timeout=30000)
                    self.page.wait_for_load_state('networkidle', timeout=30000)
                return True
            except Exception as e:
                print(f"等待手動驗證完成時發生錯誤: {e}")
        return False
    
    def scrape_products(self, search_terms: List[str], fetch_details: bool = True) -> List[Dict[str, Any]]:
        """爬取 Shopee 商品資訊"""
        results: List[Dict[str, Any]] = []

        try:
            # 確保瀏覽器已初始化
            if self.page is None:
                self._setup_browser()
            
            # 策略：先訪問首頁建立會話，降低被檢測概率
            # 模擬真實用戶行為：訪問首頁 → 瀏覽 → 等待 → 再搜索
            if not self._is_logged_in:
                print("訪問首頁建立會話...")
                try:
                    if self.page:
                        # 1. 訪問首頁
                        self.page.goto(self.BASE_URL, wait_until='domcontentloaded', timeout=30000)
                        print("首頁已加載，模擬瀏覽行為...")
                        
                        # 2. 模擬真實用戶行為（滾動、鼠標移動等）
                        self._simulate_human_behavior()
                        
                        # 3. 等待更長時間，模擬閱讀首頁內容
                        wait_time = random.uniform(5, 10)
                        print(f"模擬閱讀首頁內容，等待 {wait_time:.1f} 秒...")
                        self.add_delay(wait_time, wait_time + 2)
                        
                        # 4. 再次模擬行為，讓會話更自然
                        self._simulate_human_behavior()
                        
                        print("首頁訪問完成，會話已建立")
                    else:
                        print("警告: 瀏覽器頁面未初始化")
                except Exception as e:
                    print(f"訪問首頁時發生錯誤（繼續執行）: {e}")
            
            for term in search_terms:
                url = f"{self.BASE_URL}/search?keyword={term.replace(' ', '%20')}"
                print(f"正在訪問 Shopee 搜索頁面: {url}")
                
                # 增加延遲，模擬真實用戶思考時間（搜索前會思考一下）
                wait_time = random.uniform(5, 10)
                print(f"模擬用戶思考時間，等待 {wait_time:.1f} 秒...")
                self.add_delay(wait_time, wait_time + 2)
                
                # 嘗試多種選擇器，Shopee 可能使用不同的結構
                soup = self.get_page(url, wait_selector=None, timeout=45000)
                if not soup:
                    print(f"警告: 無法獲取頁面內容，URL: {url}")
                    continue
                
                # 檢查是否需要登入
                if not self._check_and_login_if_needed(soup):
                    print("登入失敗，無法繼續爬取")
                    continue
                
                # 如果剛完成登入，重新獲取頁面
                if self._just_logged_in or self._is_logged_in:
                    current_url = self.page.url if self.page else ''
                    if self._just_logged_in:
                        print("剛完成登入，重新訪問搜索頁面...")
                    if '/buyer/login' in current_url or '/verify' in current_url or self._just_logged_in:
                        # 先訪問首頁確保登入狀態刷新
                        try:
                            self.page.goto(self.BASE_URL, wait_until='domcontentloaded', timeout=30000)
                            self.add_delay(2, 3)
                        except Exception as e:
                            print(f"登入後訪問首頁時發生錯誤: {e}")
                        # 再訪問搜索頁面
                        soup = self.get_page(url, wait_selector=None, timeout=45000)
                        self._just_logged_in = False
                        if not soup:
                            continue
                
                # 檢查頁面標題，確認是否成功加載
                title = soup.find('title')
                if title:
                    title_text = title.get_text(strip=True)
                    print(f"頁面標題: {title_text}")
                    if 'captcha' in title_text.lower() or 'verify' in title_text.lower():
                        print("檢測到驗證頁面，跳過此搜索")
                        continue
                
                # 嘗試多種商品容器選擇器
                containers = []
                selectors_to_try = [
                    '.shopee-search-item-result__item',
                    '[data-sqe="item"]',
                    'div[class*="shopee-search-item-result"]',
                    'div[class*="product-item"]',
                    'a[href*="/product/"]',
                    'div[class*="item-card"]',
                    'div[data-testid*="product"]',
                    'div[class*="search-result"]'
                ]
                
                for selector in selectors_to_try:
                    containers = soup.select(selector)
                    if containers:
                        print(f"使用選擇器 '{selector}' 找到 {len(containers)} 個候選商品")
                        break
                
                # 如果還是沒找到，嘗試從所有包含商品鏈接的元素中提取
                if not containers:
                    print("未找到標準商品容器，嘗試從鏈接中提取...")
                    product_links = soup.select('a[href*="/product/"]')
                    print(f"找到 {len(product_links)} 個商品鏈接")
                    # 將鏈接的父元素作為容器
                    for link in product_links[:20]:
                        parent = link.find_parent(['div', 'article', 'section'])
                        if parent:
                            containers.append(parent)
                
                # 如果還是沒有，嘗試解析 JSON 數據（Shopee 可能使用 API）
                if not containers:
                    print("嘗試從頁面 JSON 數據中提取商品...")
                    json_products = self._extract_products_from_json(soup)
                    if json_products:
                        print(f"從 JSON 數據中提取到 {len(json_products)} 個商品")
                        results.extend(json_products)
                        continue

                print(f"Shopee 找到 {len(containers)} 個候選商品容器")

                # 調試：檢查第一個容器的內容
                if containers and len(containers) > 0:
                    first_container_text = containers[0].get_text(strip=True)[:200]
                    print(f"第一個容器預覽: {first_container_text}...")

                for i, card in enumerate(containers[:10]):
                    print(f"處理商品 {i+1}/{min(10, len(containers))}")
                    info = self.extract_product_info(card)
                    
                    # 如果沒有提取到名稱，嘗試更寬鬆的提取
                    if not info.get("name"):
                        # 嘗試從鏈接中提取
                        link_el = card.find("a", href=re.compile(r"/product/"))
                        if link_el:
                            link_text = link_el.get_text(strip=True)
                            if link_text and len(link_text) > 5:
                                info["name"] = link_text
                                # 從鏈接獲取 URL
                                href = link_el.get("href", "")
                                if href:
                                    if href.startswith("/"):
                                        info["product_url"] = f"{self.BASE_URL}{href}"
                                    else:
                                        info["product_url"] = href
                    
                    if not info.get("name"):
                        print(f"  跳過商品 {i+1}：無法提取商品名稱")
                        continue

                    print(f"  商品名稱: {info.get('name', 'N/A')[:50]}...")

                    if fetch_details and info.get("product_url"):
                        try:
                            # 獲取商品詳情（包含評論）
                            detail_info = self.scrape_product_detail(
                                info["product_url"], 
                                fetch_reviews=True, 
                                max_reviews=10  # 每個商品最多獲取 10 條評論
                            )
                            info.update(detail_info)
                            self.add_delay(2, 4)  # 增加延遲，因為需要獲取評論
                        except Exception as detail_exc:
                            print(f"  Shopee 詳情抓取失敗: {detail_exc}")

                    results.append(info)
                    print(f"  已添加商品，當前總數: {len(results)}")

                self.add_delay(2, 4)
        finally:
            self.save_cookies()
            if self.enable_request_monitoring:
                self.save_request_logs()

        print(f"Shopee 爬取完成，共獲取 {len(results)} 個商品")
        return results

    def scrape_categories(self) -> List[Dict[str, Any]]:
        """爬取 Shopee 首頁分類"""
        try:
            print(f"正在訪問 Shopee 首頁: {self.BASE_URL}")
            soup = self.get_page(self.BASE_URL, wait_selector=None, timeout=30000)
            if not soup:
                print("無法獲取 Shopee 首頁")
                return []

            categories: List[Dict[str, Any]] = []
            selectors = [
                'a[href*="search?category"]',
                'a[href*="/category/"]',
                'a[data-sqe="category"]',
                '.home-category-list a',
                '.Wf72uQ a',
                'nav a[href*="category"]',
                '[class*="category"] a',
                '[class*="Category"] a'
            ]
            
            for selector in selectors:
                links = soup.select(selector)
                print(f"選擇器 '{selector}' 找到 {len(links)} 個鏈接")
                for a_tag in links:
                    text = a_tag.get_text(strip=True)
                    href = a_tag.get("href")
                    if not text or not href:
                        continue
                    if len(text) < 2 or len(text) > 50:
                        continue
                    if any(bad in text.lower() for bad in ["help", "seller", "sign", "login", "cart", "register", "download"]):
                        continue
                    url = href if href.startswith("http") else f"{self.BASE_URL}{href}"
                    categories.append({"category_name": text, "url": url})
                
                if categories:
                    print(f"使用選擇器 '{selector}' 找到 {len(categories)} 個分類")
                    break

            # 如果沒找到，嘗試從導航菜單中提取
            if not categories:
                print("嘗試從導航菜單提取分類...")
                nav_links = soup.select('nav a, header a, [role="navigation"] a')
                for link in nav_links:
                    text = link.get_text(strip=True)
                    href = link.get("href", "")
                    if text and href and ('category' in href.lower() or 'search' in href.lower()):
                        if len(text) > 2 and len(text) < 50:
                            url = href if href.startswith("http") else f"{self.BASE_URL}{href}"
                            categories.append({"category_name": text, "url": url})

            # 去重
            unique: List[Dict[str, Any]] = []
            seen = set()
            for cat in categories:
                if cat["category_name"] not in seen:
                    seen.add(cat["category_name"])
                    unique.append(cat)

            print(f"Shopee 找到 {len(unique)} 個唯一分類")
            return unique[:20]
        except Exception as e:
            print(f"爬取 Shopee 分類時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            self.save_cookies()

    # ----------------------------
    # 輔助方法
    # ----------------------------
    def _extract_ld_json(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """解析頁面中的 LD+JSON Product 資料"""
        for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
            try:
                data = json.loads(script.string or "{}")
            except json.JSONDecodeError:
                continue

            if isinstance(data, list):
                for item in data:
                    product = self._extract_product_from_ld_item(item)
                    if product:
                        return product
            else:
                product = self._extract_product_from_ld_item(data)
                if product:
                    return product
        return None

    def _extract_product_from_ld_item(self, item: Union[Dict[str, Any], None]) -> Optional[Dict[str, Any]]:
        if not isinstance(item, dict):
            return None
        if item.get("@type") == "Product":
            return item
        graph = item.get("@graph")
        if isinstance(graph, list):
            for node in graph:
                if isinstance(node, dict) and node.get("@type") == "Product":
                    return node
        return None

    def _fill_detail_from_ld(self, target: Dict[str, Any], ld_product: Dict[str, Any]):
        """將 LD+JSON 的資訊填入 detail"""
        if ld_product.get("name"):
            target["name"] = ld_product["name"]
        if ld_product.get("description"):
            target["description"] = ld_product["description"]
        image = ld_product.get("image")
        if isinstance(image, list) and image:
            target["image_url"] = image[0]
        elif isinstance(image, str):
            target["image_url"] = image

        offers = ld_product.get("offers") or {}
        if isinstance(offers, dict):
            price = offers.get("price") or offers.get("lowPrice")
            currency = offers.get("priceCurrency", "")
            if price:
                target["price"] = f"{currency} {price}".strip()

        rating = ld_product.get("aggregateRating")
        if isinstance(rating, dict):
            try:
                target["rating"] = float(rating.get("ratingValue"))
            except Exception:
                pass
            review_count = rating.get("reviewCount") or rating.get("ratingCount")
            if review_count:
                target["review_count"] = str(review_count)

    def _collect_texts(self, soup: BeautifulSoup, selectors: List[str], limit: int = 5, min_length: int = 0) -> List[str]:
        """根據多個選擇器收集文字"""
        results: List[str] = []
        for selector in selectors:
            for node in soup.select(selector):
                text = node.get_text(strip=True)
                if text and len(text) >= min_length:
                    results.append(text)
                    if len(results) >= limit:
                        return results
            if results:
                return results
        return results

    def _extract_variations(self, soup: BeautifulSoup, variation_selector: str, extract_price: bool = True) -> List[Dict[str, Any]]:
        """抽取變體選項（顏色或尺寸）"""
        variations: List[Dict[str, Any]] = []
        for button in soup.select(variation_selector):
            aria_label = button.get("aria-label") or button.get_text(strip=True)
            if not aria_label:
                continue
            info: Dict[str, Any] = {"label": aria_label}
            if extract_price:
                price_match = re.search(r'([\d.,]+)', aria_label)
                if price_match:
                    symbol = self._detect_currency_symbol(aria_label)
                    info["color_price"] = f"{symbol}{price_match.group(1)}"
            variations.append(info)
        return variations

    def _extract_product_ids(self, product_url: str, soup: Optional[BeautifulSoup] = None) -> Tuple[Optional[int], Optional[int]]:
        """從商品 URL 或頁面中提取 shop_id 和 item_id"""
        shop_id = None
        item_id = None
        
        try:
            # 方法1: 從 URL 中提取（格式: /product/123456/78901234）
            url_match = re.search(r'/product/(\d+)/(\d+)', product_url)
            if url_match:
                shop_id = int(url_match.group(1))
                item_id = int(url_match.group(2))
                return shop_id, item_id
            
            # 方法2: 從頁面 JSON 數據中提取
            if soup:
                # 查找包含商品 ID 的 script 標籤
                scripts = soup.find_all('script', type='application/json')
                scripts.extend(soup.find_all('script', string=re.compile(r'item_id|shop_id')))
                
                for script in scripts:
                    script_text = script.string or script.get_text()
                    if not script_text:
                        continue
                    
                    # 嘗試提取 item_id
                    item_match = re.search(r'"item_id"\s*:\s*(\d+)', script_text)
                    if item_match and not item_id:
                        item_id = int(item_match.group(1))
                    
                    # 嘗試提取 shop_id
                    shop_match = re.search(r'"shop_id"\s*:\s*(\d+)', script_text)
                    if shop_match and not shop_id:
                        shop_id = int(shop_match.group(1))
                    
                    if shop_id and item_id:
                        break
                
                # 方法3: 從頁面文本中搜索
                if not shop_id or not item_id:
                    page_text = str(soup)
                    if not item_id:
                        item_match = re.search(r'item_id["\']?\s*[:=]\s*(\d+)', page_text)
                        if item_match:
                            item_id = int(item_match.group(1))
                    if not shop_id:
                        shop_match = re.search(r'shop_id["\']?\s*[:=]\s*(\d+)', page_text)
                        if shop_match:
                            shop_id = int(shop_match.group(1))
        
        except Exception as e:
            print(f"提取商品 ID 時發生錯誤: {e}")
        
        return shop_id, item_id
    
    def scrape_product_reviews(self, shop_id: int, item_id: int, max_reviews: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """爬取商品評論（使用 Shopee API）"""
        reviews: List[Dict[str, Any]] = []
        
        try:
            if not self.page:
                self._setup_browser()
            
            # Shopee 評論 API 端點
            # 注意：實際的 API 端點可能需要根據 Shopee 的更新進行調整
            api_url = f"{self.BASE_URL}/api/v2/item/get_ratings"
            
            # 構建請求參數
            params = {
                'itemid': item_id,
                'shopid': shop_id,
                'offset': offset,
                'limit': min(max_reviews, 59),  # Shopee 通常限制每頁最多 59 條
                'filter': 0,  # 0=全部, 1=有圖, 2=有影片
                'flag': 1,
                'type': 0  # 0=全部, 1=好評, 2=中評, 3=差評
            }
            
            print(f"正在獲取評論: shop_id={shop_id}, item_id={item_id}")
            
            # 使用 Playwright 發送請求
            response = self.page.request.get(api_url, params=params)
            
            if response.status == 200:
                try:
                    data = response.json()
                    
                    # 解析評論數據（根據 Shopee API 響應結構）
                    if 'data' in data and 'ratings' in data['data']:
                        ratings = data['data']['ratings']
                        for rating in ratings[:max_reviews]:
                            review = {
                                'rating': rating.get('rating_star', 0),
                                'comment': rating.get('comment', ''),
                                'username': rating.get('user_name', ''),
                                'time': rating.get('ctime', 0),
                                'images': rating.get('images', []),
                                'videos': rating.get('videos', []),
                                'variation': rating.get('product_items', [{}])[0].get('name', '') if rating.get('product_items') else ''
                            }
                            reviews.append(review)
                    elif 'ratings' in data:
                        # 另一種可能的響應結構
                        for rating in data['ratings'][:max_reviews]:
                            review = {
                                'rating': rating.get('rating_star', 0),
                                'comment': rating.get('comment', ''),
                                'username': rating.get('user_name', ''),
                                'time': rating.get('ctime', 0),
                                'images': rating.get('images', []),
                                'videos': rating.get('videos', [])
                            }
                            reviews.append(review)
                    
                    print(f"成功解析 {len(reviews)} 條評論")
                    
                except json.JSONDecodeError as e:
                    print(f"解析評論 JSON 失敗: {e}")
                    # 嘗試從 HTML 中提取評論
                    reviews = self._extract_reviews_from_html(shop_id, item_id, max_reviews)
            else:
                print(f"API 請求失敗，狀態碼: {response.status}")
                # 回退到從 HTML 提取
                reviews = self._extract_reviews_from_html(shop_id, item_id, max_reviews)
        
        except Exception as e:
            print(f"爬取評論時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            # 嘗試從 HTML 提取
            try:
                reviews = self._extract_reviews_from_html(shop_id, item_id, max_reviews)
            except:
                pass
        
        return reviews
    
    def _extract_reviews_from_html(self, shop_id: int, item_id: int, max_reviews: int = 20) -> List[Dict[str, Any]]:
        """從商品詳情頁的 HTML 中提取評論（備用方法）"""
        reviews: List[Dict[str, Any]] = []
        
        try:
            # 訪問評論頁面
            review_url = f"{self.BASE_URL}/product/{shop_id}/{item_id}/ratings"
            soup = self.get_page(review_url, wait_selector=None, timeout=30000)
            
            if not soup:
                return reviews
            
            # 查找評論容器
            review_selectors = [
                '.shopee-product-rating',
                '[data-sqe="review"]',
                '.review-item',
                '[class*="review"]',
                '[class*="rating-item"]'
            ]
            
            review_elements = []
            for selector in review_selectors:
                review_elements = soup.select(selector)
                if review_elements:
                    break
            
            for review_el in review_elements[:max_reviews]:
                try:
                    review = {}
                    
                    # 評分
                    rating_el = review_el.select_one('[class*="rating"], [class*="star"]')
                    if rating_el:
                        rating_text = rating_el.get_text(strip=True)
                        rating_match = re.search(r'(\d+)', rating_text)
                        if rating_match:
                            review['rating'] = int(rating_match.group(1))
                    
                    # 評論內容
                    comment_el = review_el.select_one('[class*="comment"], [class*="content"], p')
                    if comment_el:
                        review['comment'] = comment_el.get_text(strip=True)
                    
                    # 用戶名
                    username_el = review_el.select_one('[class*="user"], [class*="name"], a')
                    if username_el:
                        review['username'] = username_el.get_text(strip=True)
                    
                    # 時間
                    time_el = review_el.select_one('[class*="time"], [class*="date"]')
                    if time_el:
                        review['time_text'] = time_el.get_text(strip=True)
                    
                    # 圖片
                    images = []
                    for img in review_el.select('img'):
                        img_src = img.get('src') or img.get('data-src')
                        if img_src and 'shopee' in img_src.lower():
                            images.append(img_src)
                    if images:
                        review['images'] = images
                    
                    if review:
                        reviews.append(review)
                
                except Exception as e:
                    continue
        
        except Exception as e:
            print(f"從 HTML 提取評論時發生錯誤: {e}")
        
        return reviews
    
    def _detect_currency_symbol(self, text: Optional[str]) -> str:
        """簡單檢測貨幣符號（默認 SGD）"""
        if not text:
            return "S$"
        if "RM" in text:
            return "RM"
        if "NT$" in text:
            return "NT$"
        if "฿" in text:
            return "฿"
        if "$" in text:
            return "$"
        return "S$"
    
    def _extract_products_from_json(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """從頁面中的 JSON 數據提取商品（Shopee 可能使用 API 加載）"""
        products = []
        
        try:
            # 查找所有 script 標籤中的 JSON 數據
            scripts = soup.find_all('script', type='application/json')
            scripts.extend(soup.find_all('script', string=re.compile(r'window\._SSR_HYDRATED_DATA')))
            scripts.extend(soup.find_all('script', string=re.compile(r'__APP_INITIAL_STATE__')))
            
            for script in scripts:
                try:
                    script_text = script.string or script.get_text()
                    if not script_text:
                        continue
                    
                    # 嘗試提取 JSON 對象
                    json_match = re.search(r'\{.*\}', script_text, re.DOTALL)
                    if json_match:
                        data = json.loads(json_match.group())
                        # 遞歸搜索商品數據
                        products.extend(self._find_products_in_dict(data))
                except (json.JSONDecodeError, Exception) as e:
                    continue
            
            # 也嘗試從 window.__APP_INITIAL_STATE__ 等全局變量中提取
            page_text = str(soup)
            for pattern in [
                r'window\.__APP_INITIAL_STATE__\s*=\s*(\{.*?\});',
                r'window\._SSR_HYDRATED_DATA\s*=\s*(\{.*?\});',
                r'"items":\s*(\[.*?\])',
            ]:
                matches = re.findall(pattern, page_text, re.DOTALL)
                for match in matches:
                    try:
                        data = json.loads(match)
                        if isinstance(data, list):
                            products.extend(self._find_products_in_list(data))
                        elif isinstance(data, dict):
                            products.extend(self._find_products_in_dict(data))
                    except Exception:
                        continue
        
        except Exception as e:
            print(f"從 JSON 提取商品時發生錯誤: {e}")
        
        return products
    
    def _find_products_in_dict(self, data: Dict[str, Any], depth: int = 0) -> List[Dict[str, Any]]:
        """遞歸搜索字典中的商品數據"""
        products = []
        if depth > 5:  # 限制遞歸深度
            return products
        
        for key, value in data.items():
            if key in ['items', 'products', 'item_basic', 'item_list'] and isinstance(value, list):
                products.extend(self._parse_product_list(value))
            elif isinstance(value, dict):
                products.extend(self._find_products_in_dict(value, depth + 1))
            elif isinstance(value, list):
                products.extend(self._find_products_in_list(value, depth + 1))
        
        return products
    
    def _find_products_in_list(self, data: List[Any], depth: int = 0) -> List[Dict[str, Any]]:
        """遞歸搜索列表中的商品數據"""
        products = []
        if depth > 5:
            return products
        
        for item in data:
            if isinstance(item, dict):
                # 檢查是否像商品對象
                if any(key in item for key in ['name', 'item_name', 'title', 'item_basic']):
                    product = self._parse_product_dict(item)
                    if product:
                        products.append(product)
                else:
                    products.extend(self._find_products_in_dict(item, depth + 1))
            elif isinstance(item, list):
                products.extend(self._find_products_in_list(item, depth + 1))
        
        return products
    
    def _parse_product_list(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """解析商品列表"""
        products = []
        for item in items:
            product = self._parse_product_dict(item)
            if product:
                products.append(product)
        return products
    
    def _parse_product_dict(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """解析單個商品字典"""
        try:
            product = {}
            
            # 名稱
            name = item.get('name') or item.get('item_name') or item.get('title')
            if not name and 'item_basic' in item:
                name = item['item_basic'].get('name') or item['item_basic'].get('item_name')
            if name:
                product['name'] = str(name)
            
            # 價格
            price = item.get('price') or item.get('price_min') or item.get('price_max')
            if not price and 'item_basic' in item:
                price = item['item_basic'].get('price') or item['item_basic'].get('price_min')
            if price:
                try:
                    price_val = int(price) / 100000  # Shopee 價格通常以最小單位存儲
                    currency = self._detect_currency_symbol(str(item))
                    product['price'] = f"{currency}{price_val:,.2f}"
                except Exception:
                    pass
            
            # 評分
            rating = item.get('rating') or item.get('item_rating')
            if not rating and 'item_basic' in item:
                rating = item['item_basic'].get('item_rating', {}).get('rating_star')
            if rating:
                try:
                    product['rating'] = float(rating)
                except Exception:
                    pass
            
            # 評論數
            review_count = item.get('review_count') or item.get('cmt_count')
            if not review_count and 'item_basic' in item:
                review_count = item['item_basic'].get('cmt_count')
            if review_count:
                product['review_count'] = str(review_count)
            
            # 圖片
            image = item.get('image') or item.get('image_url')
            if not image and 'item_basic' in item:
                image = item['item_basic'].get('image')
            if image:
                if isinstance(image, list) and image:
                    product['image_url'] = image[0]
                elif isinstance(image, str):
                    product['image_url'] = image
            
            # URL
            itemid = item.get('itemid') or item.get('item_id')
            shopid = item.get('shopid') or item.get('shop_id')
            if itemid and shopid:
                product['product_url'] = f"{self.BASE_URL}/product/{shopid}/{itemid}"
            elif 'item_basic' in item:
                itemid = item['item_basic'].get('itemid')
                shopid = item['item_basic'].get('shopid')
                if itemid and shopid:
                    product['product_url'] = f"{self.BASE_URL}/product/{shopid}/{itemid}"
            
            # 描述
            if 'name' in product:
                features = self.extract_product_features(product['name'])
                product['description'] = self.create_description(product['name'], features)
            
            return product if product.get('name') else None
            
        except Exception as e:
            print(f"解析商品字典時發生錯誤: {e}")
            return None

