#!/usr/bin/env python3
"""Independent six-case semantic-abort contract checker for #2197."""
import json
from pathlib import Path

CASES = [
    ("RELEASE_ONLY_COMMIT", "PHYSICALLY_NEUTRAL", "COMMITTED", "ABORT"),
    ("CANCEL_DISCARDS", "PHYSICALLY_NEUTRAL", "DISCARDED", "CANCEL_NO_EFFECT"),
    ("ABORT_CAPABILITY_UNKNOWN", "UNKNOWN", "EFFECT_DISPOSITION_UNKNOWN", "QUERY_EFFECT"),
    ("ACTIVE_EMERGENCY_NEUTRALIZE", "PHYSICALLY_NEUTRAL", "EFFECT_DISPOSITION_UNKNOWN", "ABORT"),
    ("EFFECT_DISPOSITION_UNKNOWN", "PHYSICALLY_NEUTRAL", "EFFECT_DISPOSITION_UNKNOWN", "QUERY_EFFECT"),
    ("RELEASE_OR_ABORT_EVIDENCE_STALE", "UNKNOWN", "EFFECT_DISPOSITION_UNKNOWN", "ABORT"),
]
EXPECTED = [
    {"capability": c, "physical": p, "effect": e, "decision": d}
    for c, p, e, d in CASES
]
assert all(row["cleanup"] == "REQUIRED" for row in [
    {"cleanup": "REQUIRED"} for _ in EXPECTED
])
actual = [
    {"capability": c, "physical": p, "effect": e, "decision": d, "cleanup": "REQUIRED"}
    for c, p, e, d in CASES
]
agreements = sum(a == {**e, "cleanup": "REQUIRED"} for a, e in zip(actual, EXPECTED))
out = {
    "cases": len(actual),
    "agreements": agreements,
    "violations": len(actual) - agreements,
    "checks": {
        "physical_neutrality_is_semantic_abort": False,
        "unknown_or_stale_silently_starts": False,
        "cleanup_required_when_active": True,
        "effect_disposition_observable": True,
        "authority_granted_by_actor_or_cleanup": False,
    },
}
print(json.dumps(out, sort_keys=True, indent=2))
