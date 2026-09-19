"""Verify the #2813 task-1 entry gate without starting GUI/model execution."""
import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent

def main():
    plan = json.loads((HERE / "preregistration.json").read_text(encoding="utf-8"))
    mismatches = []
    for name, expected in plan["source_sha256"].items():
        path = ROOT / name
        if not path.is_file(): mismatches.append({"path": name, "reason": "missing"}); continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected: mismatches.append({"path": name, "expected": expected, "actual": actual})
    result = {"status": "PASS_TASK1_ROUTE_PREFLIGHT" if not mismatches else "STOP_SOURCE_HASH_MISMATCH", "issue": 2813, "mismatches": mismatches, "authority_granted": False, "gui_operations": 0, "task_execution": False}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not mismatches else 1

if __name__ == "__main__": raise SystemExit(main())
