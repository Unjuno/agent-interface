import hashlib
import json
import sys
from pathlib import Path


raw = Path(sys.argv[1]).read_bytes()
lines = raw.splitlines(keepends=True)
assert raw.endswith(b"\n"), "missing final LF"
rows = [json.loads(line) for line in lines]
assert len(rows) == 4, f"expected 4 raw rows, got {len(rows)}"
assert all(line.endswith(b"\n") for line in lines), "non-LF row ending"
assert all(json.dumps(row, sort_keys=True, separators=(",", ":")).encode() + b"\n" == line
           for row, line in zip(rows, lines)), "noncanonical JSONL bytes"

old, decoy, positive, identity = rows
assert old["event"] == "old_target_attempt"
assert old["old_generation"] != old["current_generation"]
assert old["p2_effect_after_attempt"] is False, "stale XID caused p2 effect"
assert decoy["event"] == "decoy_target_attempt"
assert decoy["target_pid"] != decoy["window_pid"]
assert decoy["decoy_effect"] is True and decoy["p2_effect"] is False
assert positive["event"] == "p2_positive_control"
assert positive["target_pid"] == positive["window_pid"] and positive["p2_effect"] is True
assert identity["old_generation"] != identity["current_generation"]
assert identity["current_pid"] == positive["target_pid"]

print(json.dumps({
    "audit": "PASS_BYTE_AND_SCOPED_EFFECT_GATES",
    "rows": len(rows), "bytes": len(raw),
    "sha256": hashlib.sha256(raw).hexdigest(),
    "old_target_no_p2_effect": True,
    "decoy_isolated": True,
    "p2_positive_effect": True,
}, sort_keys=True))
