#!/usr/bin/env python3
"""
Amazon 爬蟲主入口點
"""

import sys
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from scripts.run_cli import main

if __name__ == "__main__":
    main()
