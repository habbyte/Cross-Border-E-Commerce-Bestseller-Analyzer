#!/usr/bin/env python3
"""
修复数据库配置，切换到 data 数据库
"""

import sys
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=" * 70)
print("修复数据库配置")
print("=" * 70)

# 读取 .env 文件
env_file = Path(".env")
if not env_file.exists():
    print("❌ .env 文件不存在")
    sys.exit(1)

# 读取文件内容（尝试多种编码）
encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1', 'cp1252']
lines = None
used_encoding = None

for encoding in encodings:
    try:
        with open(env_file, 'r', encoding=encoding) as f:
            lines = f.readlines()
            used_encoding = encoding
            print(f"   使用编码: {encoding}")
            break
    except (UnicodeDecodeError, UnicodeError):
        continue

if lines is None:
    print("❌ 无法读取 .env 文件（编码问题）")
    sys.exit(1)

# 修改 MONGODB_DATABASE
modified = False
new_lines = []
for line in lines:
    if line.startswith("MONGODB_DATABASE="):
        old_value = line.strip().split("=", 1)[1]
        if old_value != "data":
            print(f"   发现: MONGODB_DATABASE={old_value}")
            new_lines.append("MONGODB_DATABASE=data\n")
            modified = True
            print(f"   修改为: MONGODB_DATABASE=data")
        else:
            new_lines.append(line)
            print(f"   ✓ 已经是: MONGODB_DATABASE=data")
    else:
        new_lines.append(line)

# 如果没有找到 MONGODB_DATABASE，添加它
if not any("MONGODB_DATABASE" in line for line in lines):
    new_lines.append("MONGODB_DATABASE=data\n")
    modified = True
    print("   添加: MONGODB_DATABASE=data")

# 写回文件（使用 UTF-8 编码）
if modified:
    try:
        with open(env_file, 'w', encoding='utf-8', newline='\n') as f:
            f.writelines(new_lines)
        print("\n✓ .env 文件已更新（使用 UTF-8 编码）")
    except Exception as e:
        print(f"\n❌ 无法写入 .env 文件: {e}")
        sys.exit(1)
else:
    print("\n✓ 配置已经是正确的")

print("\n" + "=" * 70)
print("修复完成！请重启后端服务器以使配置生效")
print("=" * 70)
print("\n重启命令: python run_api.py")

