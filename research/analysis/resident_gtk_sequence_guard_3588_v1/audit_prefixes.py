from __future__ import annotations

import json
from pathlib import Path

from oracle import PrefixOracle, snapshot
from traces import COMPARATORS, TRACES


raw = json.loads(Path("/evidence/prefixes.json").read_text())
errors = []
prefix_count = 0
for name, events in TRACES.items():
    recorded = raw.get("traces", {}).get(name)
    if not recorded or recorded.get("events") != events:
        errors.append(f"{name}: frozen trace mismatch")
        continue
    oracle = PrefixOracle()
    actual_rows = recorded.get("guarded_candidate", [])
    if len(actual_rows) != len(events):
        errors.append(f"{name}: candidate prefix denominator mismatch")
        continue
    for index, (event, row) in enumerate(zip(events, actual_rows)):
        before = len(oracle.actions)
        oracle.consume(event)
        expected_state = snapshot(oracle)
        expected_delta = [list(a) for a in oracle.actions[before:]]
        if row.get("prefix") != index + 1 or row.get("event") != event:
            errors.append(f"{name} prefix {index+1}: prefix/event binding mismatch")
        if row.get("state") != expected_state:
            errors.append(f"{name} prefix {index+1}: state differs from independent prefix replay")
        if row.get("action_delta") != expected_delta:
            errors.append(f"{name} prefix {index+1}: action delta differs from oracle")
        prefix_count += 1

rollback = raw["traces"]["delayed_replacement_rollback"]
old_rows = rollback["original"]
if old_rows[-1]["state"]["generation"] != 1 or ["emit", "old-after-rollback"] not in old_rows[-1]["action_delta"]:
    errors.append("upstream candidate failed to reproduce the known delayed-replacement rollback")
guarded_rows = rollback["guarded_candidate"]
if guarded_rows[-1]["state"]["generation"] != 2 or ["emit", "old-after-rollback"] in guarded_rows[-1]["state"]["actions"]:
    errors.append("guarded candidate permits stale-generation emit after delayed replacement")

expected_comparators = {
    "duplicate_true": (["x2"], ["x1", "x2"]),
    "arrival_true_then_delayed_false": ([], ["true3"]),
}
for name, events in COMPARATORS.items():
    exp_last, exp_count = expected_comparators[name]
    row = raw.get("comparators", {}).get(name, {})
    if row.get("events") != events:
        errors.append(f"comparator trace mismatch: {name}")
    for arm in ("original", "guarded"):
        if (row.get(f"{arm}_last_message") != exp_last
                or row.get(f"{arm}_message_count") != exp_count):
            errors.append(f"comparator semantics mismatch: {name}/{arm}")

decision = "PASS_CONSTRUCTION_PREFIX_ORACLE" if not errors else "STOP_OR_HOLD_CONSTRUCTION_AUDIT"
audit = {"decision": decision, "trace_count": len(TRACES), "prefix_count": prefix_count,
         "mutation_challenges": {"sequence_guard_removed": "unit-test adversarial trace",
                                 "state_before_sequence_check": "unit-test adversarial trace",
                                 "future_revoke_batch_lookahead": "unit-test adversarial trace"},
         "errors": errors, "formal_gui_invocations": 0}
Path("/evidence/audit.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n")
print(json.dumps(audit, sort_keys=True))
if errors:
    raise SystemExit(1)
