from __future__ import annotations
import json
from ledger import Episode, REQUIRED, validate

ROWS = [
    Episode("e1", "route-a", "stale_refusal", "yield", "refused", "mono-v1"),
    Episode("e2", "route-a", "fresh_refusal", "yield", "refused", "mono-v1"),
    Episode("e3", "route-a", "stale_action_recovery", "guarded", "recovered", "mono-v1"),
    Episode("e4", "route-a", "fresh_success", "guarded", "effect", "mono-v1"),
    Episode("e5", "route-a", "right_censored", "yield", "unknown", "mono-v1"),
]
ok, errors = validate(ROWS)
result = {
    "rows": len(ROWS),
    "required_support": sorted(REQUIRED),
    "observed_support": sorted({r.status for r in ROWS}),
    "synthetic_controls": True,
    "decision": "HOLD_SYNTHETIC_READINESS_ONLY" if ok else "FAIL_PREFLIGHT_SCHEMA",
    "errors": errors,
    "scope": "schema/readiness only; no live route, GUI, model, authority, input, or network",
}
print(json.dumps(result, indent=2, sort_keys=True))
raise SystemExit(0 if ok else 1)
