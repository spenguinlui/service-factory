# {{SERVICE_NAME}}

{{DESCRIPTION}}

由**服務製造器** job 配方 scaffold（archetype=`job`）。

- **排程**：`{{SCHEDULE}}`（{{TIMEZONE}}）
- **資料源**：`{{BQ_PROJECT}}` BigQuery（跨專案唯讀）
- **輸出**：GCS bucket → `reports/YYYY-MM-DD.html`
- **AI**：{{USES_AI}}（Claude，`CLAUDE_MODEL` 可調）
- **部署**：Cloud Run Job + Cloud Scheduler（project 由部署器決定）
- **data_class**：`{{DATA_CLASS}}`

## 要改的兩處
- `fetch_data()` — 你的查詢
- `build_prompt()` — 你給 Claude 的指令（不用 AI 就把 uses_ai 設 false）

## 本機測試
```bash
pip install -r requirements.txt
export GCS_BUCKET=... ANTHROPIC_API_KEY=... REPORT_DATE=2026-06-24
python main.py
```

## L2 硬化（已內建）
idempotent（查輸出已存在則跳過）/ structured JSON log / per-service SA least-priv。
