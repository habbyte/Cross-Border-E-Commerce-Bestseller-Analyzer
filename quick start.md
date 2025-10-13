
# Amazon Category Crawler — Local Dev & Calling Guide

This README explains **exactly how to run and call the API locally**, how to open the **static Swagger UI**, and how to test with **cURL** and **Postman**.

---

## 0) Prerequisites
- Python 3.9+ (3.11 tested)
- (Recommended) `virtualenv` or `venv`
- Internet access if you plan to perform real crawling via Firecrawl

---

## 1) Setup & Install

### 1.1 Create & activate a virtual environment
**macOS / Linux**
```bash
python -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell)**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

> If you also use conda, make sure you **deactivate** base before activating the venv:
> ```bash
> conda deactivate
> conda deactivate
> ```

### 1.2 Install dependencies
```bash
pip install -r requirements.txt
```

### 1.3 (Optional for real crawling) Configure Firecrawl API Key
Create a `.env` (or export in shell) with your key:
```bash
# macOS / Linux
export FIRECRAWL_API_KEY=fc-xxxxxxxxxxxxxxxx

# Windows (PowerShell)
$env:FIRECRAWL_API_KEY="fc-xxxxxxxxxxxxxxxx"
```
> If you only want to test the API shape/flow, you can run in mock mode (see _api.py_).

---

## 2) Run the API Locally (FastAPI)

Start the server:
```bash
# Prefer this form to ensure you use the venv's interpreter
python -m uvicorn api:app --reload --port 8000
# or explicitly
# .venv/bin/uvicorn api:app --reload --port 8000
```

You should see:
```
Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### 2.1 Verify the server is up
- Swagger UI (dynamic): http://127.0.0.1:8000/docs
- Health check:
  ```bash
  curl http://127.0.0.1:8000/health
  ```

---

## 3) Call the API Locally

### 3.1 `POST /crawl/category` — Crawl a single category
Query params:
- `category_url` **(required)** — The Amazon category/search URL to crawl
- `limit` (default 100) — Max items to discover/scrape (1–500)
- `max_discovery_depth` (default 1) — Link depth (0–3)

**Example (Kitchen & Dining node)**:
```bash
curl -X POST "http://127.0.0.1:8000/crawl/category?category_url=https://www.amazon.com/b/?node=1055398&limit=100&max_discovery_depth=1"
```

**Example (search results — air fryer)**:
```bash
curl -X POST "http://127.0.0.1:8000/crawl/category?category_url=https://www.amazon.com/s?k=air+fryer&limit=50&max_discovery_depth=1"
```

**Expected Response shape (CrawlResult):**
```json
{
  "products": [
    {
      "name": "…",
      "price": "…",
      "rating": 4.6,
      "review_count": "3,806",
      "image_url": "…",
      "product_url": "…",
      "description": "…"
    }
  ],
  "categories": [
    { "category_name": "Kitchen & Dining", "product_count": 120 }
  ],
  "metadata": { "source": "amazon", "limit": 100 }
}
```

> If you see a fixed `"Example Product"` in response, you're still running in **mock mode** — confirm your `FIRECRAWL_API_KEY` is set and restart the server.

---

### 3.2 `POST /crawl/batch` — Crawl multiple categories at once
Request body (JSON):
```json
{
  "category_urls": [
    "https://www.amazon.com/Best-Sellers/zgbs",
    "https://www.amazon.com/b/?node=1055398",
    "https://www.amazon.com/s?k=laptop"
  ],
  "limit": 80
}
```

**cURL**
```bash
curl -X POST "http://127.0.0.1:8000/crawl/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "category_urls": [
      "https://www.amazon.com/Best-Sellers/zgbs",
      "https://www.amazon.com/b/?node=1055398",
      "https://www.amazon.com/s?k=laptop"
    ],
    "limit": 80
  }'
```

Response is a **map of URL → CrawlResult**, e.g.:
```json
{
  "https://www.amazon.com/b/?node=1055398": {
    "products": [ { "name": "…", "price": "…" } ],
    "categories": [ { "category_name": "Kitchen & Dining" } ]
  },
  "https://www.amazon.com/s?k=laptop": {
    "products": [ { "name": "…", "price": "…" } ]
  }
}
```

---

### 3.3 `GET /cache/products` — Read existing cached results
Reads from `scraped_content/amazon_content.json`.

Optional query param:
- `category_keyword` — Filter categories by a case-insensitive keyword

**cURL**
```bash
curl "http://127.0.0.1:8000/cache/products?category_keyword=Kitchen"
```

**Tip:** This endpoint is useful for UI prototyping — no crawling needed.

---

### 3.4 `GET /health` — Health check
```bash
curl http://127.0.0.1:8000/health
```

---

## 4) Static Swagger UI (Optional)

If you prefer a **static, front-end–only** Swagger UI (no backend rendering), use the provided `index.html`:

```bash
# run a local static server in the folder containing index.html & openapi.yaml
python -m http.server 5500
# then open:
# http://127.0.0.1:5500
```

- The **Try it out** button will call the API base defined in `openapi.yaml -> servers`.
- Edit `openapi.yaml` to switch between `localhost`, `staging`, `production`, e.g.:
  ```yaml
  servers:
    - url: http://127.0.0.1:8000
      description: Local Dev
    - url: https://api.example.com
      description: Production
  ```

> If calling from a browser running on a different origin, make sure your API enables CORS for that origin (see `api.py` example with `CORSMiddleware`).

---

## 5) Postman Usage

Import both:
- `postman_collection.json`
- `postman_environment.json`

Select environment **Amazon Crawler Local** and run requests in order:
1. **Health** → `GET {{baseUrl}}/health`
2. **Crawl Category** → `POST {{baseUrl}}/crawl/category?...`
3. **Batch Crawl** → `POST {{baseUrl}}/crawl/batch`
4. **Read Cached** → `GET {{baseUrl}}/cache/products?category_keyword={{category_keyword}}`

---

## 6) Troubleshooting

- **`ModuleNotFoundError: No module named 'firecrawl'`**  
  You’re likely using the wrong interpreter (e.g., conda). Activate the venv and start with:
  ```bash
  python -m uvicorn api:app --reload --port 8000
  ```

- **Got 404 at `/`**  
  Normal — there is no root route. Go to `/docs` or add a redirect in `api.py`:
  ```python
  from fastapi.responses import RedirectResponse
  @app.get("/")
  def root(): return RedirectResponse(url="/docs")
  ```

- **Always getting `Example Product`**  
  You are in mock mode. Set `FIRECRAWL_API_KEY` and restart the server.

- **CORS errors from browser**  
  Add `CORSMiddleware` in `api.py` with appropriate `allow_origins`.

- **Cache endpoint 404**  
  Ensure `scraped_content/amazon_content.json` exists and path is correct.

---

## 7) Useful Snippets

### Enable CORS (when calling from a different origin)
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Run Uvicorn with explicit venv binary
```bash
.venv/bin/uvicorn api:app --reload --port 8000
```

---

Happy crawling! 🕸️
