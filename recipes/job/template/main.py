#!/usr/bin/env python3
"""{{SERVICE_NAME}} — {{DESCRIPTION}}

由服務製造器（job 配方）scaffold。黃金路徑：排程 → 讀源 →(可選)Claude → 寫 GCS，自動硬化。
特定邏輯改 TODO 兩處：fetch_data()（你的查詢）與 build_prompt()（你的 Claude 指令）。

L2 硬化（已內建，勿拆）：idempotent（查輸出已存在則跳過）/ structured log / per-service SA。

環境變數：
  BQ_PROJECT / GCS_BUCKET / REPORT_TZ / REPORT_DATE(測試) / CLAUDE_MODEL / ANTHROPIC_API_KEY(Secret)
"""
import os
import sys
import json
import datetime
from zoneinfo import ZoneInfo

from google.cloud import bigquery
from google.cloud import storage
import anthropic

BQ_PROJECT = os.environ.get("BQ_PROJECT", "{{BQ_PROJECT}}")
BQ_DATASET = os.environ.get("BQ_DATASET", "{{BQ_DATASET}}")
GCS_BUCKET = os.environ.get("GCS_BUCKET", "")
REPORT_TZ = os.environ.get("REPORT_TZ", "{{TIMEZONE}}")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-4-8")
USES_AI = os.environ.get("USES_AI", "{{USES_AI}}").lower() == "true"


def log(level, msg, **kw):
    print(json.dumps({"severity": level, "message": msg, **kw}, ensure_ascii=False), flush=True)


def target_date():
    tz = ZoneInfo(REPORT_TZ)
    override = os.environ.get("REPORT_DATE")
    if override:
        return datetime.date.fromisoformat(override)
    return (datetime.datetime.now(tz) - datetime.timedelta(days=1)).date()


def fetch_data(bq, day):
    """TODO: 換成你的查詢。回你要的資料結構。跨專案唯讀來源已由 IAM 授權。"""
    sql = f"""
        SELECT *
        FROM `{BQ_PROJECT}.{BQ_DATASET}.daily_report`
        WHERE day = @day
    """
    cfg = bigquery.QueryJobConfig(query_parameters=[
        bigquery.ScalarQueryParameter("day", "DATE", day)])
    return [dict(r.items()) for r in bq.query(sql, job_config=cfg).result()]


def build_prompt(day, data):
    """TODO: 換成你要給 Claude 的指令。回 prompt 字串。"""
    return f"以下是 {day} 的資料，請寫一段給主管的重點摘要（繁中，直接給結論）：\n{json.dumps(data, ensure_ascii=False, default=str)}"


def render_html(day, data, digest):
    def esc(s):
        return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    body = f"<h2>今日重點</h2><p>{esc(digest).replace(chr(10), '<br>')}</p>" if digest else ""
    return (f"<h1>{{SERVICE_NAME}} {day}</h1>{body}"
            f"<h2>資料</h2><pre>{esc(json.dumps(data, ensure_ascii=False, indent=2, default=str))}</pre>"
            f"<p><small>自動產生 by {{SERVICE_NAME}}（服務製造器 job 配方）</small></p>")


def object_name(day):
    return f"reports/{day}.html"


def main():
    if not GCS_BUCKET:
        log("ERROR", "GCS_BUCKET 未設定"); sys.exit(1)
    day = target_date()
    log("INFO", "start", date=str(day), bq_project=BQ_PROJECT, model=CLAUDE_MODEL if USES_AI else None)

    gcs = storage.Client()
    blob = gcs.bucket(GCS_BUCKET).blob(object_name(day))
    if blob.exists():   # idempotent：防 retry 重複
        log("INFO", "already_exists_skip", date=str(day), object=object_name(day)); return

    bq = bigquery.Client()
    data = fetch_data(bq, day)
    log("INFO", "fetched", date=str(day), rows=len(data) if hasattr(data, "__len__") else None)

    digest = ""
    if USES_AI and data:
        client = anthropic.Anthropic()
        resp = client.messages.create(model=CLAUDE_MODEL, max_tokens=1500,
            messages=[{"role": "user", "content": build_prompt(day, data)}])
        digest = "".join(b.text for b in resp.content if b.type == "text").strip()

    html = render_html(day, data, digest)
    blob.upload_from_string(html, content_type="text/html; charset=utf-8")
    link = f"https://storage.cloud.google.com/{GCS_BUCKET}/{object_name(day)}"
    log("INFO", "created", date=str(day), gcs=f"gs://{GCS_BUCKET}/{object_name(day)}", link=link)


if __name__ == "__main__":
    main()
