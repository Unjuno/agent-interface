"""Reproduce class-label relabel acceptance against the #5139 raw auditor."""
from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path
import sys

PACKAGE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PACKAGE))
from audit_results import audit, reference_bind, reference_effect  # noqa: E402
from make_dataset import build  # noqa: E402
from sampler import CLASSES, select_support  # noqa: E402

FORMAL_SENTINEL = 830513911
SUPPORT_SENTINEL = 830513912
ALLOCATION = "qwen5139-class-label-integrity-verification-20260929"
SWAP = {"yield:forbidden": "yield:ambiguous", "yield:ambiguous": "yield:forbidden"}


def canonical_bytes(value: dict) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def class_from_intent(intent: dict) -> str | None:
    """Independent semantic mapping, deliberately not reading row['class']."""
    op = intent.get("op")
    if op in ("yield", "no_action"):
        reason = intent.get("reason")
        return f"{op}:{reason}" if isinstance(reason, str) else None
    return op if op in ("set", "save", "toggle") else None


data = build(FORMAL_SENTINEL, SUPPORT_SENTINEL, ALLOCATION)
for pool_name in ("support_pool", "heldout_pool"):
    for row in data[pool_name]:
        row["class"] = SWAP.get(row["class"], row["class"])

imbalanced, balanced = select_support(data["support_pool"], SUPPORT_SENTINEL)
data["supports"] = {
    "imbalanced": [row for name in CLASSES for row in imbalanced[name]],
    "balanced": [row for name in CLASSES for row in balanced[name]],
}
grouped = defaultdict(list)
for row in data["heldout_pool"]:
    grouped[row["class"]].append(row)
data["heldout"] = [row for name in CLASSES for row in grouped[name][:8]]
data["heldout_selection"] = {name: [row["case_id"] for row in grouped[name][:8]] for name in CLASSES}

data_bytes = canonical_bytes(data)
dataset_sha = hashlib.sha256(data_bytes).hexdigest()
raw_documents = {}
for arm in ("base", "imbalanced", "balanced"):
    results = []
    for row in data["heldout"]:
        intent = row["intent"]
        bound = reference_bind(intent, row["state"], row["requested_generation"])
        effect = reference_effect(bound, row["state"])
        raw_text = json.dumps(intent, sort_keys=True, separators=(",", ":"))
        token_ids = list(range(1, 1 + max(1, len(raw_text.encode()) // 4)))
        results.append({
            "case_id": row["case_id"], "class": row["class"], "raw_text": raw_text,
            "parsed": intent, "parse_error": None, "truth_intent": intent,
            "bound": bound, "effect": effect, "latency_ns": 1000,
            "input_tokens": 20, "output_token_ids": token_ids, "output_tokens": len(token_ids),
        })
    raw_documents[arm] = {
        "schema": "qwen05b-abstention-balance-raw-arm-v1", "arm": arm,
        "adapter": arm != "base", "seed": FORMAL_SENTINEL,
        "dataset_sha256": dataset_sha, "results": results,
    }

outcome = audit(data_bytes, raw_documents)
mismatches = sum(
    row.get("class") != class_from_intent(row.get("intent", {}))
    for pool in ("support_pool", "heldout_pool")
    for row in data[pool]
)
result = {
    "status": "PASS_REPRODUCED_CLASS_LABEL_ACCEPTANCE" if outcome["integrity_pass"] and mismatches else "STOP_REPRODUCTION_MISMATCH",
    "sentinels": {"formal": FORMAL_SENTINEL, "support": SUPPORT_SENTINEL},
    "dataset_sha256": dataset_sha,
    "class_mapping_mismatches": mismatches,
    "independent_raw_audit_integrity_pass": outcome["integrity_pass"],
    "independent_raw_audit_errors": outcome["errors"],
    "reported_metrics": outcome["metrics"],
    "reported_balanced_per_class": outcome["per_class_exact"]["balanced"],
    "scope": "synthetic auditor-integrity reproduction only; no model/GPU/Docker/formal result",
}
Path(__file__).with_name("result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, sort_keys=True))
if result["status"] != "PASS_REPRODUCED_CLASS_LABEL_ACCEPTANCE":
    raise SystemExit(1)
