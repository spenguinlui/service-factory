# service-factory — 服務包產生器

用對話（或 CLI）把「我想要一個每天自動…的服務」變成一個**符合規範的服務包資料夾**——到此為止。
**零雲端依賴**（無 gcloud / Gitea / GCS / 網路），可完全本機離線跑。

提交、部署、登記＝**部署器**的事（`service-deployer`，私有、工程師專用）。
兩者唯一的合約＝**bundle spec v1**：見 public repo
`ai-infra-management/docs/service-factory/bundle-spec.md`。

> 狀態：私有開發中；spec 穩定 + 安全審查（R4）後翻 public。
> 架構背景：`ai-infra-management/docs/service-factory/target-architecture.md`（ADR 0007）。

## 用法

```bash
pip install pyyaml
python3 generator.py my-service --out . \
  --params '{"archetype":"job","description":"每天…","owner":"you@sunnyfounder.com"}'
```

產出 `./my-service/`＝配方模板 render + `service.yaml`，並跑**禮貌性預檢**
（vendored `registry_contract.py`；部署器收包會 re-validate，那才是權威）。

## 內容
- `generator.py` — 產生器本體（CLI）
- `recipes/<archetype>/` — 配方（`job`、`service`；recipe.yaml 選型 + template/ 骨架）
- `plugin/` — Cowork/Claude Code plugin（非工程師對話殼；連接與提交流程 R5 更新）
- `registry_contract.py` — 【vendored】合約 validator 副本；**正典在 ai-infra-management**，spec 變動須同步

## org 預設（org-defaults.yaml）
公開 repo 不含任何組織內部值。你的組織預設（資料源專案、dataset、典型服務鏈邊）放
`org-defaults.yaml`（已 gitignore）或以 `GENERATOR_ORG_DEFAULTS` 指定路徑；範例見
`org-defaults.example.yaml`。沒有 org 檔也能用——把 `edges`/`bq_project` 等直接放 `--params`。
合併順序：內建通用值 < org-defaults < --params。

## 設計原則
- 產生器**沒有任何權力**（不碰雲端、不持 secret）→ 才能公開、去中心化。
- 「先用、用順了再固定」：日常一次性需求別產生服務；確定要**定期自動跑**才產包提交。
