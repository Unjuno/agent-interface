"""Fail-closed source and authority preflight for successor #2337."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EXPECTED = {
    "runtime/golden_desktop_demo_v3.py": "26db03b8400b03fbe5272bd4ae5ad9c3a82d31a2",
    "runtime/cli_v1/api.py": "f9dc26441c5f4ff9d7f57aa6a6a7b3849a1537d7",
    "runtime/cli_v1/golden_v3.py": "b72fa2203c9b8be7a03e084cee1e43c239efe92a",
    "runtime/results/golden-desktop-app-server-v3-live-01/golden-report.json": "e168a9bdc84fc6b807f4e90806ec7c501da89689",
}


def git_blob_sha(relative: str) -> str | None:
    """Read the committed blob identity, avoiding Windows newline conversion."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", f"HEAD:{relative}"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or None


def main() -> int:
    checks = {}
    for relative, expected in EXPECTED.items():
        path = ROOT / relative
        observed = git_blob_sha(relative) if path.is_file() else None
        checks[relative] = {
            "exists": path.is_file(),
            "expected": expected,
            "observed": observed,
            "match": observed == expected,
        }
    source_ok = all(row["match"] for row in checks.values())
    authority = os.environ.get("AGENT_INTERFACE_LIVE_AUTHORITY", "").strip().lower() in {"1", "true", "yes"}
    status = (
        "STOP_SOURCE_IDENTITY_GAP" if not source_ok
        else "HOLD_NO_MODEL_AUTHORITY" if not authority
        else "READY_FOR_SEPARATE_LIVE_ALLOCATION"
    )
    result = {
        "schema": "golden_v3_live_adapter_preflight_v2",
        "status": status,
        "source_checks": checks,
        "authority_declared": authority,
        "model_calls": 0,
        "gui_calls": 0,
        "input_events": 0,
        "network_task_calls": 0,
        "scope": "preflight only; no live allocation",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if status in {"HOLD_NO_MODEL_AUTHORITY", "READY_FOR_SEPARATE_LIVE_ALLOCATION"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
