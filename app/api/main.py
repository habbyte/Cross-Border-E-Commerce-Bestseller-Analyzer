"""
FastAPI 應用主入口
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import products, chat, search
from app.db.mongodb import mongodb
import logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Amazon Products API",
    description="產品數據 API",
    version="1.0.0",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "https://habbyte.github.io",
        "https://habbyte.github.io/Cross-Border-E-Commerce-Bestseller-Analyzer"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 註冊路由
app.include_router(products.router)
app.include_router(chat.router)
app.include_router(search.router)


@app.on_event("startup")
async def startup_event():
    """應用啟動時測試 MongoDB 連接"""
    logger.info("正在測試 MongoDB 連接...")
    if mongodb.test_connection():
        logger.info("✓ MongoDB 連接成功")
    else:
        logger.warning("✗ MongoDB 連接失敗，請檢查 MONGODB_URL 配置")


@app.on_event("shutdown")
async def shutdown_event():
    """應用關閉時關閉 MongoDB 連接"""
    logger.info("正在關閉 MongoDB 連接...")
    mongodb.close()


@app.get("/")
def root():
    return {"message": "Amazon Products API", "version": "1.0.0"}


@app.get("/health")
def health():
    """健康檢查端點，包含 MongoDB 連接狀態"""
    db = mongodb.connect()
    mongodb_status = "connected" if db is not None else "disconnected"
    return {
        "status": "ok",
        "mongodb": mongodb_status
    }

