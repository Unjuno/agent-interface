#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
plan = json.loads((ROOT / "plan.json").read_text())
result = json.loads((ROOT / "result.json").read_text())

assert result["task"] == plan["task"]
assert result["freeze_head"] == "2ff8e897501aa434869bb19999b1e949d203c664"
assert result["measured_update_attempts"] == 3
assert result["successful_initial_commits"] == 3
assert result["recovery_put_attempts"] == 0

seen = {row["name"]: row for row in result["cases"]}
assert list(plan["measured_order"]) == [row["name"] for row in result["cases"]]
for name, cfg in plan["cases"].items():
    row = seen[name]
    assert row["classification"] == cfg["expected"] == row["expected"]
    assert row["payload_blob"] == row["readback_blob"]
    assert row["recovery_puts"] == 0

assert seen["same_owner_changed_content"]["classification"] == "CONFLICT_CONTENT_MISMATCH"
assert all(result["gates"].values())
assert result["decision"] == "PASS_CONTENT_BOUND_READBACK_SCOPED"
print("PASS_CONTENT_BOUND_READBACK_SCOPED")
