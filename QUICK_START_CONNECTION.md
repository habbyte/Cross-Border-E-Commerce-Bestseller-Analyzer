# 快速啟動：前端與數據庫串接

## 快速檢查清單

### 1. 後端設置（5 分鐘）

```bash
# 1. 確保有 .env 文件（項目根目錄）
# 包含 DATABASE_URL 等配置

# 2. 啟動後端 API
python run_api.py

# 應該看到：
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 2. 前端設置（2 分鐘）

```bash
# 1. 創建前端 .env 文件（項目根目錄）
echo "VITE_API_BASE_URL=http://localhost:8000" > .env

# 2. 啟動前端開發服務器
npm run dev

# 應該看到：
# VITE v5.x.x  ready in xxx ms
# ➜  Local:   http://localhost:3001/
```

### 3. 驗證連接（1 分鐘）

#### 方法 1: 使用測試腳本

```bash
# 在另一個終端運行
python scripts/test_api_connection.py
```

#### 方法 2: 手動測試

```bash
# 測試後端健康檢查
curl http://localhost:8000/health

# 測試產品 API
curl http://localhost:8000/api/products/?limit=5
```

#### 方法 3: 瀏覽器檢查

1. 打開瀏覽器開發者工具（F12）
2. 訪問前端頁面：http://localhost:3001
3. 查看 Network 標籤
4. 應該看到對 `/api/products/` 的請求
5. 檢查響應狀態碼（應該是 200）

## 常見問題

### Q: 前端顯示模擬數據而不是真實數據

**原因**：API 連接失敗，ProductService 回退到模擬數據

**解決方案**：
1. 確認後端 API 正在運行：`curl http://localhost:8000/health`
2. 檢查瀏覽器控制台的錯誤信息
3. 確認 `.env` 文件中的 `VITE_API_BASE_URL` 設置正確
4. 重啟前端開發服務器（環境變量更改需要重啟）

### Q: CORS 錯誤

**錯誤信息**：`Access to fetch at 'http://localhost:8000/...' from origin 'http://localhost:3001' has been blocked by CORS policy`

**解決方案**：
- 確認前端端口在 `app/api/main.py` 的 CORS 配置中
- 當前已配置：5173, 3000, 3001

### Q: 數據庫連接失敗

**錯誤信息**：`could not connect to server` 或 `database does not exist`

**解決方案**：
1. 檢查 `.env` 文件中的 `DATABASE_URL`
2. 確認 PostgreSQL 服務正在運行
3. 測試連接：`psql $DATABASE_URL`

### Q: API 返回空數組

**原因**：數據庫中沒有 `status='active'` 的產品

**解決方案**：
1. 檢查數據庫中的產品：
   ```sql
   SELECT COUNT(*) FROM products;
   SELECT COUNT(*) FROM products WHERE status = 'active';
   ```
2. 如果有產品但狀態不是 'active'，可以：
   - 修改 API 請求：`?status=all`
   - 或更新數據庫：`UPDATE products SET status = 'active' WHERE ...`

## 數據流程圖

```
┌─────────────┐
│  瀏覽器     │
│  (前端)     │
└──────┬──────┘
       │ HTTP Request
       │ GET /api/products/
       ▼
┌─────────────┐
│  FastAPI    │
│  (後端)     │
└──────┬──────┘
       │ SQL Query
       │ SELECT * FROM products
       ▼
┌─────────────┐
│ PostgreSQL  │
│  (數據庫)    │
└─────────────┘
```

## 下一步

- [ ] 確認數據庫中有測試數據
- [ ] 測試搜索功能
- [ ] 測試產品詳情頁面
- [ ] 測試過濾功能（平台、分類）

詳細文檔請參考：`docs/FRONTEND_BACKEND_CONNECTION.md`

