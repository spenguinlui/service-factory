#!/usr/bin/env python3
"""{{SERVICE_NAME}} — {{DESCRIPTION}}

由服務製造器（service 配方）scaffold。Cloud Run HTTP 服務（FastAPI）。
改 TODO：你的端點邏輯。健康檢查 /health 已內建（勿拆）。

環境變數：PORT（Cloud Run 注入）/ BQ_PROJECT / CLAUDE_MODEL / ANTHROPIC_API_KEY(Secret) / USES_AI
"""
import os
import json
from fastapi import FastAPI

USES_AI = os.environ.get("USES_AI", "{{USES_AI}}").lower() == "true"
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-4-8")

app = FastAPI(title="{{SERVICE_NAME}}")


def log(level, msg, **kw):
    print(json.dumps({"severity": level, "message": msg, **kw}, ensure_ascii=False), flush=True)


@app.get("/health")
def health():
    return {"status": "ok", "service": "{{SERVICE_NAME}}"}


@app.get("/")
def root():
    # TODO: 換成你的端點邏輯
    log("INFO", "hit_root")
    return {"service": "{{SERVICE_NAME}}", "description": "{{DESCRIPTION}}", "uses_ai": USES_AI}


# 範例：需要 Claude 時（uses_ai=true）
# from anthropic import Anthropic
# @app.post("/ask")
# def ask(q: dict):
#     r = Anthropic().messages.create(model=CLAUDE_MODEL, max_tokens=800,
#             messages=[{"role":"user","content": q["text"]}])
#     return {"answer": "".join(b.text for b in r.content if b.type=="text")}
