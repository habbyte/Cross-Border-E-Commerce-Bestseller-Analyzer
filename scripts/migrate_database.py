#!/usr/bin/env python3
"""
數據庫遷移腳本
添加 enhanced JSON 支持的新字段
"""

import sys
import os
from pathlib import Path

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

from sqlalchemy import text
from app.db.session import SessionLocal, engine
from app.config import settings


def migrate_database():
    """執行數據庫遷移"""
    print("開始數據庫遷移...")
    
    migration_sql = """
    -- 添加新字段（如果不存在）
    DO $$ 
    BEGIN
        -- status 字段
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                      WHERE table_name='products' AND column_name='status') THEN
            ALTER TABLE products ADD COLUMN status VARCHAR DEFAULT 'draft';
        END IF;
        
        -- category_path 字段
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                      WHERE table_name='products' AND column_name='category_path') THEN
            ALTER TABLE products ADD COLUMN category_path TEXT;
        END IF;
        
        -- bought_in_past_month 字段
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                      WHERE table_name='products' AND column_name='bought_in_past_month') THEN
            ALTER TABLE products ADD COLUMN bought_in_past_month VARCHAR;
        END IF;
        
        -- product_details 字段
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                       WHERE table_name='products' AND column_name='product_details') THEN
            ALTER TABLE products ADD COLUMN product_details JSONB;
        END IF;
        
        -- about_this_item 字段
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                      WHERE table_name='products' AND column_name='about_this_item') THEN
            ALTER TABLE products ADD COLUMN about_this_item JSONB;
        END IF;
        
        -- color_options 字段
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                      WHERE table_name='products' AND column_name='color_options') THEN
            ALTER TABLE products ADD COLUMN color_options JSONB;
        END IF;
        
        -- size_options 字段
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                      WHERE table_name='products' AND column_name='size_options') THEN
            ALTER TABLE products ADD COLUMN size_options JSONB;
        END IF;
        
        -- platform 字段
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                      WHERE table_name='products' AND column_name='platform') THEN
            ALTER TABLE products ADD COLUMN platform VARCHAR;
        END IF;
        
        -- created_by 字段（如果 users 表存在）
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                      WHERE table_name='products' AND column_name='created_by') THEN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='users') THEN
                ALTER TABLE products ADD COLUMN created_by INTEGER;
            ELSE
                ALTER TABLE products ADD COLUMN created_by INTEGER;
            END IF;
        END IF;
        
        -- updated_by 字段（如果 users 表存在）
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                      WHERE table_name='products' AND column_name='updated_by') THEN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='users') THEN
                ALTER TABLE products ADD COLUMN updated_by INTEGER;
            ELSE
                ALTER TABLE products ADD COLUMN updated_by INTEGER;
            END IF;
        END IF;
        
        -- run_id 字段
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                      WHERE table_name='products' AND column_name='run_id') THEN
            ALTER TABLE products ADD COLUMN run_id VARCHAR;
        END IF;
    END $$;
    """
    
    try:
        with SessionLocal() as session:
            session.execute(text(migration_sql))
            session.commit()
            print("數據庫遷移成功完成！")
            return True
    except Exception as e:
        print(f"數據庫遷移失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = migrate_database()
    sys.exit(0 if success else 1)

