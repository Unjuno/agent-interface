import hashlib
import json
from pathlib import Path

raw = Path("/harness/out/raw.jsonl").read_bytes()
lines = raw.splitlines(keepends=True)
rows = [json.loads(line) for line in lines]
byte_gate = raw.endswith(b"\n") and len(rows) == 4 and all(
    line.endswith(b"\n") and
    json.dumps(row, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n" == line
    for row, line in zip(rows, lines)
)
old, decoy, positive, identity = rows
gates = {
    "byte_gate": byte_gate,
    "stale_attempt_no_p2_effect": old["p2_effect_after_attempt"] is False,
    "decoy_window_distinct_from_target": decoy["window_pid"] != decoy["target_pid"],
    "decoy_effect_confirmed": decoy["decoy_effect"] is True,
    "p2_unchanged_by_decoy": decoy["p2_effect"] is False,
    "p2_positive_effect": positive["target_pid"] == positive["window_pid"] and positive["p2_effect"] is True,
    "old_xid_reused_by_decoy": identity["old_window"] == decoy["window"],
    "old_generation_differs": identity["old_generation"] != identity["current_generation"],
}
print(json.dumps({
    "audit": "HOLD_DECOY_EFFECT_UNVERIFIED" if not all(gates.values()) else "PASS_SCOPED",
    "rows": len(rows), "bytes": len(raw),
    "sha256": hashlib.sha256(raw).hexdigest(), "gates": gates,
}, sort_keys=True))
