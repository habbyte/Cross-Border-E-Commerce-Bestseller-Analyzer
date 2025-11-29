#!/usr/bin/env python3
"""
重建 .env 文件，修复编码问题
"""

import sys
from pathlib import Path

print("=" * 70)
print("重建 .env 文件")
print("=" * 70)

env_file = Path(".env")
backup_file = Path(".env.backup")

# 备份原文件
if env_file.exists():
    try:
        # 尝试读取现有配置
        encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1', 'cp1252']
        existing_config = {}
        
        for encoding in encodings:
            try:
                with open(env_file, 'r', encoding=encoding) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            existing_config[key.strip()] = value.strip()
                print(f"   成功读取现有配置（使用 {encoding} 编码）")
                break
            except:
                continue
        
        # 备份
        import shutil
        shutil.copy(env_file, backup_file)
        print(f"   ✓ 已备份到: {backup_file}")
    except Exception as e:
        print(f"   ⚠ 无法备份: {e}")

# 重建 .env 文件
print("\n重建 .env 文件...")

# 必需的配置（从现有配置中获取或使用默认值）
new_config = {
    "MONGODB_DATABASE": existing_config.get("MONGODB_DATABASE", "data"),
    "MONGODB_URL": existing_config.get("MONGODB_URL", ""),
    "DATABASE_URL": existing_config.get("DATABASE_URL", ""),
    "FIRECRAWL_API_KEY": existing_config.get("FIRECRAWL_API_KEY", ""),
}

# 添加其他配置（如果存在）
for key, value in existing_config.items():
    if key not in new_config:
        new_config[key] = value

# 写入新文件（UTF-8 编码）
try:
    with open(env_file, 'w', encoding='utf-8', newline='\n') as f:
        f.write("# MongoDB 配置\n")
        f.write(f"MONGODB_URL={new_config.get('MONGODB_URL', '')}\n")
        f.write(f"MONGODB_DATABASE={new_config.get('MONGODB_DATABASE', 'data')}\n")
        f.write("\n# PostgreSQL 配置\n")
        f.write(f"DATABASE_URL={new_config.get('DATABASE_URL', '')}\n")
        f.write("\n# Firecrawl 配置\n")
        f.write(f"FIRECRAWL_API_KEY={new_config.get('FIRECRAWL_API_KEY', '')}\n")
        
        # 添加其他配置
        other_keys = [k for k in new_config.keys() if k not in ['MONGODB_URL', 'MONGODB_DATABASE', 'DATABASE_URL', 'FIRECRAWL_API_KEY']]
        if other_keys:
            f.write("\n# 其他配置\n")
            for key in other_keys:
                f.write(f"{key}={new_config[key]}\n")
    
    print(f"   ✓ .env 文件已重建（UTF-8 编码）")
    print(f"   MONGODB_DATABASE={new_config.get('MONGODB_DATABASE', 'data')}")
    
except Exception as e:
    print(f"   ❌ 无法写入 .env 文件: {e}")
    sys.exit(1)

print("\n" + "=" * 70)
print("完成！请重启后端服务器")
print("=" * 70)

