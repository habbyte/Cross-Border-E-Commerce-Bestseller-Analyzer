# Static Swagger UI for Amazon Category Crawler API

This folder contains a **static** Swagger UI that renders your `openapi.yaml`.
It gives you the same experience as FastAPI's `/docs` page, including **Try it out**.

## How to preview locally

```bash
# from this folder
python -m http.server 5500
# then open http://localhost:5500
```

> The "Try it out" button will call whatever base URL is defined in `openapi.yaml -> servers[0].url`.
> By default it's `http://localhost:8000`. Change it to your dev/staging/prod as needed.

## Deploy to GitHub Pages

1. Create a new repo (or a `docs/` folder in an existing one).
2. Commit these files (`index.html` and `openapi.yaml`).
3. In GitHub: Settings → Pages → Source: `main` branch (root or `/docs`).
4. Visit the provided URL to see the interactive docs online.

## Files

- `index.html` — static Swagger UI loader
- `openapi.yaml` — the API contract (already prepared)