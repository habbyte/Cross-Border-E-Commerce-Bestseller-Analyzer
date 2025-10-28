from typing import Iterable, List
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert
from app.db.models import Product, Category, ProductCategory, AuditLog
from app.db.session import SessionLocal, engine
from app.schemas.product import ProductIn, ProductWithCategories


def bulk_upsert_products(products: List[ProductIn]) -> int:
    if not products:
        return 0

    payload = [p.model_dump(mode="json") for p in products]
    with SessionLocal() as session:  # type: Session
        stmt = pg_insert(Product.__table__).values(payload)
        update_cols = {c.name: getattr(stmt.excluded, c.name)
                       for c in Product.__table__.columns
                       if c.name not in ("id", "created_at")}
        stmt = stmt.on_conflict_do_update(
            index_elements=["product_url", "name"],
            set_=update_cols
        )
        result = session.execute(stmt)
        session.commit()
        return len(payload)


def bulk_upsert_products_with_categories(data: List[ProductWithCategories], actor_user_id: int | None = None, run_id: str | None = None) -> int:
    if not data:
        return 0

    with SessionLocal() as session:  # type: Session
        # 1) upsert categories 先彙整
        cat_names = {}
        for item in data:
            for c in item.categories:
                if c.name not in cat_names:
                    cat_names[c.name] = c

        if cat_names:
            # 以 Pydantic JSON dump 轉成原生型別（HttpUrl -> str）
            cat_payload = [c.model_dump(mode="json") for c in cat_names.values()]
            stmt_cat = pg_insert(Category.__table__).values(cat_payload)
            stmt_cat = stmt_cat.on_conflict_do_update(
                index_elements=["name"],
                set_={"source_url": stmt_cat.excluded.source_url}
            )
            session.execute(stmt_cat)

        # 2) upsert products
        # 以 JSON dump 轉成原生型別（HttpUrl -> str）
        prod_payload = [i.product.model_dump(mode="json") for i in data]
        # 預設狀態與 run 標記
        for p in prod_payload:
            p.setdefault("status", "draft")
            if run_id:
                p["run_id"] = run_id
        stmt_prod = pg_insert(Product.__table__).values(prod_payload)
        update_cols = {c.name: getattr(stmt_prod.excluded, c.name)
                       for c in Product.__table__.columns
                       if c.name not in ("id", "created_at")}
        stmt_prod = stmt_prod.on_conflict_do_update(
            index_elements=["product_url", "name"],
            set_=update_cols
        )
        session.execute(stmt_prod)

        # 3) 建立 product_categories 關聯
        # 需要查 product 與 category 的 id
        # 取所有需要的名稱/URL
        from sqlalchemy import select

        def _norm_url(u):
            if u is None:
                return None
            return str(u)

        prod_keys = set((_norm_url(p.product.product_url), p.product.name) for p in data)
        q_products = select(Product.id, Product.product_url, Product.name)
        ids = session.execute(q_products).all()
        prod_key_to_id = {}
        for pid, purl, pname in ids:
            key = (_norm_url(purl), pname)
            if key in prod_keys:
                prod_key_to_id[key] = pid

        cat_needed = set(cat_names.keys()) if cat_names else set()
        q_cats = select(Category.id, Category.name)
        cat_rows = session.execute(q_cats).all()
        cat_name_to_id = {name: cid for cid, name in cat_rows if name in cat_needed or True}

        rel_payload = []
        for item in data:
            prod_id = prod_key_to_id.get((_norm_url(item.product.product_url), item.product.name))
            if not prod_id:
                continue
            for c in item.categories:
                cid = cat_name_to_id.get(c.name)
                if cid:
                    rel_payload.append({"product_id": prod_id, "category_id": cid})

        if rel_payload:
            stmt_rel = pg_insert(ProductCategory.__table__).values(rel_payload)
            stmt_rel = stmt_rel.on_conflict_do_nothing(index_elements=["product_id", "category_id"])
            session.execute(stmt_rel)

        # 4) 審計紀錄（批次）
        if prod_payload:
            logs = [{
                "entity_type": "product",
                "entity_id": 0,  # 無法逐一抓 id，這裡記錄批次行為
                "action": "upsert_draft",
                "detail": f"batch_size={len(prod_payload)}",
                "actor_id": actor_user_id,
            }]
            stmt_log = pg_insert(AuditLog.__table__).values(logs)
            session.execute(stmt_log)

        session.commit()
        return len(prod_payload)


