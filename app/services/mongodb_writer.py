from typing import List, Dict, Any
from app.schemas.product import ProductWithCategories
from app.db.mongodb import mongodb
from datetime import datetime


def bulk_upsert_products_mongodb(data: List[ProductWithCategories], run_id: str | None = None) -> int:
    """將產品資料寫入 MongoDB"""
    if not data:
        return 0
    
    db = mongodb.connect()
    if not db:
        print("MongoDB 未設定，跳過 MongoDB 寫入")
        return 0
    
    try:
        products_collection = db["products"]
        categories_collection = db["categories"]
        
        # 1) 處理分類
        category_names = set()
        for item in data:
            for cat in item.categories:
                category_names.add(cat.name)
        
        # 建立分類文件
        for cat_name in category_names:
            categories_collection.update_one(
                {"name": cat_name},
                {"$set": {"name": cat_name, "updated_at": datetime.utcnow()}},
                upsert=True
            )
        
        # 2) 處理產品
        products_to_insert = []
        for item in data:
            product_doc = {
                "name": item.product.name,
                "price": item.product.price,
                "rating": item.product.rating,
                "review_count_text": item.product.review_count_text,
                "review_count": item.product.review_count,
                "image_url": str(item.product.image_url) if item.product.image_url else None,
                "product_url": str(item.product.product_url) if item.product.product_url else None,
                "description": item.product.description,
                "source_url": str(item.product.source_url) if item.product.source_url else None,
                "content_hash": item.product.content_hash,
                "status": "draft",
                "run_id": run_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "categories": [cat.name for cat in item.categories]
            }
            products_to_insert.append(product_doc)
        
        # 3) 批量 upsert 產品
        for product in products_to_insert:
            products_collection.update_one(
                {
                    "product_url": product["product_url"],
                    "name": product["name"]
                },
                {
                    "$set": {
                        **product,
                        "updated_at": datetime.utcnow()
                    },
                    "$setOnInsert": {
                        "created_at": product["created_at"]
                    }
                },
                upsert=True
            )
        
        return len(products_to_insert)
        
    except Exception as e:
        print(f"MongoDB 寫入錯誤: {e}")
        return 0
    finally:
        mongodb.close()
