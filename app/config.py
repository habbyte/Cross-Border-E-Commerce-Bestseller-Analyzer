from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    database_url: str = Field(alias="DATABASE_URL")
    firecrawl_api_key: str = Field(alias="FIRECRAWL_API_KEY")
    mongodb_url: str = Field(alias="MONGODB_URL", default="")
    mongodb_database: str = Field(alias="MONGODB_DATABASE", default="data")
    
    # 爬蟲設置
    max_products_per_search: int = Field(default=20, alias="MAX_PRODUCTS_PER_SEARCH")
    delay_min: float = Field(default=2.0, alias="DELAY_MIN")
    delay_max: float = Field(default=5.0, alias="DELAY_MAX")
    output_dir: str = Field(default="data/scraped_content", alias="OUTPUT_DIR")
    
    # 日誌設置
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_file: str = Field(default="data/logs/scraper.log", alias="LOG_FILE")
    
    # 增強爬蟲設置（Playwright）
    proxy: str = Field(default="", alias="PROXY")  # 格式: "http://user:pass@host:port" 或 "socks5://host:port"
    cookies_file: str = Field(default="data/cookies.json", alias="COOKIES_FILE")
    headless: bool = Field(default=True, alias="HEADLESS")
    enable_request_monitoring: bool = Field(default=True, alias="ENABLE_REQUEST_MONITORING")
    shopee_base_url: str = Field(default="https://shopee.tw/", alias="SHOPEE_BASE_URL")
    
    # Shopee 登入設置
    shopee_email: str = Field(default="", alias="SHOPEE_EMAIL")
    shopee_password: str = Field(default="", alias="SHOPEE_PASSWORD")
    
    # DeepSeek API 設置
    deepseek_api_key: str = Field(default="", alias="DEEPSEEK_API_KEY")

    def model_post_init(self, __context) -> None:
        # 將沒有指定驅動的 Postgres 連線字串，統一轉成 psycopg v3 驅動
        if self.database_url.startswith("postgres://"):
            self.database_url = self.database_url.replace("postgres://", "postgresql+psycopg://", 1)
        elif self.database_url.startswith("postgresql://") and "+psycopg" not in self.database_url:
            self.database_url = self.database_url.replace("postgresql://", "postgresql+psycopg://", 1)

    class Config:
        env_file = ".env"


settings = Settings()