#!/usr/bin/env python3
"""registry_contract.py — 【VENDORED 副本】正典在 public repo ai-infra-management/tools/registry_contract.py

bundle spec 有變動時必須同步。此副本只供產生器本機預檢（部署器另持權威副本）。

—— 原始說明 ——
服務目錄單一登記契約（Stage 0-B）

把鬆散的三條 ingestion（build-ai-catalog / discover-initiatives / catalog-server，
未來 + 工廠 MCP 的 register tool）收斂到**同一道驗證**。是純函式 + 一個 CLI 稽核模式，
無副作用、無 I/O（CLI 模式才讀檔），方便各入口共用。

契約（spec：docs/service-factory/stage0-foundation-and-contract.md 0-B）：
  - spec.type 必在 enum。
  - data_class 必在 enum；**畢業到 production 等級時不接受 null**（取代舊「可選」）。
  - 畢業到 production 等級的 Component 必有 **≥1 條 typed 邊**，且邊的 type/data_class 不得是 unknown。
  - ai_generated=true 的節點必有 tech_owner（誰維護 AI 產物）。

分級執行（lifecycle-graduated）：低 stage 寬鬆（只查 enum 合法），畢業前才全查。
  - LENIENT：idea / experiment / in-use → 只查 enum 正確性，缺 data_class/邊只警告不擋。
  - STRICT ：standardized / blessed / production → 全契約必過。

R1（ADR 0007）：本檔同時是「服務包（bundle spec v1）」的 validator——產生器端當禮貌性預檢、
部署器端 re-validate 為權威（永不信任 client）。spec 文件：docs/service-factory/bundle-spec.md。
"""
import os
import re

VALID_TYPES = ('service', 'website', 'data-product', 'skill', 'mcp-tool', 'job', 'library')
VALID_DATA_CLASS = ('none', 'internal', 'customer-pii', 'financial', 'regulated')
VALID_EDGE_TYPE = ('sync-api', 'webhook-async', 'reads-data', 'writes-data',
                   'auth', 'shared-infra', 'event')
VALID_LIFECYCLE = ('idea', 'experiment', 'in-use', 'standardized', 'blessed',
                   'production', 'deprecated')

# 走到這些 lifecycle = 已畢業/對外營運 → 全契約必過
STRICT_LIFECYCLES = ('standardized', 'blessed', 'production')
# library 只發版不部署，登記時可無依賴邊 → 豁免「≥1 邊」（仍須 data_class）
EDGE_EXEMPT_TYPES = ('library',)


def _node_refs(name, kind):
    """節點在邊上的端點字串：Component→component:name、Resource→resource:name。"""
    prefix = 'resource' if (kind or 'Component').lower() == 'resource' else 'component'
    return {f'{prefix}:{name}'}


def edges_touching(name, kind, edges):
    """回傳所有以此節點為端點的邊。"""
    refs = _node_refs(name, kind)
    return [e for e in (edges or [])
            if e.get('from') in refs or e.get('to') in refs]


def validate(node, edges=None, *, strict=None):
    """驗證單一節點（+ 與它相連的邊）。回傳錯誤字串 list（空 = 通過）。

    strict=None → 依 lifecycle 自動判定；strict=True/False → 強制覆寫。
    edges = service-graph 的完整 edges[]（會自行篩出相連的）。
    """
    errs = []
    spec = node.get('spec') or {}
    gov = spec.get('governance') or {}
    name = (node.get('metadata') or {}).get('name') or '(unnamed)'
    kind = node.get('kind') or 'Component'

    # ── enum 正確性（不分 stage 都查）──
    typ = spec.get('type')
    if typ not in VALID_TYPES:
        errs.append(f'spec.type={typ!r} 不在 enum {VALID_TYPES}')
    life = spec.get('lifecycle')
    if life not in VALID_LIFECYCLE:
        errs.append(f'spec.lifecycle={life!r} 不在 enum {VALID_LIFECYCLE}')
    dc = gov.get('data_class')
    if dc not in (None, '') and dc not in VALID_DATA_CLASS:
        errs.append(f'governance.data_class={dc!r} 不在 enum {VALID_DATA_CLASS}')

    if strict is None:
        strict = life in STRICT_LIFECYCLES
    if not strict:
        return errs   # 低 stage：enum 過了就放行

    # ── STRICT：畢業契約 ──
    if dc in (None, ''):
        errs.append('governance.data_class 缺（畢業到 production 等級必填，不接受 null）')

    if typ not in EDGE_EXEMPT_TYPES:
        rel = edges_touching(name, kind, edges)
        typed = [e for e in rel
                 if e.get('type') in VALID_EDGE_TYPE
                 and e.get('data_class') not in (None, '', 'unknown')
                 and e.get('criticality') not in ('unknown',)]
        if not typed:
            errs.append('缺 ≥1 條 typed 邊（type∈enum、data_class/criticality 不得 unknown）；'
                        f'相連邊 {len(rel)} 條但無一達標')

    if gov.get('ai_generated') is True and not gov.get('tech_owner'):
        errs.append('ai_generated=true 但 governance.tech_owner 空（AI 產物須指定維護人）')

    return errs


