#!/usr/bin/env python3
"""
導入 enhanced JSON 文件到數據庫
用法: python scripts/import_enhanced_json.py <json_file_path> [--run-id <run_id>]
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Optional
import os

# 設置 UTF-8 編碼以支持 Unicode 字符
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.pipelines.enhanced_adapter import extract_products_from_enhanced_json
from app.services.product_writer import bulk_upsert_products_with_categories
from app.config import settings


def import_json_file(json_file_path: str, run_id: Optional[str] = None, platform: Optional[str] = None):
    """
    導入 JSON 文件到數據庫
    
    Args:
        json_file_path: JSON 文件路徑
        run_id: 運行 ID（可選）
        platform: 平台名稱（可選，會從 JSON 中自動檢測）
    """
    json_path = Path(json_file_path)
    if not json_path.exists():
        print(f"錯誤: 文件不存在: {json_file_path}")
        return False
    
    print(f"讀取文件: {json_path}")
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"錯誤: JSON 解析失敗: {e}")
        return False
    except Exception as e:
        print(f"錯誤: 讀取文件失敗: {e}")
        return False
    
    # 提取產品數據
    print("提取產品數據...")
    products_with_categories = extract_products_from_enhanced_json(
        data,
        source_url=None,  # enhanced JSON 通常不包含 source_url
        platform=platform
    )
    
    if not products_with_categories:
        print("警告: 未找到任何產品數據")
        return False
    
    print(f"找到 {len(products_with_categories)} 個產品")
    
    # 導入數據庫
    print("導入數據庫...")
    try:
        count = bulk_upsert_products_with_categories(
            products_with_categories,
            actor_user_id=None,
            run_id=run_id
        )
        print(f"成功導入 {count} 個產品")
        return True
    except Exception as e:
        error_msg = str(e)
        # 處理 Unicode 編碼問題
        try:
            print(f"錯誤: 導入失敗: {error_msg}")
        except UnicodeEncodeError:
            print(f"錯誤: 導入失敗: {error_msg.encode('utf-8', errors='replace').decode('utf-8')}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(description="導入 enhanced JSON 文件到數據庫")
    parser.add_argument("json_file", help="JSON 文件路徑")
    parser.add_argument("--run-id", help="運行 ID（可選）")
    parser.add_argument("--platform", help="平台名稱（可選，會從 JSON 中自動檢測）")
    
    args = parser.parse_args()
    
    success = import_json_file(args.json_file, args.run_id, args.platform)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

