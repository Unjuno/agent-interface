#!/usr/bin/env python3
"""Offline deterministic verifier for the retained Issue #433 result.

No network access and no experiment allocation.  This checker verifies retained
final state/result invariants only.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load(name):
    return json.loads((ROOT / name).read_text())


result = load("result.json")
naive = load("receiver_naive.json")
barrier = load("receiver_barrier.json")
coord_naive = load("coord_naive.json")
coord_barrier = load("coord_barrier.json")

assert result["decision"] == "PASS_ACTIVATION_BARRIER_PROPAGATION_GAP_SCOPED"
assert coord_naive["active_generation"] == 2
assert coord_barrier["active_generation"] == 2

assert naive["mode"] == "ACTIVE"
assert naive["accepted_generation"] == 2
assert naive["effect_count"] == 2
assert [e["generation"] for e in naive["effects"]] == [1, 2]
assert naive["receipts"]["cmd-old-011"]["outcome"] == "APPLIED"
assert naive["receipts"]["cmd-new-011"]["outcome"] == "APPLIED"

assert barrier["mode"] == "ACTIVE"
assert barrier["accepted_generation"] == 2
assert barrier["effect_count"] == 1
assert [e["generation"] for e in barrier["effects"]] == [2]
assert set(barrier["receipts"]) == {"cmd-new-011"}
assert barrier["receipts"]["cmd-new-011"]["outcome"] == "APPLIED"

assert result["barrier"]["old_request_outcome"] == "BARRIER_BLOCKED"
assert result["barrier"]["old_request_write_count"] == 0
assert all(result["gates"].values())

print("PASS_ACTIVATION_BARRIER_PROPAGATION_GAP_SCOPED")
