#!/usr/bin/env python3
"""Deterministic offline verifier for Issue #449 retained artifacts.

No GitHub/network I/O. This file is retained for reproducibility; repository
publication does not by itself claim that an independent agent executed it.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def raw(name):
    return (ROOT / name).read_text(encoding="utf-8")


result = load("result.json")
assert result["decision"] == "PASS_CONTENT_BOUND_BARRIER_READBACK_SCOPED"
assert result["measurement"]["initial_barrier_update_successes"] == 3
assert result["measurement"]["receiver_recovery_put_count"] == 0
assert result["measurement"]["coordination_update_count"] == 1
assert result["measurement"]["mode_only_acceptance_count"] == 0
assert result["measurement"]["timeout_used_as_evidence"] is False

# Exact case: retained receiver bytes equal the frozen expected barrier bytes.
assert raw("receiver_exact.json") == raw("payload_barrier_exact.json")
coord_exact = load("coord_exact.json")
assert coord_exact["active_generation"] == 2

# Changed case: mode remains BLOCKED but exact content differs, so coordination stayed g1.
receiver_changed = load("receiver_changed.json")
expected_changed = load("payload_barrier_changed.json")
assert receiver_changed["mode"] == expected_changed["mode"] == "BLOCKED"
assert raw("receiver_changed.json") != raw("payload_barrier_changed.json")
assert receiver_changed["revision"] == 2
assert load("coord_changed.json")["active_generation"] == 1

# Unavailable classifier observation never granted coordination authority.
assert raw("receiver_unavailable.json") == raw("payload_barrier_unavailable.json")
assert load("coord_unavailable.json")["active_generation"] == 1

cases = {c["name"]: c for c in result["cases"]}
assert cases["exact_barrier_readback"]["classification"] == "BARRIER_CONFIRMED"
assert cases["changed_barrier_readback"]["classification"] == "BARRIER_CONFLICT"
assert cases["unavailable_barrier_observation"]["classification"] == "BARRIER_UNKNOWN"
assert all(c["receiver_recovery_puts"] == 0 for c in cases.values())

print("PASS_CONTENT_BOUND_BARRIER_READBACK_SCOPED")
