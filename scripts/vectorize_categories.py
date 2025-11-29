#!/usr/bin/env python3
"""
向量化类别数据脚本
从 categories.csv 加载数据，进行向量化，并保存结果
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.vector_service import vector_service
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """主函数"""
    # 默认路径
    csv_path = project_root / "categories.csv"
    output_path = project_root / "data" / "vectorized_categories.json"
    
    # 检查 CSV 文件是否存在
    if not csv_path.exists():
        logger.error(f"CSV 文件不存在: {csv_path}")
        logger.info("请确保 categories.csv 文件在项目根目录")
        return 1
    
    try:
        logger.info(f"开始加载类别数据: {csv_path}")
        categories = vector_service.load_categories_from_csv(str(csv_path))
        
        if not categories:
            logger.error("未找到类别数据")
            return 1
        
        logger.info(f"开始向量化 {len(categories)} 条数据...")
        vectorized_categories = vector_service.vectorize_categories(categories)
        
        if not vectorized_categories:
            logger.error("向量化失败")
            return 1
        
        logger.info(f"保存向量化数据到: {output_path}")
        vector_service.save_vectorized_data(vectorized_categories, str(output_path))
        
        logger.info("✓ 向量化完成！")
        logger.info(f"  - 总数据量: {len(categories)}")
        logger.info(f"  - 成功向量化: {len(vectorized_categories)}")
        logger.info(f"  - 输出文件: {output_path}")
        
        return 0
    
    except Exception as e:
        logger.error(f"向量化过程出错: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())

