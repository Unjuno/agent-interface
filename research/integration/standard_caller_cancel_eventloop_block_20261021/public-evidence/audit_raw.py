"""Independent invariant and latency-separation audit of raw/r02.json."""

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
conditions = json.loads((ROOT / "conditions.json").read_text(encoding="utf-8"))
result = json.loads((ROOT / "raw" / "r02.json").read_text(encoding="utf-8"))
assert result["conditions_sha256"] == hashlib.sha256(
    (ROOT / "conditions.json").read_bytes()).hexdigest()
assert result["audit"]["status"] == "PASS"
assert result["audit"]["failures"] == []
assert len(result["trials"]) == 6

arms = {name: [row for row in result["trials"] if row["arm"] == name]
        for name in conditions["arms"]}
for name, rows in arms.items():
    assert len(rows) == 3, (name, len(rows))
    for row in rows:
        assert row["cancel"]["release_confirmed"] is False
        assert row["cancel"]["cleanup_status"] == "UNKNOWN"
        assert row["cancel"]["task_success"] is None
        assert row["cancel"]["replay_allowed"] is False
        assert row["terminal_call"]["status"] == "runtime_failed"
        assert row["terminal_call"]["release_confirmed"] is False
        assert row["terminal_call"]["cleanup_status"] == "UNKNOWN"
        assert row["terminal_call"]["task_success"] is None
        assert row["terminal_call"]["replay_allowed"] is False
        if row["arm"] == "injected-cleanup-boundary-delay":
            assert abs(row["cancel_tool_elapsed_ms"]
                       - row["max_event_loop_gap_ms"]) < 1.0

baseline = arms["no-injected-cleanup-delay"]
delayed = arms["injected-cleanup-boundary-delay"]
assert min(row["cancel_tool_elapsed_ms"] for row in delayed) > max(
    row["cancel_tool_elapsed_ms"] for row in baseline)
assert min(row["max_event_loop_gap_ms"] for row in delayed) > max(
    row["max_event_loop_gap_ms"] for row in baseline)

for name, rows in arms.items():
    cancel_ms = [row["cancel_tool_elapsed_ms"] for row in rows]
    loop_ms = [row["max_event_loop_gap_ms"] for row in rows]
    print("%s n=%d cancel_ms=%.1f..%.1f heartbeat_gap_ms=%.1f..%.1f" % (
        name, len(rows), min(cancel_ms), max(cancel_ms), min(loop_ms), max(loop_ms)))
print("independent audit: PASS (descriptive Fake X method result only)")
