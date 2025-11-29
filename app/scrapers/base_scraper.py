"""
基礎爬蟲類
定義所有爬蟲的通用接口和功能
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import time
import random


class BaseScraper(ABC):
    """基礎爬蟲抽象類"""
    
    def __init__(self, output_dir: str = "data/scraped_content"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    @abstractmethod
    def scrape_products(self, search_terms: List[str]) -> List[Dict[str, Any]]:
        """爬取商品信息"""
        pass
    
    @abstractmethod
    def scrape_categories(self) -> List[Dict[str, Any]]:
        """爬取分類信息"""
        pass
    
    def save_results(self, data: Dict[str, Any], filename: str) -> Path:
        """保存爬取結果到文件"""
        filepath = self.output_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return filepath
    
    def add_delay(self, min_delay: float = 1.0, max_delay: float = 3.0):
        """添加隨機延遲"""
        time.sleep(random.uniform(min_delay, max_delay))
    
    def extract_product_features(self, product_name: str) -> Dict[str, str]:
        """從商品名稱中提取特徵（尺寸、顏色、材質等）"""
        import re
        
        features = {}
        
        # 提取尺寸
        size_match = re.search(r'(XS|S|M|L|XL|XXL|XXXL|\d+\.?\d*[xX]\d+\.?\d*)', product_name)
        if size_match:
            features['size'] = size_match.group(1)
        
        # 提取顏色
        color_match = re.search(r'(Black|White|Red|Blue|Green|Yellow|Pink|Purple|Orange|Brown|Gray|Grey|Navy|Beige|Cream)', product_name, re.I)
        if color_match:
            features['color'] = color_match.group(1)
        
        # 提取材質
        material_match = re.search(r'(Cotton|Polyester|Wool|Silk|Leather|Denim|Linen|Rayon|Spandex|Nylon)', product_name, re.I)
        if material_match:
            features['material'] = material_match.group(1)
        
        return features
    
    def create_description(self, product_name: str, features: Dict[str, str]) -> str:
        """創建商品描述"""
        desc_parts = []
        
        if features.get('size'):
            desc_parts.append(f"Size: {features['size']}")
        if features.get('color'):
            desc_parts.append(f"Color: {features['color']}")
        if features.get('material'):
            desc_parts.append(f"Material: {features['material']}")
        
        if desc_parts:
            return " | ".join(desc_parts)
        else:
            return product_name[:100] + "..." if len(product_name) > 100 else product_name
