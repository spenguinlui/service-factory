#!/usr/bin/env python3
"""generator.py — 服務包產生器（R2，ADR 0007）

把配方 render 成「服務包」資料夾（bundle spec v1）——**到此為止**。
零雲端依賴（無 gcloud / Gitea / GCS / 網路）：可完全本機離線跑。
R3 會抽成獨立 repo、R4 審查後翻 public；提交/部署/登記＝部署器的事
（factory.py submit_bundle / deploy / register，工程師專用、私有）。

用法：
  python3 generator.py <name> --out <dir> \
    --params '{"archetype":"job","description":"...","owner":"you@sunnyfounder.com"}'

產出：<out>/<name>/ ＝ 配方模板 render + service.yaml（合約見 docs/service-factory/bundle-spec.md）。
產出後跑禮貌性預檢（registry_contract.validate_bundle）；部署器收包會 re-validate（權威）。
"""
import os
import re
import sys
import json

HERE = os.path.dirname(os.path.abspath(__file__))
RECIPES = os.path.join(HERE, "recipes")
NAME_RE = re.compile(r"^[a-z][a-z0-9-]{1,38}[a-z0-9]$")

# 通用預設。org 專屬預設（資料源專案/dataset/典型邊）放 org-defaults.yaml（gitignore；
# 範例見 org-defaults.example.yaml；本 org 真實檔存私有 service-deployer repo org/）。
DEFAULTS = {"archetype": "job", "description": "", "schedule": "0 8 * * *",
            "timezone": "Asia/Taipei", "uses_ai": False, "bq_project": "",
            "bq_dataset": "", "data_class": "internal"}
ORG_DEFAULTS_FILE = os.environ.get("GENERATOR_ORG_DEFAULTS", os.path.join(HERE, "org-defaults.yaml"))


def _org_defaults():
    if os.path.isfile(ORG_DEFAULTS_FILE):
        try:
            import yaml
            with open(ORG_DEFAULTS_FILE) as f:
                d = yaml.safe_load(f) or {}
            if isinstance(d, dict):
                return d
        except Exception:
            pass
    return {}


def _render(text, params):
    for k, v in params.items():
        text = text.replace("{{" + k.upper() + "}}", str(v))
    return text


def list_archetypes():
    if not os.path.isdir(RECIPES):
        return []
    return sorted(d for d in os.listdir(RECIPES)
                  if os.path.isdir(os.path.join(RECIPES, d, "template")))


def build_manifest(name, params):
    """params → service.yaml dict（bundle spec v1）。"""
    arch = params["archetype"]
    m = {"bundle_spec": "v1", "name": name, "archetype": arch,
         "description": params.get("description", ""),
         "owner": params.get("owner", ""),
         "governance": {"data_class": params.get("data_class", "internal"),
                        "uses_ai": bool(params.get("uses_ai", False)),
                        "criticality": params.get("criticality", "low")},
         "edges": params.get("edges") or ([
             {"to": params["edge_to"], "type": params.get("edge_type", "reads-data")}]
             if params.get("edge_to") else [])}
    if params.get("title"):
        m["title"] = params["title"]
    if arch == "job":
        m["runtime"] = {"schedule": params.get("schedule", "0 8 * * *"),
                        "timezone": params.get("timezone", "Asia/Taipei")}
    if params.get("seven_questions"):
        m["seven_questions"] = params["seven_questions"]
    return m


def generate(name, params, out_dir):
    """render 配方 + 寫 service.yaml → 服務包。回 (bundle_path, 預檢錯誤 list)。"""
    if not NAME_RE.match(name):
        raise ValueError(f"service_name 格式不合（小寫英數-，3-40 字）：{name!r}")
    params = {**DEFAULTS, **_org_defaults(), **(params or {})}
    arch = params["archetype"]
    tpl = os.path.join(RECIPES, arch, "template")
    if not os.path.isdir(tpl):
        raise ValueError(f"沒有 {arch!r} 配方（有：{', '.join(list_archetypes())}）")
    try:
        import yaml
    except ImportError:
        raise RuntimeError("需要 PyYAML：pip install pyyaml")

    bundle = os.path.join(out_dir, name)
    os.makedirs(bundle, exist_ok=True)
    rp = dict(params, service_name=name)
    for fn in os.listdir(tpl):
        src = os.path.join(tpl, fn)
        if os.path.isfile(src):
            with open(src) as fh:
                out = _render(fh.read(), rp)
            with open(os.path.join(bundle, fn), "w") as fh:
                fh.write(out)
    manifest = build_manifest(name, params)
    if not manifest["edges"] and params["archetype"] != "library":
        raise ValueError("需要至少一條服務鏈邊：提供 params.edges / edge_to，"
                         "或安裝 org-defaults.yaml（bundle 契約要求 ≥1 typed 邊）")
    with open(os.path.join(bundle, "service.yaml"), "w") as fh:
        yaml.safe_dump(manifest, fh, allow_unicode=True, sort_keys=False)

    # 禮貌性預檢（單一真相＝registry_contract；R3 拆 repo 後 validator 隨產生器帶走或裝套件）
    try:
        sys.path.insert(0, HERE)   # 同 repo 佈局：registry_contract.py（vendored）在旁邊
        import registry_contract as contract
        errs = contract.validate_bundle(bundle)
    except Exception as e:   # 預檢失敗不擋產出（部署器才是權威）
        errs = [f"（預檢無法執行：{e}）"]
    return bundle, errs


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="服務包產生器（bundle spec v1；零雲端依賴）")
    ap.add_argument("name")
    ap.add_argument("--out", default=".", help="輸出目錄（預設當前目錄）")
    ap.add_argument("--params", default="{}", help="JSON params（archetype/description/owner/…）")
    a = ap.parse_args()
    bundle, errs = generate(a.name, json.loads(a.params), a.out)
    print(f"服務包：{bundle}")
    if errs:
        print(f"⚠ 預檢 {len(errs)} 項（部署器收包會權威 re-validate）：")
        for e in errs:
            print(f"   - {e}")
        sys.exit(1)
    print("✅ 預檢通過（bundle spec v1 + 0-B）")
