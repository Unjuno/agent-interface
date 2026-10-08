"""Independent integrity and decision audit for the retained A01 run."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit() -> dict:
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    result = json.loads((HERE / "RESULT.json").read_text(encoding="utf-8-sig"))
    checks = []

    def check(name, passed, detail):
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    sources_ok = True
    for item in freeze["files"]:
        path = ROOT / item["path"]
        if not path.is_file() or sha256(path) != item["sha256"]:
            sources_ok = False
    check("frozen_source_and_input_hashes", sources_ok,
          f"{len(freeze['files'])} frozen files compared by SHA-256")

    raw_path = ROOT / freeze["input_path"]
    rows = [json.loads(line) for line in raw_path.read_text(encoding="utf-8").splitlines()]
    down = next((row for row in rows if row.get("event") == "input_admission"), None)
    up = next((row for row in rows if row.get("event") == "input_release_measurement"), None)
    identity_ok = bool(down and up) and all(
        down.get(field) == up.get(field) for field in ("id", "step", "key", "owner_id", "intent_token"))
    physical = (up or {}).get("physical_key_measurement", {})
    edge = physical.get("adapter_edge", {})
    interval = edge.get("interval")
    measured_boundary = (interval[1] if isinstance(interval, list) and len(interval) == 2
                         and all(type(value) is int for value in interval) else None)
    evidence_ok = (
        identity_ok
        and down.get("event") == "input_admission"
        and up.get("event") == "input_release_measurement"
        and down.get("grants_input_authority") is False
        and up.get("grants_input_authority") is False
        and physical.get("application_consumption_observed") is False
        and edge.get("edge") == "up"
        and edge.get("status") == "CONFIRMED_PHYSICAL_UP"
        and measured_boundary == freeze["expected_release_boundary_ns"]
    )
    check("raw_event_join_and_release_boundary", evidence_ok,
          f"event pair={bool(down and up)}; boundary_ns={measured_boundary}; "
          "raw event labels and authority/consumption flags preserved")

    expected_runs = {"WSL_TEST_OUTPUT.txt": "wsl_core",
                     "WINDOWS_TEST_OUTPUT.txt": "windows_compatibility"}
    outputs_ok = True
    run_summaries = {}
    for filename, key in expected_runs.items():
        output_path = HERE / filename
        text = output_path.read_text(encoding="utf-8-sig") if output_path.is_file() else ""
        match = re.search(r"Ran (\d+) tests? in [^\r\n]+", text)
        exit_code = result.get("exit_codes", {}).get(key)
        passed = match is not None and "\nOK" in text and "\nFAILED" not in text and exit_code == 0
        outputs_ok &= passed
        run_summaries[key] = {"test_count": int(match.group(1)) if match else None,
                              "exit_code": exit_code}
    check("retained_test_run_outputs", outputs_ok, json.dumps(run_summaries, sort_keys=True))

    claims_ok = (result.get("experiment_id") == freeze["experiment_id"]
                 and result.get("disposition") == "PASS"
                 and result.get("expected_release_boundary_ns") == measured_boundary
                 and result.get("scope", "").startswith("construction-only"))
    check("result_scope_and_preregistered_decision", claims_ok,
          "result identity, PASS gate, expected boundary, and construction-only scope agree")
    passed = all(item["passed"] for item in checks)
    return {
        "schema": "v39-perkey-scorer-tail-a01-independent-audit-v1",
        "experiment_id": freeze["experiment_id"],
        "auditor": "audit.py independent raw JSON/hash/output checks",
        "disposition": "PASS_AUDIT" if passed else "FAIL_AUDIT",
        "checks": checks,
        "limits": ["fake-display input trace", "no live game or OS input",
                   "no application-consumption or task-effect evidence"],
    }


if __name__ == "__main__":
    report = audit()
    (HERE / "AUDIT.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                                     encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if report["disposition"] == "PASS_AUDIT" else 1)
