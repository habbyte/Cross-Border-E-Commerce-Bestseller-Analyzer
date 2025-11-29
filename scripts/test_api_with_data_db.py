#!/usr/bin/env python3
"""
測試使用 data 數據庫的 API
"""

import sys
from pathlib import Path
import os

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 臨時設置環境變數使用 data 數據庫
os.environ["MONGODB_DATABASE"] = "data"

from app.config import settings
from app.db.mongodb import mongodb
from fastapi.testclient import TestClient
from app.api.main import app

print("=" * 60)
print("測試使用 data 數據庫的 API")
print("=" * 60)

# 測試連接
print("\n1. 測試 MongoDB 連接...")
db = mongodb.connect()
if db is None:
    print("❌ 連接失敗")
    sys.exit(1)

print(f"✓ 連接到數據庫: {settings.mongodb_database}")

# 檢查數據
collection = db["products"]
total = collection.count_documents({})
print(f"✓ products 集合總數: {total}")

# 測試 API
print("\n2. 測試 API 端點...")
client = TestClient(app)

# 測試獲取產品列表
response = client.get("/api/products/?limit=5")
print(f"GET /api/products/ - Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"✓ 返回產品數量: {len(data)}")
    if data:
        print(f"  第一個產品: {data[0]['title'][:60]}...")
        print(f"  價格: {data[0]['formattedPrice']}")
        print(f"  平台: {data[0]['platform']}")
else:
    print(f"❌ 錯誤: {response.text[:200]}")

# 測試統計
print("\n3. 測試統計端點...")
response = client.get("/api/products/stats/summary")
if response.status_code == 200:
    stats = response.json()
    print(f"✓ 統計信息:")
    print(f"  總產品數: {stats.get('totalProducts', 0)}")
    print(f"  活躍產品: {stats.get('activeProducts', 0)}")
    print(f"  平台分布: {stats.get('platforms', {})}")
else:
    print(f"❌ 錯誤: {response.text[:200]}")

print("\n" + "=" * 60)
print("測試完成！")
print("=" * 60)
print("\n提示：要永久使用 data 數據庫，請在 .env 文件中設置：")
print("MONGODB_DATABASE=data")

