"""
項目配置文件
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """應用設置"""
    
    # 數據庫設置
    database_url: str = DATABASE_URL
    mongodb_url: str = MONGODB_URL
    
    # Firecrawl 設置
    firecrawl_api_key: str = FIRECRAWL_API_KEY
    
    # 爬蟲設置
    max_products_per_search: int = 20
    delay_min: float = 2.0
    delay_max: float = 5.0
    output_dir: str = "data/scraped_content"
    
    # 日誌設置
    log_level: str = "INFO"
    log_file: str = "data/logs/scraper.log"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 創建全局設置實例
settings = Settings()
