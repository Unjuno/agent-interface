"""No-GUI historical import closure gate for #2922."""
from __future__ import annotations
import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LIVE = ROOT / "research" / "live_control"
for path in (LIVE, ROOT / "research" / "observation_tiles", ROOT / "research" / "observation_gating", ROOT / "research" / "real_apps_v1"):
    sys.path.insert(0, str(path))

MODULES = ("tile_transport", "image_artifact", "gui_suite", "executor_v3", "lease", "session_v4")

def main() -> int:
    rows = []
    for name in MODULES:
        try:
            module = importlib.import_module(name)
        except Exception as error:
            rows.append({"module": name, "status": "STOP_IMPORT_CLOSURE", "error_type": type(error).__name__, "error": str(error)})
            break
        rows.append({"module": name, "status": "PASS_IMPORT", "file": str(getattr(module, "__file__", ""))})
    result = {"schema": "golden-ipc-import-closure-result-v1", "issue": 2922, "rows": rows,
              "status": "PASS_IMPORT_CLOSURE" if rows and all(row["status"] == "PASS_IMPORT" for row in rows) else "STOP_IMPORT_CLOSURE",
              "authority_granted": False, "gui_operations": 0, "input_operations": 0, "runtime_ready": False}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS_IMPORT_CLOSURE" else 1

if __name__ == "__main__":
    raise SystemExit(main())
