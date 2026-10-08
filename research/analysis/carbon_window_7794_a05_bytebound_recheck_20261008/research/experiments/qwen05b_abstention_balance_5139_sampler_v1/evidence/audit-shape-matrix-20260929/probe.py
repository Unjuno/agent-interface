"""Deterministic malformed-dataset structural mutation matrix for #5139."""
from __future__ import annotations

import hashlib
import json

from audit_results import audit
from make_dataset import build


CASES = (
    ("support_pool_null", lambda d: d.__setitem__("support_pool", None)),
    ("heldout_pool_null", lambda d: d.__setitem__("heldout_pool", None)),
    ("heldout_null", lambda d: d.__setitem__("heldout", None)),
    ("support_row_nonobject", lambda d: d["support_pool"].__setitem__(0, None)),
    ("heldout_pool_row_nonobject", lambda d: d["heldout_pool"].__setitem__(0, None)),
    ("support_class_list", lambda d: d["support_pool"][0].__setitem__("class", [])),
    ("heldout_class_object", lambda d: d["heldout_pool"][0].__setitem__("class", {"bad": True})),
    ("support_state_null", lambda d: d["support_pool"][0].__setitem__("state", None)),
    ("heldout_state_string", lambda d: d["heldout_pool"][0].__setitem__("state", "bad")),
    ("support_intent_list", lambda d: d["support_pool"][0].__setitem__("intent", [])),
    ("heldout_intent_null", lambda d: d["heldout_pool"][0].__setitem__("intent", None)),
    ("supports_null", lambda d: d.__setitem__("supports", None)),
    ("support_task_list", lambda d: d["support_pool"][0].__setitem__("task", [])),
    ("heldout_task_object", lambda d: d["heldout_pool"][0].__setitem__("task", {"bad": True})),
    ("support_case_id_list", lambda d: d["support_pool"][0].__setitem__("case_id", [])),
    ("heldout_case_id_object", lambda d: d["heldout_pool"][0].__setitem__("case_id", {"bad": True})),
)


def run_case(name, mutate):
    data = build(830513951, 830513952, "qwen5139-audit-shape-matrix-20260929")
    mutate(data)
    raw = (json.dumps(data, sort_keys=True, separators=(",", ":")) + "\n").encode()
    try:
        result = audit(raw, {})
    except Exception as exc:
        return {
            "case": name,
            "dataset_sha256": hashlib.sha256(raw).hexdigest(),
            "raised": type(exc).__name__,
            "message": str(exc),
            "rejected": False,
        }
    structural_errors = [e for e in result["errors"] if not e.startswith("missing_raw:")]
    return {
        "case": name,
        "dataset_sha256": hashlib.sha256(raw).hexdigest(),
        "raised": None,
        "rejected": not result["integrity_pass"] and bool(structural_errors),
        "integrity_pass": result["integrity_pass"],
        "structural_errors": structural_errors,
    }


rows = [run_case(name, mutate) for name, mutate in CASES]
print(json.dumps({
    "cases": rows,
    "case_count": len(rows),
    "exception_count": sum(row["raised"] is not None for row in rows),
    "rejected_count": sum(row["rejected"] for row in rows),
    "scope": "synthetic dataset-auditor robustness only; no model/GPU/Docker/formal result",
    "status": "PASS" if all(row["rejected"] for row in rows) else "FAIL_OR_EXCEPTION_OBSERVED",
}, sort_keys=True))
