from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class MongoDBClient:
    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.async_client: Optional[AsyncIOMotorClient] = None
        self.database = None
        self.async_database = None
        self._connected = False

    def connect(self):
        """建立同步 MongoDB 連線（使用連接池，不關閉連接）"""
        if not settings.mongodb_url:
            logger.warning("MONGODB_URL 未設定，無法連接 MongoDB")
            return None
        
        # 如果已經連接，直接返回數據庫對象
        if self._connected and self.client is not None:
            try:
                # 測試連接是否仍然有效
                self.client.admin.command('ping')
                return self.database
            except Exception as e:
                logger.warning(f"MongoDB 連接已斷開，重新連接: {e}")
                self._connected = False
        
        try:
            # 使用連接池配置
            self.client = MongoClient(
                settings.mongodb_url,
                serverSelectionTimeoutMS=5000,  # 5秒超時
                connectTimeoutMS=5000,
                socketTimeoutMS=5000,
                maxPoolSize=10,  # 連接池大小
                minPoolSize=1,
            )
            self.database = self.client[settings.mongodb_database]
            
            # 測試連接
            self.client.admin.command('ping')
            self._connected = True
            logger.info(f"成功連接到 MongoDB: {settings.mongodb_database}")
            return self.database
        except Exception as e:
            logger.error(f"MongoDB 連接失敗: {e}")
            logger.error(f"MONGODB_URL: {settings.mongodb_url[:20]}..." if settings.mongodb_url else "MONGODB_URL 為空")
            logger.error(f"MONGODB_DATABASE: {settings.mongodb_database}")
            self._connected = False
            return None

    def connect_async(self):
        """建立異步 MongoDB 連線"""
        if not settings.mongodb_url:
            return None
        
        if self.async_client is None:
            try:
                self.async_client = AsyncIOMotorClient(
                    settings.mongodb_url,
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=5000,
                    socketTimeoutMS=5000,
                    maxPoolSize=10,
                    minPoolSize=1,
                )
                self.async_database = self.async_client[settings.mongodb_database]
                logger.info(f"成功建立異步 MongoDB 連接: {settings.mongodb_database}")
            except Exception as e:
                logger.error(f"異步 MongoDB 連接失敗: {e}")
                return None
        
        return self.async_database

    def test_connection(self) -> bool:
        """測試 MongoDB 連接是否正常"""
        try:
            db = self.connect()
            if db is None:
                return False
            # 執行簡單查詢測試
            db.list_collection_names()
            return True
        except Exception as e:
            logger.error(f"MongoDB 連接測試失敗: {e}")
            return False

    def close(self):
        """關閉連線（僅在應用關閉時調用）"""
        if self.client:
            try:
                self.client.close()
                logger.info("MongoDB 同步連接已關閉")
            except Exception as e:
                logger.warning(f"關閉 MongoDB 連接時出錯: {e}")
            finally:
                self.client = None
                self.database = None
                self._connected = False
        
        if self.async_client:
            try:
                self.async_client.close()
                logger.info("MongoDB 異步連接已關閉")
            except Exception as e:
                logger.warning(f"關閉 MongoDB 異步連接時出錯: {e}")
            finally:
                self.async_client = None
                self.async_database = None


# 全域實例
mongodb = MongoDBClient()
