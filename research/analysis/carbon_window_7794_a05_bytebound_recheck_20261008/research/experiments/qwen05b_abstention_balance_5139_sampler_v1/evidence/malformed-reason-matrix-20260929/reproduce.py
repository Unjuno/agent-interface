"""Exercise list/object reason values for both operation and pool families."""
from __future__ import annotations

import hashlib
import json

from audit_results import audit
from make_dataset import build


data = build(830513931, 830513932, "qwen5139-malformed-reason-matrix-20260929")
mutations = [
    ("support_pool", 0, {"op": "yield", "reason": []}),
    ("support_pool", 1, {"op": "no_action", "reason": {"malformed": True}}),
    ("heldout_pool", 0, {"op": "yield", "reason": {"malformed": True}}),
    ("heldout_pool", 1, {"op": "no_action", "reason": []}),
]
for pool_name, index, intent in mutations:
    data[pool_name][index]["intent"] = intent
payload = (json.dumps(data, sort_keys=True, separators=(",", ":")) + "\n").encode()
result = audit(payload, {})
support_errors = [e for e in result["errors"] if e.startswith("support_class_mismatch:")]
heldout_errors = [e for e in result["errors"] if e.startswith("heldout_class_mismatch:")]
print(json.dumps({
    "input_sha256": hashlib.sha256(payload).hexdigest(),
    "integrity_pass": result["integrity_pass"],
    "raised": None,
    "support_class_mismatch_count": len(support_errors),
    "heldout_class_mismatch_count": len(heldout_errors),
    "errors": result["errors"],
    "scope": "synthetic auditor robustness only; no model/GPU/Docker/formal result",
}, sort_keys=True))
