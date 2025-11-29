#!/usr/bin/env python3
"""
诊断前端和后端连接问题
"""

import sys
from pathlib import Path
import requests
import json

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.config import settings
from app.db.mongodb import mongodb
from pymongo import MongoClient

print("=" * 70)
print("前端和后端连接诊断")
print("=" * 70)

# 1. 检查后端配置
print("\n【1. 后端配置检查】")
print(f"   MONGODB_DATABASE: {settings.mongodb_database}")
print(f"   MONGODB_URL: {settings.mongodb_url[:30]}..." if settings.mongodb_url else "   MONGODB_URL: 未设置")

# 2. 检查 MongoDB 连接
print("\n【2. MongoDB 连接检查】")
db = mongodb.connect()
if db is None:
    print("   ❌ MongoDB 连接失败")
    sys.exit(1)
else:
    print("   ✓ MongoDB 连接成功")

# 3. 检查当前数据库的产品
print("\n【3. 当前数据库产品检查】")
collection = db["products"]
total = collection.count_documents({})
active = collection.count_documents({"status": "active"})
draft = collection.count_documents({"status": "draft"})
no_status = collection.count_documents({"status": {"$exists": False}})
active_query = collection.count_documents({
    "$or": [{"status": "active"}, {"status": {"$exists": False}}]
})

print(f"   数据库: {settings.mongodb_database}")
print(f"   总产品数: {total}")
print(f"   active: {active}, draft: {draft}, 无status: {no_status}")
print(f"   符合 active 查询: {active_query}")

# 4. 检查 data 数据库
print("\n【4. data 数据库检查】")
client = MongoClient(settings.mongodb_url)
db_data = client["data"]
collection_data = db_data["products"]
total_data = collection_data.count_documents({})
active_query_data = collection_data.count_documents({
    "$or": [{"status": "active"}, {"status": {"$exists": False}}]
})
print(f"   总产品数: {total_data}")
print(f"   符合 active 查询: {active_query_data}")

# 5. 测试 API
print("\n【5. API 测试】")
try:
    # 测试 active 状态
    response = requests.get("http://localhost:8000/api/products/?status=active&limit=5", timeout=5)
    print(f"   GET /api/products/?status=active&limit=5")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   返回产品数: {len(data)}")
        if data:
            print(f"   第一个产品: {data[0].get('title', 'N/A')[:50]}...")
            print(f"   产品ID: {data[0].get('id', 'N/A')}")
        else:
            print("   ⚠ 返回空数组！")
    else:
        print(f"   ❌ 错误: {response.text[:200]}")
except requests.exceptions.ConnectionError:
    print("   ❌ 无法连接到 API 服务器")
    print("   请确保后端服务器正在运行: python run_api.py")
except Exception as e:
    print(f"   ❌ 错误: {e}")

# 6. 诊断结果
print("\n【6. 诊断结果】")
if active_query == 0:
    print("   ❌ 问题：当前数据库没有符合 active 查询的产品")
    print(f"   ✓ 解决方案：切换到 data 数据库（有 {active_query_data} 个符合 active 查询的产品）")
    print(f"   请在 .env 文件中设置: MONGODB_DATABASE=data")
    print(f"   然后重启后端服务器")
elif active_query > 0:
    print(f"   ✓ 当前数据库有 {active_query} 个符合 active 查询的产品")
    if response.status_code == 200 and len(response.json()) == 0:
        print("   ⚠ 但 API 返回空数组，可能是查询逻辑问题")
    else:
        print("   ✓ API 可以正常返回数据")

# 7. 前端检查建议
print("\n【7. 前端检查建议】")
print("   1. 打开浏览器开发者工具 (F12)")
print("   2. 查看 Console 标签，查找 ProductService 的日志")
print("   3. 查看 Network 标签，检查对 /api/products/ 的请求")
print("   4. 确认请求 URL 和响应状态码")
print("   5. 检查响应数据是否为空数组")

print("\n" + "=" * 70)
print("诊断完成")
print("=" * 70)

