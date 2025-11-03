# 快速啟動指南

## 問題：商品管理頁面沒有數據

如果商品管理頁面沒有顯示數據，請按以下步驟檢查：

### 1. 確認數據庫遷移已完成

```bash
python scripts/migrate_database.py
```

這會添加所有必需的字段（`status`, `created_by`, `updated_by`, `run_id`, `platform` 等）。

### 2. 確認數據已導入

```bash
python scripts/import_enhanced_json.py data/scraped_content/amazon_enhanced.json
```

應該看到 "成功導入 X 個產品" 的消息。

### 3. 啟動 API 服務器

```bash
python run_api.py
```

API 將在 `http://localhost:8000` 啟動。

### 4. 測試 API

在瀏覽器中訪問：
- `http://localhost:8000/api/products/` - 查看產品列表
- `http://localhost:8000/docs` - 查看 API 文檔

### 5. 配置前端環境變量

確保 `.env` 文件包含（或在 `vite.config.js` 中配置）：

```env
VITE_API_BASE_URL=http://localhost:8000
```

### 6. 啟動前端

```bash
npm run dev
```

### 7. 檢查瀏覽器控制台

打開瀏覽器開發者工具（F12），查看：
- Console 標籤：是否有錯誤信息
- Network 標籤：檢查 `/api/products/` 請求是否成功

### 常見問題

#### API 返回 500 錯誤

1. 檢查數據庫連接是否正常
2. 確認所有字段都已遷移（運行 `migrate_database.py`）
3. 查看 API 服務器的終端輸出，查看具體錯誤

#### 前端顯示 "Failed to load products from API"

1. 確認 API 服務器正在運行
2. 檢查 `VITE_API_BASE_URL` 環境變量
3. 檢查瀏覽器控制台的 CORS 錯誤
4. 確認 API 端點返回正確的 JSON 格式

#### 數據庫字段缺失錯誤

運行遷移腳本：
```bash
python scripts/migrate_database.py
```

#### 前端回退到模擬數據

這是正常的後備機制。如果 API 不可用，前端會自動使用模擬數據。

要強制使用 API：
1. 確保 API 服務器運行
2. 清除瀏覽器緩存
3. 檢查網絡請求是否成功

