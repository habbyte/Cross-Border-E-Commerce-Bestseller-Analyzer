import hashlib
from typing import Any, Dict, Iterable, List
from app.schemas.product import ProductIn, CategoryIn, ProductWithCategories


def _parse_int_safe(text: str | None) -> int | None:
    if not text:
        return None
    try:
        return int(text.replace(",", "").strip())
    except Exception:
        return None


def _compute_hash(values: List[str | None]) -> str:
    hasher = hashlib.sha256()
    for v in values:
        hasher.update((v or "").encode("utf-8"))
        hasher.update(b"\x1f")
    return hasher.hexdigest()


def extract_products_from_result(result_obj: Any) -> List[ProductIn]:
    """將 Firecrawl 結果轉為標準化的 ProductIn 陣列。"""
    result_dict = result_obj.model_dump(exclude_none=True, mode="json")
    items = result_dict.get("data", [])

    products: List[ProductIn] = []
    for item in items:
        js = (item or {}).get("json") or {}
        meta = (item or {}).get("metadata") or {}
        source_url = meta.get("url")

        for p in (js.get("products") or []):
            name = p.get("name")
            if not name:
                continue

            review_count_text = p.get("review_count")
            core_values = [
                name,
                p.get("price"),
                str(p.get("rating") or ""),
                review_count_text,
                p.get("image_url"),
                p.get("product_url"),
                p.get("description"),
                source_url,
            ]
            content_hash = _compute_hash(core_values)

            products.append(ProductIn(
                name=name,
                price=p.get("price"),
                rating=p.get("rating"),
                review_count_text=review_count_text,
                review_count=_parse_int_safe(review_count_text),
                image_url=p.get("image_url"),
                product_url=p.get("product_url"),
                description=p.get("description"),
                source_url=source_url,
                content_hash=content_hash,
            ))
    return products


def extract_products_with_categories(result_obj: Any) -> List[ProductWithCategories]:
    """回傳每個 product 與該頁面 categories。"""
    result_dict = result_obj.model_dump(exclude_none=True, mode="json")
    items = result_dict.get("data", [])

    out: List[ProductWithCategories] = []
    for item in items:
        js = (item or {}).get("json") or {}
        meta = (item or {}).get("metadata") or {}
        source_url = meta.get("url")

        cats = []
        for c in (js.get("categories") or []):
            name = (c or {}).get("category_name") or (c or {}).get("name")
            if not name:
                continue
            cats.append(CategoryIn(name=name, source_url=source_url))

        for p in (js.get("products") or []):
            name = p.get("name")
            if not name:
                continue
            review_count_text = p.get("review_count")
            core_values = [
                name,
                p.get("price"),
                str(p.get("rating") or ""),
                review_count_text,
                p.get("image_url"),
                p.get("product_url"),
                p.get("description"),
                source_url,
            ]
            content_hash = _compute_hash(core_values)

            prod = ProductIn(
                name=name,
                price=p.get("price"),
                rating=p.get("rating"),
                review_count_text=review_count_text,
                review_count=_parse_int_safe(review_count_text),
                image_url=p.get("image_url"),
                product_url=p.get("product_url"),
                description=p.get("description"),
                source_url=source_url,
                content_hash=content_hash,
            )
            out.append(ProductWithCategories(product=prod, categories=cats))
    return out


