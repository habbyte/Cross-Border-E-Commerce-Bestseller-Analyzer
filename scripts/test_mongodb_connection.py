#!/usr/bin/env python3
"""
測試 MongoDB Atlas 連接
用法: python scripts/test_mongodb_connection.py
"""

import sys
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.config import settings
from app.db.mongodb import mongodb
from pymongo.errors import ServerSelectionTimeoutError, ConfigurationError
import traceback


def test_mongodb_connection():
    """測試 MongoDB 連接"""
    print("=" * 60)
    print("MongoDB Atlas 連接測試")
    print("=" * 60)
    
    # 1. 檢查環境變數
    print("\n1. 檢查環境變數配置...")
    if not settings.mongodb_url:
        print("❌ MONGODB_URL 未設定")
        print("   請在 .env 文件中添加：")
        print("   MONGODB_URL=mongodb+srv://<user>:<password>@<cluster>.mongodb.net/")
        return False
    else:
        # 只顯示前 30 個字符，隱藏密碼
        url_display = settings.mongodb_url[:30] + "..." if len(settings.mongodb_url) > 30 else settings.mongodb_url
        print(f"✓ MONGODB_URL: {url_display}")
    
    print(f"✓ MONGODB_DATABASE: {settings.mongodb_database}")
    
    # 2. 測試連接
    print("\n2. 測試 MongoDB 連接...")
    try:
        db = mongodb.connect()
        if db is None:
            print("❌ 連接失敗：返回 None")
            return False
        
        # 測試 ping
        print("   正在 ping 服務器...")
        mongodb.client.admin.command('ping')
        print("✓ Ping 成功")
        
        # 列出數據庫
        print("\n3. 檢查數據庫和集合...")
        db_names = mongodb.client.list_database_names()
        print(f"✓ 可用數據庫: {', '.join(db_names)}")
        
        if settings.mongodb_database not in db_names:
            print(f"⚠ 警告：數據庫 '{settings.mongodb_database}' 不存在")
            print("   將嘗試訪問該數據庫（MongoDB 會自動創建）")
        else:
            print(f"✓ 數據庫 '{settings.mongodb_database}' 存在")
        
        # 列出集合
        collections = db.list_collection_names()
        print(f"✓ 集合數量: {len(collections)}")
        if collections:
            print(f"   集合列表: {', '.join(collections[:10])}")
            if len(collections) > 10:
                print(f"   ... 還有 {len(collections) - 10} 個集合")
        
        # 檢查 products 集合
        print("\n4. 檢查 products 集合...")
        if "products" in collections:
            products_count = db["products"].count_documents({})
            print(f"✓ products 集合存在，包含 {products_count} 個文檔")
            
            # 顯示一個示例文檔的字段
            sample = db["products"].find_one()
            if sample:
                print(f"   示例文檔字段: {', '.join(list(sample.keys())[:10])}")
        else:
            print("⚠ products 集合不存在")
            print("   請確保已導入數據到 MongoDB")
        
        print("\n" + "=" * 60)
        print("✓ MongoDB 連接測試成功！")
        print("=" * 60)
        return True
        
    except ServerSelectionTimeoutError as e:
        print(f"❌ 連接超時: {e}")
        print("\n可能的原因：")
        print("  1. MongoDB Atlas IP 白名單未配置")
        print("  2. 網絡連接問題")
        print("  3. MongoDB Atlas 集群未運行")
        print("\n解決方案：")
        print("  1. 登錄 MongoDB Atlas")
        print("  2. 進入 Network Access")
        print("  3. 添加當前 IP 地址（或使用 0.0.0.0/0 允許所有 IP）")
        return False
        
    except ConfigurationError as e:
        print(f"❌ 配置錯誤: {e}")
        print("\n請檢查 MONGODB_URL 格式是否正確")
        print("正確格式: mongodb+srv://<username>:<password>@<cluster>.mongodb.net/")
        return False
        
    except Exception as e:
        print(f"❌ 連接失敗: {e}")
        print("\n詳細錯誤信息：")
        traceback.print_exc()
        return False
    
    finally:
        mongodb.close()


if __name__ == "__main__":
    success = test_mongodb_connection()
    sys.exit(0 if success else 1)

