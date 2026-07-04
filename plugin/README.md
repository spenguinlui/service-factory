# 服務製造器 Plugin（Cowork，非工程師）

薄殼 plugin：讓非工程師用對話做出/維護 `job` 服務。重邏輯與強制在工廠 MCP server 側。

## 結構
- `.claude-plugin/plugin.json` — manifest
- `.mcp.json` — 綁 remote 工廠 MCP connector（`streamable-http`）
- `skills/make-service/SKILL.md` — 對話流程（薄）

## 安裝前提
1. **工廠 remote MCP server 已部署**，把 `.mcp.json` 的 `url` 換成實際 Cloud Run URL（`https://.../mcp`）。
2. connector 認證接上（OAuth / IAP），server 才拿得到使用者身分做蓋章。

## 佈署路徑（現實）
- Claude Code **尚未 GA**「組織管理員一鍵預推 MCP 給全 org」。現階段用**私有 plugin marketplace**（私有 git repo）讓成員 `claude plugin install`，或 project-scope `.mcp.json`。
- 待 Managed scope GA 再改為管理員預推。

## 安全
工廠能建 repo / 部署 / 改 IAM / 登記——remote 上線前**必先鎖好身分驗證**（`--no-allow-unauthenticated` + IAP/OAuth；server 讀認證 header 當 actor，禁匿名）。
