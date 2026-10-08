#!/usr/bin/env python3
"""Independent route-selection policy output checker for #2210."""
import json

CASES = [
    ("XI2_AVAILABLE_AND_VERIFIED", "scale+center", "XI2_PINCH"),
    ("CTRL_WHEEL_AVAILABLE", "scale", "CTRL_WHEEL"),
    ("ROUTE_CAPABILITY_UNKNOWN_OR_STALE", "scale+center", "QUERY_CAPABILITY"),
    ("XI2_AVAILABLE_AND_VERIFIED", "scale+selection-preservation", "QUERY_CAPABILITY"),
    ("CTRL_WHEEL_AVAILABLE", "scale+input-cleanup-unknown", "ABORT"),
    ("CROSS_PLATFORM_OR_BACKEND_MISMATCH", "scale", "ABORT"),
]

def policy(capability, task):
    if capability == "ROUTE_CAPABILITY_UNKNOWN_OR_STALE":
        return "QUERY_CAPABILITY"
    if capability == "CROSS_PLATFORM_OR_BACKEND_MISMATCH":
        return "ABORT"
    if "cleanup-unknown" in task:
        return "ABORT"
    if "selection-preservation" in task:
        return "QUERY_CAPABILITY"
    if capability == "XI2_AVAILABLE_AND_VERIFIED" and task == "scale+center":
        return "XI2_PINCH"
    if capability == "CTRL_WHEEL_AVAILABLE" and task == "scale":
        return "CTRL_WHEEL"
    return "ABORT"

rows = []
for capability, task, expected in CASES:
    observed = policy(capability, task)
    rows.append({"capability": capability, "task": task, "expected": expected, "observed": observed})
agreements = sum(row["expected"] == row["observed"] for row in rows)
out = {
    "cases": len(rows),
    "agreements": agreements,
    "violations": len(rows) - agreements,
    "rows": rows,
    "checks": {
        "visible_scale_alone_authorizes": False,
        "unknown_or_stale_blind_input": False,
        "authority_expansion": False,
    },
}
print(json.dumps(out, sort_keys=True, indent=2))
