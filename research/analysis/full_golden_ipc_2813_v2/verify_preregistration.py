"""Verify the current-main successor entry gate without execution."""
import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent

def stable_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()

def main() -> int:
    plan = json.loads((HERE / "preregistration.json").read_text(encoding="utf-8"))
    mismatches = []
    for name, expected in plan["source_sha256_normalized_lf"].items():
        path = ROOT / name
        if not path.is_file():
            mismatches.append({"path": name, "reason": "missing"})
        else:
            actual = stable_sha256(path)
            if actual != expected:
                mismatches.append({"path": name, "expected": expected, "actual": actual})
    result = {"status": "PASS_TASK1_ROUTE_PREFLIGHT" if not mismatches else "STOP_SOURCE_HASH_MISMATCH", "issue": 2813, "successor": "full_golden_ipc_2813_v2", "mismatches": mismatches, "authority_granted": False, "gui_operations": 0, "task_execution": False}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not mismatches else 1

if __name__ == "__main__":
    raise SystemExit(main())
