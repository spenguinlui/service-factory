# 服務包產生 Plugin（非工程師）

純 skill 殼：讓非工程師用對話把「已驗證好用的東西」固化成**服務包資料夾**——到此為止。
**不含任何 connector**（非工程師不需要連任何 server、不需要任何授權）。

- `.claude-plugin/plugin.json` — manifest
- `skills/make-service/SKILL.md` — 對話流程（畢業判斷 → 收參數 → 產包 → 交付工程師）

## 流程
1. 平常直接請 Claude 做（一次性，不產包）。
2. 用順了、要固定 → 說「幫我變成每天自動跑的服務」→ Claude 產出服務包資料夾。
3. 把資料夾**交給工程師**：工程師用部署器（私有 service-deployer）驗證、部署、登記。

## 佈署給同仁
私有 plugin marketplace / 手動安裝皆可；因為不含 connector 與 secret，佈署零風險。
