"""Audit only the retained pre-observation STOP evidence; never infers science."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit() -> dict:
    env = json.loads((ROOT / "FORMAL_EXECUTION_ENVIRONMENT.json").read_text())
    formal = ROOT / "formal"
    result_path = formal / "FORMAL_RESULT.json"
    launch_path = formal / "p1-immediate" / "launch.json"
    events_path = formal / "p1-immediate" / "controller_events.json"
    result = json.loads(result_path.read_text())
    launch = json.loads(launch_path.read_text())
    events = json.loads(events_path.read_text())
    frozen_sources = {}
    for line in (ROOT / "SHA256SUMS.source").read_text().splitlines():
        digest, relative = line.split(maxsplit=1)
        relative = relative.lstrip("* ")
        if relative.startswith("source/"):
            frozen_sources[relative.removeprefix("source/")] = digest
    restored_sources = ROOT / "restored_source"

    checks = {
        "formal_result_hash": sha(result_path) == env["formal_result_sha256"],
        "launch_hash": sha(launch_path) == env["first_case_launch_sha256"],
        "controller_events_hash": sha(events_path) == env["first_case_controller_events_sha256"],
        "single_invocation_no_retry": (
            result.get("formal_invocations") == 1
            and result.get("reruns") == 0
            and result.get("replacements") == 0
            and result.get("tuning_after_freeze") == 0
        ),
        "retained_runtime_stop": (
            result.get("decision") == "FAIL_FORMAL_RUNTIME_OR_SCHEMA"
            and result.get("rows") == []
            and result.get("stop", {}).get("case_id") == "p1-immediate"
            and result.get("stop", {}).get("arm") == "IMMEDIATE"
        ),
        "missing_xlib_is_first_failure": all(
            "ModuleNotFoundError" in failure and "No module named" in failure and "Xlib" in failure
            for failure in (result.get("stop", {}).get("error", ""), launch.get("failure", ""))
        ),
        "no_control_or_runtime_evidence": (
            events == []
            and not (formal / "p1-immediate" / "runtime").exists()
            and not env["session_runtime_directory_created"]
            and env["raw_controller_events"] == 0
        ),
        "wheel_omitted_by_recorded_recipe": (
            "python_xlib" not in (ROOT / "DOCKERFILE.local.formal-stop").read_text()
            and env["missing_distribution"] == "python-xlib==0.33"
        ),
        "restored_capsule_source_hashes": bool(frozen_sources)
        and all(
            (restored_sources / name).is_file()
            and sha(restored_sources / name) == digest
            for name, digest in frozen_sources.items()
        ),
        "no_scientific_result_claim": env["scientific_disposition"] == "UNRESOLVED; no task-effect observation",
    }
    return {
        "schema": "map01-attack-onset-formal-stop-audit-v1",
        "pass": all(checks.values()),
        "scope": "stop evidence only; not a scientific result audit",
        "checks": checks,
        "science_claim": False,
    }


if __name__ == "__main__":
    report = audit()
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if report["pass"] else 1)