def audit_catalog(catalog, graph):
    """稽核整份 catalog。回傳 [(name, lifecycle, [errs]), ...]，只列有錯的。"""
    edges = (graph or {}).get('edges') or []
    out = []
    for node in catalog.get('initiatives') or []:
        errs = validate(node, edges)
        if errs:
            life = (node.get('spec') or {}).get('lifecycle')
            name = (node.get('metadata') or {}).get('name')
            out.append((name, life, errs))
    return out


# ── 服務包 bundle spec v1（R1，ADR 0007）─────────────────────────
# 服務包＝產生器與部署器之間的唯一合約（public interface）。
BUNDLE_SPEC_VERSIONS = ("v1",)
NAME_RE = re.compile(r"^[a-z][a-z0-9-]{1,38}[a-z0-9]$")
REF_RE = re.compile(r"^(component|resource):\S+$")
BUNDLE_REQUIRED_FILES = ("service.yaml", "Dockerfile", "requirements.txt", "README.md")
# 程式進入點：main.py 或 src/ 至少一個（見 bundle-spec.md）


def load_bundle_manifest(bundle_dir):
    """讀服務包資料夾 → (manifest dict|None, [結構錯誤])。只做結構層；語意層在 validate_bundle。"""
    if not os.path.isdir(bundle_dir):
        return None, [f"服務包資料夾不存在：{bundle_dir}"]
    errs = [f"缺必要檔：{f}" for f in BUNDLE_REQUIRED_FILES
            if not os.path.isfile(os.path.join(bundle_dir, f))]
    if not (os.path.isfile(os.path.join(bundle_dir, "main.py"))
            or os.path.isdir(os.path.join(bundle_dir, "src"))):
        errs.append("缺程式進入點：main.py 或 src/")
    mpath = os.path.join(bundle_dir, "service.yaml")
    if not os.path.isfile(mpath):
        return None, errs
    try:
        import yaml
    except ImportError:
        return None, errs + ["解析 service.yaml 需要 PyYAML：pip install pyyaml"]
    try:
        with open(mpath) as f:
            m = yaml.safe_load(f)
    except Exception as e:
        return None, errs + [f"service.yaml 解析失敗：{e}"]
    if not isinstance(m, dict):
        return None, errs + ["service.yaml 頂層必須是 mapping"]
    return m, errs


def bundle_to_entry(manifest, actor=None):
    """service.yaml → (catalog Component, [富邊])。與部署器共用的唯一 mapping。
    actor＝認證身分：部署器一定要傳（覆核自報 owner）；產生器預檢可不傳（用自報值）。"""
    m = manifest
    name = m.get("name") or ""
    gov_in = m.get("governance") or {}
    owner = (actor or m.get("owner") or "")
    short = owner.split("@")[0] if "@" in owner else owner
    uses_ai = bool(gov_in.get("uses_ai", False))
    entry = {
        "kind": "Component",
        "metadata": {"name": name, "title": m.get("title") or name},
        "spec": {"type": m.get("archetype"), "lifecycle": "production",
                 "governance": {"fidelity": "A", "hosting": "gcp", "hosting_tier": "P1",
                                "criticality": gov_in.get("criticality", "low"),
                                "owner": short, "data_class": gov_in.get("data_class"),
                                "uses_ai": "Claude" if uses_ai else "無",
                                "tech_owner": short, "ai_generated": True}},
        "_provenance": "bundle:spec-v1"}
    edges = []
    for e in (m.get("edges") or []):
        if not isinstance(e, dict):
            continue
        edges.append({"from": f"component:{name}", "to": e.get("to", ""),
                      "direction": e.get("direction", "from-to"), "type": e.get("type"),
                      "criticality": e.get("criticality", "soft"),
                      "data_class": e.get("data_class", gov_in.get("data_class")),
                      "external": bool(e.get("external", False)),
                      "discovery_source": "self_declared",
                      "interface": e.get("interface", ""),
                      "evidence": e.get("evidence", "service.yaml")})
    return entry, edges


