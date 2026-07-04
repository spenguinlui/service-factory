# {{SERVICE_NAME}}

{{DESCRIPTION}}

由**服務製造器** service 配方 scaffold（archetype=`service`）。Cloud Run HTTP 服務。

- **runtime**：Cloud Run service（常駐、無 scheduler）
- **框架**：FastAPI + uvicorn
- **認證**：預設 `--no-allow-unauthenticated`
- **健康檢查**：`GET /health`
- **AI**：{{USES_AI}}（Claude，可選）

## 要改的
- `main.py` 的 `/` 或你自己的端點邏輯。

## 本機測試
```bash
pip install -r requirements.txt
uvicorn main:app --port 8080
curl localhost:8080/health
```
