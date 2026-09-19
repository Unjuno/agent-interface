"""Audit source hashes recorded by the scoped #2737 result.

This is an integrity check only. It does not rerun Docker, contact a model, or
promote the retained six-task result to current-main behavior.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RESULT = ROOT / "research/analysis/full_golden_ipc_2737_v1/RESULT.json"

def main():
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    rows = []
    drift = []
    for path, expected in result["source_hashes"].items():
        target = ROOT / path
        if not target.is_file():
            actual = None
        else:
            actual = hashlib.sha256(target.read_bytes()).hexdigest()
        row = {"path": path, "expected": expected, "actual": actual,
               "match": actual == expected}
        rows.append(row)
        if not row["match"]:
            drift.append(row)
    decision = "PASS_SOURCE_HASH_INTEGRITY" if not drift else "HOLD_SOURCE_HASH_DRIFT"
    print(json.dumps({"decision": decision, "result": str(RESULT.relative_to(ROOT)),
                      "source_count": len(rows), "drift_count": len(drift),
                      "rows": rows}, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
