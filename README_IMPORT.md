# 數據導入與 API 使用指南

## 快速開始

### 1. 安裝依賴

```bash
pip install -r requirements.txt
```

### 2. 配置環境變量

創建 `.env` 文件：

```env
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
VITE_API_BASE_URL=http://localhost:8000
```

### 3. 更新數據庫結構

執行 SQL 添加新字段（如果還沒有執行遷移）：

```sql
ALTER TABLE products 
ADD COLUMN IF NOT EXISTS category_path TEXT,
ADD COLUMN IF NOT EXISTS bought_in_past_month VARCHAR,
ADD COLUMN IF NOT EXISTS product_details JSONB,
ADD COLUMN IF NOT EXISTS about_this_item JSONB,
ADD COLUMN IF NOT EXISTS color_options JSONB,
ADD COLUMN IF NOT EXISTS size_options JSONB,
ADD COLUMN IF NOT EXISTS platform VARCHAR;
```

### 4. 導入數據

```bash
python scripts/import_enhanced_json.py data/scraped_content/amazon_enhanced.json --run-id "import-$(date +%Y-%m-%d)"
```

### 5. 啟動 API 服務器

```bash
python run_api.py
```

API 將在 `http://localhost:8000` 啟動。

### 6. 啟動前端

```bash
npm run dev
```

前端會自動從 API 加載數據。

## API 文檔

啟動 API 後，訪問 `http://localhost:8000/docs` 查看 Swagger API 文檔。

### 主要端點

- `GET /api/products/` - 獲取產品列表
- `GET /api/products/{product_id}` - 獲取產品詳情
- `GET /api/products/stats/summary` - 獲取統計信息

## 數據流程

```
amazon_enhanced.json
    ↓
enhanced_adapter.py (轉換格式)
    ↓
import_enhanced_json.py (導入數據庫)
    ↓
PostgreSQL 數據庫
    ↓
FastAPI (提供 API)
    ↓
前端 ProductService (從 API 讀取)
    ↓
Vue 組件顯示
```

## 故障排除

### 導入失敗

檢查數據庫連接和 JSON 文件格式。

### API 無法訪問

1. 確認 API 服務器正在運行
2. 檢查 CORS 配置
3. 查看 API 日誌

### 前端顯示舊數據

1. 清除瀏覽器緩存
2. 檢查瀏覽器控制台
3. 確認 API 返回正確數據

## 下一步

- 添加更多過濾選項
- 實現實時數據更新
- 添加產品詳情頁面
- 實現產品對比功能

