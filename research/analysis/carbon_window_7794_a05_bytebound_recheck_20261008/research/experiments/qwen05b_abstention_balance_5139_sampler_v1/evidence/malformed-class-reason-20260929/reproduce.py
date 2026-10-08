"""Probe unhashable reason values in the independent class derivation."""
from __future__ import annotations

import hashlib
import json

from audit_results import audit
from make_dataset import build


data = build(830513921, 830513922, "qwen5139-malformed-class-reason-probe-20260929")
data["support_pool"][0]["intent"] = {"op": "yield", "reason": []}
data["heldout_pool"][0]["intent"] = {"op": "yield", "reason": {"malformed": True}}
payload = (json.dumps(data, sort_keys=True, separators=(",", ":")) + "\n").encode()
outcome = {
    "input_sha256": hashlib.sha256(payload).hexdigest(),
    "scope": "synthetic auditor robustness only; no model/GPU/Docker/formal result",
}
try:
    result = audit(payload, {})
    outcome.update({"raised": None, "integrity_pass": result["integrity_pass"], "errors": result["errors"]})
except Exception as exc:  # Record unexpected auditor failure as the observed outcome.
    outcome.update({"raised": type(exc).__name__, "message": str(exc)})
print(json.dumps(outcome, sort_keys=True))
