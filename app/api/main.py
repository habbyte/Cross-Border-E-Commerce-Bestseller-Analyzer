"""
FastAPI 應用主入口
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import products

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
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 註冊路由
app.include_router(products.router)


@app.get("/")
def root():
    return {"message": "Amazon Products API", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "ok"}

