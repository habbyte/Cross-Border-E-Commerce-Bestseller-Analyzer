# Cross-Border-E-Commerce-Bestseller-Analyzer

## 環境變數

請建立 `.env` 檔或以系統環境變數方式提供：

```
# Firecrawl
FIRECRAWL_API_KEY=fc-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# PostgreSQL (本地)
DATABASE_URL=postgresql+psycopg://<user>:<password>@<host>:5432/<database>

# MongoDB Atlas (雲端，可選)
MONGODB_URL=mongodb+srv://<user>:<password>@<cluster>.mongodb.net/
MONGODB_DATABASE=amazon_products
```

本專案已使用 `pydantic-settings` 讀取 `.env`。

## 依賴安裝

```
pip install sqlalchemy psycopg[binary] pydantic-settings python-dotenv
```

## 執行

```
python crawl_app.py
```

執行後會：
- 呼叫 Firecrawl 取得 Amazon 首頁資料
- 將結果存成 `scraped_content/amazon_content.json`
- 建立資料表（若不存在）並 upsert 寫入 PostgreSQL 的 `products` 表
- 同時寫入 MongoDB Atlas（如果設定了 `MONGODB_URL`）
