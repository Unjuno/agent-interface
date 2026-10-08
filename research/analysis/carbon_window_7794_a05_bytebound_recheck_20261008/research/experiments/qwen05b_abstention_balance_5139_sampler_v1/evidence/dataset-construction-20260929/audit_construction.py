from __future__ import annotations
import copy, hashlib, json, sys
from collections import Counter, defaultdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from audit_sampler import CLASSES, COUNTS, audit_support_selection

raw = Path("dataset.json").read_bytes()
data = json.loads(raw.decode("utf-8"))
errors = []
if raw != (json.dumps(data, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8"):
    errors.append("raw_not_canonical_json")
if data.get("allocation") != "qwen5139-dataset-construction-20260929":
    errors.append("allocation")
if data.get("seed") != 903520260929 or data.get("support_seed") != 903520260930:
    errors.append("construction_sentinels")
if len(data.get("support_pool", [])) != 128: errors.append("support_pool_size")
if len(data.get("heldout_pool", [])) != 256: errors.append("heldout_pool_size")
if len(data.get("heldout", [])) != 64: errors.append("heldout_size")
errors.extend("support:" + e for e in audit_support_selection(data))
groups = defaultdict(list)
for row in data.get("heldout_pool", []):
    groups[row.get("class")].append(row)
expected = [row for name in CLASSES for row in groups[name][:8]]
if len(expected) != 64: errors.append("heldout_class_quota")
if data.get("heldout") != expected: errors.append("heldout_prefix_order_or_content")
ids = [r.get("case_id") for r in data.get("support_pool", []) + data.get("heldout_pool", [])]
if len(ids) != len(set(ids)): errors.append("duplicate_case_id")
support_scopes = {r.get("state", {}).get("scope_id") for r in data["support_pool"]}
heldout_scopes = {r.get("state", {}).get("scope_id") for r in data["heldout_pool"]}
if support_scopes & heldout_scopes: errors.append("support_heldout_scope_overlap")
if {r.get("task") for r in data["support_pool"]} & {r.get("task") for r in data["heldout_pool"]}:
    errors.append("support_heldout_task_overlap")
for arm, quotas in COUNTS.items():
    got = Counter(r.get("class") for r in data.get("supports", {}).get(arm, []))
    if any(got.get(k, 0) != v for k,v in quotas.items()): errors.append("support_quota:" + arm)
controls = {}
mut = copy.deepcopy(data); mut["support_seed"] += 1
controls["support_seed_mutation_rejected"] = bool(audit_support_selection(mut))
mut = copy.deepcopy(data); mut["heldout"].pop()
controls["missing_heldout_rejected"] = mut["heldout"] != expected
mut = copy.deepcopy(data); mut["heldout"].reverse()
controls["reordered_heldout_rejected"] = mut["heldout"] != expected
mut = copy.deepcopy(data); mut["heldout"][0]["state"]["scope_id"] = mut["support_pool"][0]["state"]["scope_id"]
controls["split_scope_overlap_detected"] = bool(
    {r["state"]["scope_id"] for r in mut["support_pool"]}
    & {r["state"]["scope_id"] for r in mut["heldout_pool"]}
)
if not all(controls.values()): errors.append("control_failed")
result = {
    "status": "PASS_DATASET_CONSTRUCTION_AUDIT" if not errors else "STOP_DATASET_CONSTRUCTION_AUDIT",
    "scope": "synthetic dataset construction only; no model/CUDA/GPU/Docker/formal output",
    "raw_bytes": len(raw),
    "raw_sha256": hashlib.sha256(raw).hexdigest(),
    "checks": [
        "canonical raw JSON", "allocation/sentinels", "pool and heldout denominators",
        "independent SHA-ranked support reconstruction", "heldout per-class prefix reconstruction",
        "case ID uniqueness", "support/heldout scope and task disjointness", "arm class quotas",
    ],
    "corruption_controls": controls,
    "errors": errors,
}
Path("audit.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, sort_keys=True))
if errors: sys.exit(1)

