"""Static path closure gate for golden IPC v2; no runtime or GUI execution."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent

def main() -> int:
    plan = json.loads((HERE / "preregistration.json").read_text(encoding="utf-8"))
    missing = []
    for row in plan["imports"]:
        for key in ("canonical",):
            path = ROOT / row[key]
            if not path.is_file():
                missing.append({"path": row[key], "kind": key})
        if row.get("shim") is not None and not (ROOT / row["shim"]).is_file():
            missing.append({"path": row["shim"], "kind": "shim"})
    result = {
        "schema": "golden-ipc-static-closure-result-v1",
        "issue": 2922,
        "status": "PASS_STATIC_CLOSURE_DECLARED" if not missing else "STOP_STATIC_CLOSURE_MISSING",
        "missing": missing,
        "authority_granted": False,
        "runtime_execution": False,
        "next": "HOLD_RUNTIME_READY_UNVERIFIED" if not missing else "repair_declared_paths",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not missing else 1

if __name__ == "__main__":
    raise SystemExit(main())
