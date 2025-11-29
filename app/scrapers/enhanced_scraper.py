"""
增強版爬蟲實現（使用 Playwright）
支持 Cookies、Proxy、JS 執行和請求監控
"""

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page, Request, Response
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
import re
import random
import json
import time
import threading
from pathlib import Path
from .base_scraper import BaseScraper

# 嘗試導入 nest_asyncio 以支持在異步環境中使用同步 API
try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    pass
except Exception:
    pass


class EnhancedScraper(BaseScraper):
    """增強版爬蟲（使用 Playwright）"""
    
    def __init__(
        self, 
        output_dir: str = "data/scraped_content",
        headless: bool = True,
        proxy: Optional[str] = None,
        cookies_file: Optional[str] = None,
        user_agent: Optional[str] = None,
        viewport_width: int = 1920,
        viewport_height: int = 1080,
        enable_request_monitoring: bool = True
    ):
        """
        初始化增強版爬蟲
        
        Args:
            output_dir: 輸出目錄
            headless: 是否無頭模式（False 會顯示瀏覽器窗口）
            proxy: Proxy 地址，格式: "http://user:pass@host:port" 或 "socks5://host:port"
            cookies_file: Cookies 文件路徑（JSON 格式）
            user_agent: 自定義 User-Agent
            viewport_width: 視窗寬度
            viewport_height: 視窗高度
            enable_request_monitoring: 是否啟用請求監控
        """
        super().__init__(output_dir)
        self.headless = headless
        self.proxy = proxy
        self.cookies_file = cookies_file
        self.user_agent = user_agent
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.enable_request_monitoring = enable_request_monitoring
        
        # 請求監控數據
        self.request_logs: List[Dict[str, Any]] = []
        self.response_logs: List[Dict[str, Any]] = []
        
        # 初始化 Playwright
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # 隨機 User-Agent 列表
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        ]
    
    def _setup_browser(self):
        """設置瀏覽器和上下文"""
        if self.browser is None:
            # 確保 nest_asyncio 已應用到當前線程的 asyncio loop
            try:
                import nest_asyncio
                import asyncio
                # 檢查是否已經應用過
                if not hasattr(asyncio, '_nest_patched'):
                    nest_asyncio.apply()
                # 如果已經有運行中的 loop，確保 nest_asyncio 已應用到該 loop
                try:
                    loop = asyncio.get_running_loop()
                    # 即使已經應用過，也要確保應用到當前 loop
                    # nest_asyncio 可以多次應用，不會有問題
                    nest_asyncio.apply(loop)
                except RuntimeError:
                    # 沒有運行中的 loop，這是正常的，直接應用即可
                    if not hasattr(asyncio, '_nest_patched'):
                        nest_asyncio.apply()
            except ImportError:
                pass
            except Exception as e:
                # 如果 nest_asyncio 應用失敗，記錄但不阻止繼續
                print(f"警告: nest_asyncio 應用失敗: {e}")
            
            try:
                # 啟動 Playwright
                self.playwright = sync_playwright().start()
            except Exception as e:
                error_msg = str(e)
                if "asyncio loop" in error_msg.lower() or "sync api" in error_msg.lower():
                    print("警告: 檢測到異步環境，嘗試使用 nest_asyncio 修復...")
                    try:
                        import nest_asyncio
                        import asyncio
                        # 強制應用到當前 loop（如果存在）
                        try:
                            loop = asyncio.get_running_loop()
                            nest_asyncio.apply(loop)
                            print("已應用 nest_asyncio 到運行中的 loop")
                        except RuntimeError:
                            # 沒有運行中的 loop，直接應用
                            nest_asyncio.apply()
                            print("已應用 nest_asyncio（無運行中的 loop）")
                        
                        # 再次嘗試啟動
                        self.playwright = sync_playwright().start()
                    except Exception as e2:
                        raise RuntimeError(
                            f"無法在異步環境中啟動 Playwright。\n"
                            f"原始錯誤: {error_msg}\n"
                            f"修復嘗試錯誤: {e2}\n"
                            f"提示: 請確保已安裝 nest-asyncio: pip install nest-asyncio"
                        )
                else:
                    raise
            
            # 構建啟動選項（增強反檢測）
            launch_options = {
                'headless': self.headless,
                'args': [
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--disable-site-isolation-trials',
                    '--disable-infobars',
                    '--window-size=1920,1080',
                    '--start-maximized',
                    '--disable-extensions-except',
                    '--disable-plugins-discovery',
                    '--disable-default-apps',
                ]
            }
            
            # 添加 Proxy
            if self.proxy:
                launch_options['proxy'] = {'server': self.proxy}
            
            # 啟動瀏覽器
            self.browser = self.playwright.chromium.launch(**launch_options)
            
            # 構建上下文選項（增強反檢測）
            # 根據 Shopee 站點選擇合適的時區和語言
            if 'shopee.tw' in str(getattr(self, 'BASE_URL', '')):
                locale = 'zh-TW'
                timezone = 'Asia/Taipei'
                geolocation = {'latitude': 25.0330, 'longitude': 121.5654}  # 台北
            elif 'shopee.sg' in str(getattr(self, 'BASE_URL', '')):
                locale = 'en-SG'
                timezone = 'Asia/Singapore'
                geolocation = {'latitude': 1.3521, 'longitude': 103.8198}  # 新加坡
            else:
                locale = 'en-US'
                timezone = 'America/New_York'
                geolocation = {'latitude': 40.7128, 'longitude': -74.0060}  # New York
            
            context_options = {
                'viewport': {'width': self.viewport_width, 'height': self.viewport_height},
                'user_agent': self.user_agent or random.choice(self.user_agents),
                'locale': locale,
                'timezone_id': timezone,
                'permissions': ['geolocation', 'notifications'],
                'geolocation': geolocation,
                'color_scheme': 'light',
                'has_touch': False,
                'is_mobile': False,
                'device_scale_factor': 1,
                'screen': {'width': self.viewport_width, 'height': self.viewport_height},
            }
            
            # 添加 Proxy 到上下文（如果沒有在啟動時設置）
            if self.proxy and 'proxy' not in launch_options:
                context_options['proxy'] = {'server': self.proxy}
            
            # 創建上下文
            self.context = self.browser.new_context(**context_options)
            
            # 加載 Cookies
            if self.cookies_file and Path(self.cookies_file).exists():
                try:
                    with open(self.cookies_file, 'r', encoding='utf-8') as f:
                        cookies = json.load(f)
                        # 修復 cookies 格式，確保 sameSite 字段正確
                        fixed_cookies = []
                        for cookie in cookies:
                            fixed_cookie = dict(cookie)
                            # 確保 sameSite 是有效的值
                            if 'sameSite' in fixed_cookie:
                                same_site = fixed_cookie['sameSite']
                                if same_site not in ['Strict', 'Lax', 'None']:
                                    # 如果值不正確，根據情況設置默認值
                                    if same_site in ['strict', 'STRICT']:
                                        fixed_cookie['sameSite'] = 'Strict'
                                    elif same_site in ['lax', 'LAX']:
                                        fixed_cookie['sameSite'] = 'Lax'
                                    elif same_site in ['none', 'NONE']:
                                        fixed_cookie['sameSite'] = 'None'
                                    else:
                                        fixed_cookie['sameSite'] = 'Lax'  # 默認值
                            else:
                                # 如果沒有 sameSite，設置默認值
                                fixed_cookie['sameSite'] = 'Lax'
                            
                            # 確保必要的字段存在
                            if 'domain' not in fixed_cookie or not fixed_cookie['domain']:
                                continue  # 跳過無效的 cookie
                            
                            fixed_cookies.append(fixed_cookie)
                        
                        if fixed_cookies:
                            self.context.add_cookies(fixed_cookies)
                            print(f"已加載 {len(fixed_cookies)} 個 Cookies")
                except Exception as e:
                    print(f"加載 Cookies 失敗: {e}")
            
            # 創建頁面
            self.page = self.context.new_page()
            
            # 設置額外的請求頭（增強反檢測）
            extra_headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
            }
            self.context.set_extra_http_headers(extra_headers)
            
            # 設置請求監控
            if self.enable_request_monitoring:
                self._setup_request_monitoring()
            
            # 注入反檢測腳本
            self._inject_stealth_scripts()
    
    def _setup_request_monitoring(self):
        """設置請求監控"""
        if not self.page:
            return
        
        def on_request(request: Request):
            """請求攔截器"""
            request_info = {
                'url': request.url,
                'method': request.method,
                'headers': request.headers,
                'post_data': request.post_data,
                'timestamp': time.time()
            }
            self.request_logs.append(request_info)
            print(f"[請求] {request.method} {request.url}")
        
        def on_response(response: Response):
            """響應攔截器"""
            response_info = {
                'url': response.url,
                'status': response.status,
                'headers': dict(response.headers),
                'timestamp': time.time()
            }
            self.response_logs.append(response_info)
            print(f"[響應] {response.status} {response.url}")
        
        self.page.on('request', on_request)
        self.page.on('response', on_response)
    
    def _inject_stealth_scripts(self):
        """注入反檢測腳本（增強版）"""
        if not self.page:
            return
        
        # 增強的反檢測腳本
        stealth_script = """
        // 1. 隱藏 webdriver 屬性
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        
        // 2. 偽造 Chrome 對象
        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
            app: {}
        };
        
        // 3. 偽造權限
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        
        // 4. 偽造插件（更真實的列表）
        Object.defineProperty(navigator, 'plugins', {
            get: () => {
                const plugins = [];
                for (let i = 0; i < 5; i++) {
                    plugins.push({
                        name: `Plugin ${i}`,
                        description: `Plugin ${i} Description`,
                        filename: `plugin${i}.dll`
                    });
                }
                return plugins;
            }
        });
        
        // 5. 偽造語言（根據站點）
        const locale = window.location.hostname.includes('.tw') ? 
            ['zh-TW', 'zh', 'en'] : 
            window.location.hostname.includes('.sg') ? 
            ['en-SG', 'en', 'zh'] : 
            ['en-US', 'en'];
        Object.defineProperty(navigator, 'languages', {
            get: () => locale
        });
        
        // 6. 偽造 platform
        Object.defineProperty(navigator, 'platform', {
            get: () => 'Win32'
        });
        
        // 7. 偽造 hardwareConcurrency
        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: () => 8
        });
        
        // 8. 偽造 deviceMemory
        Object.defineProperty(navigator, 'deviceMemory', {
            get: () => 8
        });
        
        // 9. 覆蓋 toString 方法
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) {
                return 'Intel Inc.';
            }
            if (parameter === 37446) {
                return 'Intel Iris OpenGL Engine';
            }
            return getParameter.call(this, parameter);
        };
        
        // 10. 偽造 canvas 指紋
        const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function() {
            const context = this.getContext('2d');
            if (context) {
                const imageData = context.getImageData(0, 0, this.width, this.height);
                for (let i = 0; i < imageData.data.length; i += 4) {
                    imageData.data[i] += Math.floor(Math.random() * 3) - 1;
                }
                context.putImageData(imageData, 0, 0);
            }
            return originalToDataURL.apply(this, arguments);
        };
        
        // 11. 偽造 WebGL 指紋
        const getParameter2 = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) {
                return 'Intel Inc.';
            }
            if (parameter === 37446) {
                return 'Intel Iris OpenGL Engine';
            }
            return getParameter2.call(this, parameter);
        };
        
        // 12. 偽造 Battery API
        if (navigator.getBattery) {
            navigator.getBattery = () => Promise.resolve({
                charging: true,
                chargingTime: 0,
                dischargingTime: Infinity,
                level: 1
            });
        }
        
        // 13. 偽造 Connection API
        if (navigator.connection) {
            Object.defineProperty(navigator, 'connection', {
                get: () => ({
                    effectiveType: '4g',
                    rtt: 50,
                    downlink: 10,
                    saveData: false
                })
            });
        }
        
        // 14. 移除自動化標記
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false
        });
        
        // 15. 偽造 Notification
        if (window.Notification) {
            window.Notification.permission = 'default';
        }
        """
        
        self.page.add_init_script(stealth_script)
    
    def get_page(self, url: str, wait_selector: Optional[str] = None, timeout: int = 60000) -> Optional[BeautifulSoup]:
        """
        獲取頁面內容
        
        Args:
            url: 目標 URL
            wait_selector: 等待選擇器（可選，用於等待動態內容加載）
            timeout: 超時時間（毫秒，預設 60 秒）
        """
        try:
            if self.page is None:
                self._setup_browser()
            
            print(f"正在獲取頁面: {url}")
            
            # 隨機延遲
            delay = random.uniform(2, 5)
            print(f"等待 {delay:.1f} 秒...")
            self.add_delay(delay, delay + 0.5)
            
            # 隨機更新 User-Agent
            if not self.user_agent:
                new_ua = random.choice(self.user_agents)
                self.context.set_extra_http_headers({'User-Agent': new_ua})
            
            # 設置 Referer（如果是搜索頁面，Referer 應該是首頁）
            referer = None
            if hasattr(self, 'BASE_URL') and self.BASE_URL:
                referer = self.BASE_URL
            elif '/search' in url:
                # 從 URL 提取域名作為 Referer
                from urllib.parse import urlparse
                parsed = urlparse(url)
                referer = f"{parsed.scheme}://{parsed.netloc}"
            
            # 訪問頁面（使用更寬鬆的等待策略）
            goto_options = {'wait_until': 'domcontentloaded', 'timeout': timeout}
            if referer:
                goto_options['referer'] = referer
            
            try:
                self.page.goto(url, **goto_options)
            except Exception as e:
                print(f"頁面導航警告: {e}，嘗試繼續...")
                # 即使導航失敗，也嘗試獲取當前頁面內容
            
            # 等待特定選擇器（如果提供，但不要過於嚴格）
            if wait_selector:
                try:
                    self.page.wait_for_selector(wait_selector, timeout=20000, state='attached')
                    print(f"成功找到選擇器: {wait_selector}")
                except Exception as e:
                    print(f"等待選擇器 {wait_selector} 超時（繼續執行）: {e}")
                    # 不拋出異常，繼續執行
            
            # 等待頁面加載（使用更寬鬆的策略）
            try:
                # 先等待 DOM 內容加載
                self.page.wait_for_load_state('domcontentloaded', timeout=15000)
                print("DOM 內容已加載")
            except Exception as e:
                print(f"等待 DOM 加載超時（繼續執行）: {e}")
            
            # 嘗試等待網絡空閒，但不強制要求
            try:
                self.page.wait_for_load_state('networkidle', timeout=20000)
                print("網絡已空閒")
            except Exception as e:
                print(f"等待網絡空閒超時（繼續執行）: {e}")
                # 即使超時也繼續，至少等待 DOM 加載完成
            
            # 模擬人類行為（在獲取內容前）
            try:
                self._simulate_human_behavior()
            except Exception as e:
                print(f"模擬人類行為時發生錯誤（繼續執行）: {e}")
            
            # 滾動頁面以觸發懶加載（可選）
            try:
                self._scroll_page()
            except Exception as e:
                print(f"滾動頁面時發生錯誤（繼續執行）: {e}")
            
            # 獲取頁面內容
            try:
                content = self.page.content()
                if not content or len(content) < 100:
                    print("警告: 頁面內容過短，可能未正確加載")
                    return None
                
                soup = BeautifulSoup(content, 'html.parser')
                
                # 檢查是否被重定向到驗證頁面
                current_url = self.page.url
                current_url_lower = current_url.lower() if isinstance(current_url, str) else ''
                if any(keyword in current_url_lower for keyword in ['captcha', 'robot', 'verify']):
                    print("檢測到驗證/安全頁面。")
                    if self._handle_verification_page(current_url):
                        print("驗證處理完成，重新解析頁面內容。")
                        content = self.page.content()
                        if content and len(content) >= 100:
                            return BeautifulSoup(content, 'html.parser')
                    print("驗證未處理或仍受限，跳過此 URL")
                    return None
                
                print(f"成功獲取頁面，內容長度: {len(content)} 字節")
                return soup
            except Exception as e:
                print(f"獲取頁面內容失敗: {e}")
                return None
            
        except Exception as e:
            error_msg = str(e)
            print(f"獲取頁面失敗: {error_msg}")
            
            # 如果是異步環境錯誤，提供更詳細的提示
            if "asyncio loop" in error_msg.lower():
                print("\n提示: 如果持續出現此錯誤，請確保已安裝 nest-asyncio:")
                print("  pip install nest-asyncio")
            
            return None
    
    def _simulate_human_behavior(self):
        """模擬真實用戶行為（鼠標移動、隨機滾動等）"""
        if not self.page:
            return
        
        try:
            # 1. 隨機鼠標移動
            viewport = self.page.viewport_size
            if viewport:
                for _ in range(random.randint(2, 5)):
                    x = random.randint(100, viewport['width'] - 100)
                    y = random.randint(100, viewport['height'] - 100)
                    self.page.mouse.move(x, y, steps=random.randint(10, 20))
                    time.sleep(random.uniform(0.1, 0.3))
            
            # 2. 隨機滾動（模擬閱讀行為）
            scroll_amount = random.randint(200, 500)
            scroll_direction = random.choice([1, -1])
            self.page.evaluate(f"window.scrollBy(0, {scroll_amount * scroll_direction})")
            time.sleep(random.uniform(0.5, 1.5))
            
            # 3. 隨機暫停（模擬思考時間）
            time.sleep(random.uniform(0.5, 2.0))
            
        except Exception as e:
            # 行為模擬失敗不應該阻止整個流程
            pass
    
    def _scroll_page(self, scroll_pause_time: float = 1.0):
        """滾動頁面以觸發懶加載（增強版：包含人類行為模擬）"""
        if not self.page:
            return
        
        try:
            # 先模擬人類行為
            self._simulate_human_behavior()
            
            # 重置滾動計數器
            self._scroll_count = 0
            
            # 獲取頁面高度
            last_height = self.page.evaluate("document.body.scrollHeight")
            
            while True:
                # 隨機滾動（不是直接到底部，更自然）
                current_scroll = self.page.evaluate("window.pageYOffset || document.documentElement.scrollTop")
                scroll_target = min(current_scroll + random.randint(300, 800), last_height)
                self.page.evaluate(f"window.scrollTo({{top: {scroll_target}, behavior: 'smooth'}})")
                
                # 等待新內容加載（隨機時間）
                time.sleep(random.uniform(scroll_pause_time, scroll_pause_time * 1.5))
                
                # 計算新的頁面高度
                new_height = self.page.evaluate("document.body.scrollHeight")
                
                if new_height == last_height:
                    break
                
                last_height = new_height
                
                # 限制滾動次數（最多滾動3次，避免過度延遲）
                self._scroll_count = getattr(self, '_scroll_count', 0) + 1
                if self._scroll_count >= 3:
                    break
                    
                # 偶爾模擬人類行為
                if random.random() < 0.3:
                    self._simulate_human_behavior()
        except Exception as e:
            # 滾動失敗不應該阻止整個流程
            pass
    
    def save_cookies(self, filepath: str = "data/cookies.json"):
        """保存當前 Cookies"""
        if not self.context:
            return
        
        try:
            cookies = self.context.cookies()
            cookie_file = Path(filepath)
            cookie_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(cookie_file, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, indent=2, ensure_ascii=False)
            
            print(f"已保存 {len(cookies)} 個 Cookies 到 {filepath}")
        except Exception as e:
            print(f"保存 Cookies 失敗: {e}")
    
    def save_request_logs(self, filepath: str = "data/request_logs.json"):
        """保存請求日誌"""
        if not self.request_logs:
            return
        
        try:
            log_file = Path(filepath)
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            logs = {
                'requests': self.request_logs,
                'responses': self.response_logs
            }
            
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
            
            print(f"已保存請求日誌到 {filepath}")
        except Exception as e:
            print(f"保存請求日誌失敗: {e}")
    
    def _handle_verification_page(self, current_url: str) -> bool:
        """
        子類可覆寫此方法以自定義驗證處理邏輯。
        若返回 True，代表已處理並可繼續解析頁面；False 則表示無法處理。
        """
        return False
    
    def close(self):
        """關閉瀏覽器和清理資源"""
        try:
            if self.page:
                self.page.close()
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            
            self.page = None
            self.context = None
            self.browser = None
            self.playwright = None
        except Exception as e:
            print(f"關閉瀏覽器時發生錯誤: {e}")
    
    def __enter__(self):
        """上下文管理器入口"""
        self._setup_browser()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
    
    # 以下方法需要子類實現或重寫
    def extract_product_info(self, product_element) -> Dict[str, Any]:
        """從商品元素中提取商品信息（需要子類實現）"""
        raise NotImplementedError("子類需要實現此方法")
    
    def scrape_product_detail(self, product_url: str) -> Dict[str, Any]:
        """爬取商品詳情頁面的完整信息（需要子類實現）"""
        raise NotImplementedError("子類需要實現此方法")
    
    def scrape_products(self, search_terms: List[str], fetch_details: bool = True) -> List[Dict[str, Any]]:
        """爬取商品信息（需要子類實現）"""
        raise NotImplementedError("子類需要實現此方法")
    
    def scrape_categories(self) -> List[Dict[str, Any]]:
        """爬取分類信息（需要子類實現）"""
        raise NotImplementedError("子類需要實現此方法")

