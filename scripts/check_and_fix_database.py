#!/usr/bin/env python3
"""
检查并修复数据库配置问题
"""

import sys
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.config import settings
from app.db.mongodb import mongodb
from pymongo import MongoClient

print("=" * 60)
print("数据库配置检查和修复")
print("=" * 60)

# 1. 检查当前配置
print("\n1. 当前配置:")
print(f"   MONGODB_DATABASE: {settings.mongodb_database}")

# 2. 检查两个数据库的产品数量
print("\n2. 检查数据库产品数量:")
client = MongoClient(settings.mongodb_url)

# amazon_products 数据库
db_amazon = client["amazon_products"]
collection_amazon = db_amazon["products"]
total_amazon = collection_amazon.count_documents({})
active_amazon = collection_amazon.count_documents({"status": "active"})
draft_amazon = collection_amazon.count_documents({"status": "draft"})
no_status_amazon = collection_amazon.count_documents({"status": {"$exists": False}})
active_query_amazon = collection_amazon.count_documents({
    "$or": [{"status": "active"}, {"status": {"$exists": False}}]
})

print(f"   amazon_products:")
print(f"     总产品数: {total_amazon}")
print(f"     active: {active_amazon}, draft: {draft_amazon}, 无status: {no_status_amazon}")
print(f"     符合 active 查询: {active_query_amazon}")

# data 数据库
db_data = client["data"]
collection_data = db_data["products"]
total_data = collection_data.count_documents({})
active_data = collection_data.count_documents({"status": "active"})
draft_data = collection_data.count_documents({"status": "draft"})
no_status_data = collection_data.count_documents({"status": {"$exists": False}})
active_query_data = collection_data.count_documents({
    "$or": [{"status": "active"}, {"status": {"$exists": False}}]
})

print(f"   data:")
print(f"     总产品数: {total_data}")
print(f"     active: {active_data}, draft: {draft_data}, 无status: {no_status_data}")
print(f"     符合 active 查询: {active_query_data}")

# 3. 建议
print("\n3. 建议:")
if active_query_amazon == 0 and active_query_data > 0:
    print(f"   ⚠ 当前使用 amazon_products 数据库，但没有符合 active 查询的产品")
    print(f"   ✓ data 数据库有 {active_query_data} 个符合 active 查询的产品")
    print(f"\n   解决方案：")
    print(f"   1. 在 .env 文件中设置: MONGODB_DATABASE=data")
    print(f"   2. 或者更新 amazon_products 数据库中的产品状态为 active")
elif active_query_amazon > 0:
    print(f"   ✓ amazon_products 数据库有 {active_query_amazon} 个符合 active 查询的产品")
    print(f"   当前配置可以使用")
else:
    print(f"   ⚠ 两个数据库都没有符合 active 查询的产品")
    print(f"   建议使用 status=all 或 status=draft 来获取数据")

# 4. 测试 API
print("\n4. 测试 API (使用当前配置):")
db = mongodb.connect()
if db:
    collection = db["products"]
    query = {"$or": [{"status": "active"}, {"status": {"$exists": False}}]}
    count = collection.count_documents(query)
    print(f"   当前数据库符合 active 查询的产品数: {count}")
    
    if count == 0:
        print(f"   ⚠ API 将返回空数组，前端会显示为空")
    else:
        print(f"   ✓ API 可以返回 {count} 个产品")

print("\n" + "=" * 60)
print("检查完成！")
print("=" * 60)

