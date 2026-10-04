from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results" / "t0-01"


def audit() -> dict:
    windows = json.loads((RESULTS / "RUN_WINDOWS.json").read_text(encoding="utf-8"))
    wsl = json.loads((RESULTS / "RUN_WSL.json").read_text(encoding="utf-8"))
    windows_raw = (RESULTS / "raw-windows.json").read_bytes()
    wsl_raw = (RESULTS / "raw.json").read_bytes()
    assert hashlib.sha256(windows_raw).hexdigest() == windows["raw_sha256"]
    assert hashlib.sha256(wsl_raw).hexdigest() == wsl["raw_sha256"]
    windows_value = json.loads(windows_raw)
    wsl_value = json.loads(wsl_raw)
    assert windows_value == wsl_value
    canonical = json.dumps(wsl_value, sort_keys=True, separators=(",", ":")).encode()
    canonical_sha = hashlib.sha256(canonical).hexdigest()
    assert canonical_sha == windows["raw_canonical_sha256"]
    assert canonical_sha == wsl["raw_canonical_sha256"]
    return {
        "schema": "producer-scorer-cross-platform-audit-v1",
        "status": "PASS_SEMANTIC_JSON_EQUAL_LINE_ENDINGS_DIFFER",
        "windows_raw_sha256": windows["raw_sha256"],
        "wsl_raw_sha256": wsl["raw_sha256"],
        "canonical_json_sha256": canonical_sha,
        "parsed_json_equal": True,
    }


if __name__ == "__main__":
    result = audit()
    target = ROOT / "CROSS_PLATFORM_AUDIT.json"
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