def validate_bundle(bundle_dir, actor=None):
    """驗整個服務包＝結構層 + bundle 欄位 + 0-B 畢業契約（strict）。回錯誤 list（空=過）。"""
    m, errs = load_bundle_manifest(bundle_dir)
    if m is None:
        return errs
    v = m.get("bundle_spec")
    if v not in BUNDLE_SPEC_VERSIONS:
        errs.append(f"bundle_spec={v!r} 不支援（支援：{'/'.join(BUNDLE_SPEC_VERSIONS)}）")
    name = m.get("name") or ""
    if not NAME_RE.match(name):
        errs.append(f"name 格式不合（小寫英數與連字號，3-40 字）：{name!r}")
    if not str(m.get("description") or "").strip():
        errs.append("description 必填")
    owner = (actor or m.get("owner") or "")
    if "@" not in owner:
        errs.append("owner 必填（email；部署器會以認證身分覆核，自報值僅供預檢）")
    for e in (m.get("edges") or []):
        to = (e or {}).get("to", "") if isinstance(e, dict) else ""
        if not REF_RE.match(str(to)):
            errs.append(f"edge.to 須為 component:/resource: 前綴 ref：{to!r}")
    entry, edges = bundle_to_entry(m, actor=actor)
    errs += validate(entry, edges, strict=True)   # 0-B 畢業契約（data_class/typed 邊/ai_generated→tech_owner）
    return errs


def _main():
    import argparse, json, os, sys
    ap = argparse.ArgumentParser(description='稽核服務目錄是否符合登記契約（0-B）')
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument('--catalog', default=os.path.join(repo, 'config/ai-catalog.json'))
    ap.add_argument('--graph', default=os.path.join(repo, 'config/service-graph.json'))
    ap.add_argument('--strict-exit', action='store_true',
                    help='有 STRICT-lifecycle 違規時 exit 1（給 CI / reconciliation 用）')
    ap.add_argument('--bundle', help='驗證服務包資料夾（bundle spec v1，R1）')
    ap.add_argument('--actor', default=None, help='認證身分 email（部署器側傳入覆核 owner）')
    args = ap.parse_args()

    if args.bundle:
        errs = validate_bundle(args.bundle, actor=args.actor)
        if errs:
            print(f'❌ 服務包未過契約（{len(errs)} 項）：')
            for e in errs:
                print(f'   - {e}')
            sys.exit(1)
        print('✅ 服務包通過 bundle spec v1 + 0-B 畢業契約')
        return

    catalog = json.load(open(args.catalog))
    graph = json.load(open(args.graph)) if os.path.exists(args.graph) else {}
    violations = audit_catalog(catalog, graph)

    total = len(catalog.get('initiatives') or [])
    if not violations:
        print(f'✅ {total} 筆全數通過登記契約')
        return
    strict_bad = [v for v in violations if v[1] in STRICT_LIFECYCLES]
    print(f'契約稽核：{total} 筆中 {len(violations)} 筆有缺（其中 {len(strict_bad)} 筆已畢業 lifecycle 必須修）\n')
    for name, life, errs in violations:
        flag = '🔴' if life in STRICT_LIFECYCLES else '🟡'
        print(f'{flag} {name}  [{life}]')
        for e in errs:
            print(f'     - {e}')
    if args.strict_exit and strict_bad:
        sys.exit(1)


if __name__ == '__main__':
    _main()
