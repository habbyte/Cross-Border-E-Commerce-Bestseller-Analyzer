#!/usr/bin/env python3
"""
测试 API 响应
"""

import requests
import json

print("=" * 70)
print("测试 API 响应")
print("=" * 70)

try:
    url = "http://localhost:8000/api/products/?status=active&limit=5"
    print(f"\n请求 URL: {url}")
    response = requests.get(url, timeout=5)
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"返回产品数: {len(data)}")
        
        if data:
            print(f"\n第一个产品:")
            print(f"  ID: {data[0].get('id', 'N/A')}")
            print(f"  标题: {data[0].get('title', 'N/A')[:50]}...")
            print(f"  价格: {data[0].get('formattedPrice', 'N/A')}")
            print(f"  平台: {data[0].get('platform', 'N/A')}")
            print("\n✓ API 正常返回数据")
        else:
            print("\n⚠ API 返回空数组")
            print("可能原因:")
            print("  1. 数据库中没有符合查询条件的产品")
            print("  2. 查询逻辑有问题")
    else:
        print(f"\n❌ API 错误: {response.text[:200]}")
        
except requests.exceptions.ConnectionError:
    print("\n❌ 无法连接到 API 服务器")
    print("请确保后端服务器正在运行:")
    print("  python run_api.py")
except Exception as e:
    print(f"\n❌ 错误: {e}")

print("\n" + "=" * 70)

