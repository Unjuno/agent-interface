"""Independent raw-result and source-pin audit for the A03 socketpair probe."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
EXPECTED_CASES = ("ready_at_entry", "slow_callback", "normal_wait")
EXPECTED_SAMPLES = {"ready_at_entry": 0, "slow_callback": 1, "normal_wait": 1}
COMMAND = '{"op":"finish"}\n'


def _blob(commit: str, path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{commit}:{path}"])


def audit(result: dict) -> dict:
    errors: list[str] = []
    freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
    if result.get("schema") != "issue59-scorer-tail-command-priority-result-v3":
        errors.append("result schema mismatch")
    if result.get("run_id") != freeze.get("run_id"):
        errors.append("run identity mismatch")
    if result.get("source_commit") != freeze.get("source_commit"):
        errors.append("result source commit mismatch")
    source_checks = {}
    for item in freeze.get("source_files", []):
        path = ROOT / "source" / Path(item["path"]).name
        try:
            raw = path.read_bytes()
            committed = _blob(freeze["source_commit"], item["path"])
            source_checks[item["path"]] = (
                len(raw) == item["bytes"]
                and hashlib.sha256(raw).hexdigest() == item["sha256"]
                and hashlib.sha256(committed).hexdigest() == item["sha256"]
                and committed == raw
            )
        except (OSError, KeyError, subprocess.CalledProcessError):
            source_checks[item["path"]] = False
        if not source_checks[item["path"]]:
            errors.append(f"frozen source mismatch: {item['path']}")

    rows = result.get("cases")
    if type(rows) is not list or [row.get("case") for row in rows] != list(EXPECTED_CASES):
        errors.append("case sequence mismatch")
        rows = rows if type(rows) is list else []
    reconstructed = {}
    for row in rows:
        name = row.get("case")
        if name not in EXPECTED_SAMPLES:
            errors.append(f"unknown case: {name}")
            continue
        expected_samples = EXPECTED_SAMPLES[name]
        checks = {
            "termination": row.get("termination") == "command_ready",
            "disposition": row.get("disposition") == "CENSORED",
            "tail_samples": row.get("tail_samples") == expected_samples,
            "not_overrun": row.get("deadline_overrun") is False,
            "unread_after_tail": row.get("unread_command_after_tail") == COMMAND,
            "delivered_once": row.get("delivered_command") == COMMAND
                and row.get("commands_delivered") == 1,
            "resume_count_consistent": row.get("resume_samples")
                == row.get("samples_total_after_resume") - expected_samples,
            "sender_ok": row.get("sender_error") is None,
        }
        reconstructed[name] = checks
        errors.extend(f"{name}: {key}" for key, okay in checks.items() if not okay)
    passed = not errors and len(reconstructed) == len(EXPECTED_CASES)
    return {
        "schema": "issue59-scorer-tail-command-priority-audit-v3",
        "disposition": "PASS_COMMAND_PRIORITY_REPAIR_CONSTRUCTION"
            if passed else "FAIL_OR_STOP",
        "passed": sum(sum(checks.values()) for checks in reconstructed.values())
            + sum(source_checks.values()),
        "total": sum(len(checks) for checks in reconstructed.values())
            + len(source_checks),
        "source_checks": source_checks,
        "case_checks": reconstructed,
        "errors": errors,
        "scope": "frozen source and Windows socketpair readiness only",
    }


if __name__ == "__main__":
    result = json.loads((ROOT / "results" / "a03" / "RESULT.json")
                        .read_text(encoding="utf-8"))
    report = audit(result)
    (ROOT / "results" / "a03" / "AUDIT.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if report["disposition"].startswith("PASS_") else 1)
