#!/usr/bin/env python3
"""
測試 API 連接和數據庫連接
用法: python scripts/test_api_connection.py
"""

import sys
import os
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.db.session import SessionLocal, engine
from app.db.models import Base, Product
from sqlalchemy import select, func
from app.config import settings


def test_database_connection():
    """測試數據庫連接"""
    print("=" * 50)
    print("測試數據庫連接")
    print("=" * 50)
    
    try:
        # 測試連接
        db = SessionLocal()
        print(f"✓ 數據庫連接成功")
        print(f"  連接字符串: {settings.database_url[:50]}...")
        
        # 檢查表是否存在
        inspector = engine.dialect.inspector(engine)
        tables = inspector.get_table_names()
        print(f"✓ 數據庫表: {', '.join(tables)}")
        
        # 檢查產品數量
        count = db.execute(select(func.count(Product.id))).scalar()
        print(f"✓ 產品總數: {count}")
        
        # 檢查活躍產品數量
        active_count = db.execute(
            select(func.count(Product.id)).where(Product.status == "active")
        ).scalar()
        print(f"✓ 活躍產品數: {active_count}")
        
        # 顯示前 3 個產品
        products = db.execute(
            select(Product).where(Product.status == "active").limit(3)
        ).scalars().all()
        
        if products:
            print(f"\n前 3 個活躍產品:")
            for p in products:
                print(f"  - ID: {p.id}, 名稱: {p.name[:50]}, 平台: {p.platform}")
        else:
            print("\n⚠ 警告: 數據庫中沒有活躍產品")
            print("  請運行數據導入腳本或爬蟲腳本來添加數據")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"✗ 數據庫連接失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_endpoints():
    """測試 API 端點（需要 API 服務器運行）"""
    print("\n" + "=" * 50)
    print("測試 API 端點")
    print("=" * 50)
    print("注意: 此測試需要 API 服務器運行在 http://localhost:8000")
    print("      請先運行: python run_api.py")
    print()
    
    import requests
    
    base_url = "http://localhost:8000"
    
    # 測試健康檢查
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print(f"✓ 健康檢查成功: {response.json()}")
        else:
            print(f"✗ 健康檢查失敗: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ 無法連接到 API 服務器")
        print("  請確保 API 服務器正在運行: python run_api.py")
        return False
    except Exception as e:
        print(f"✗ 健康檢查錯誤: {e}")
        return False
    
    # 測試產品列表端點
    try:
        response = requests.get(
            f"{base_url}/api/products/",
            params={"status": "active", "limit": 5},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✓ 產品列表端點成功: 返回 {len(data)} 個產品")
            if data:
                print(f"  示例產品: {data[0].get('title', 'N/A')[:50]}")
        else:
            print(f"✗ 產品列表端點失敗: {response.status_code}")
            print(f"  響應: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"✗ 產品列表端點錯誤: {e}")
        return False
    
    # 測試統計端點
    try:
        response = requests.get(f"{base_url}/api/products/stats/summary", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print(f"✓ 統計端點成功: {stats}")
        else:
            print(f"✗ 統計端點失敗: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ 統計端點錯誤: {e}")
        return False
    
    return True


def main():
    """主函數"""
    print("\n" + "=" * 50)
    print("API 連接測試工具")
    print("=" * 50)
    print()
    
    # 測試數據庫連接
    db_ok = test_database_connection()
    
    # 測試 API 端點
    api_ok = test_api_endpoints()
    
    # 總結
    print("\n" + "=" * 50)
    print("測試總結")
    print("=" * 50)
    print(f"數據庫連接: {'✓ 通過' if db_ok else '✗ 失敗'}")
    print(f"API 端點: {'✓ 通過' if api_ok else '✗ 失敗'}")
    
    if db_ok and api_ok:
        print("\n✓ 所有測試通過！前端應該能夠正常連接後端。")
    else:
        print("\n⚠ 部分測試失敗，請檢查上述錯誤信息。")
    
    print()


if __name__ == "__main__":
    main()

