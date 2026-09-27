"""Raw-only auditor for the Issue #3066 v4 immediate-recovery allocation."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ALLOCATION = "safety-graph-live-x11-3066-20260927-v4-01"
CONFIGS = ("bare", "openbox")
DEADLINE_MS = 150
GRACE_MS = 50


def score(raw: Any) -> dict[str, Any]:
    issues: list[str] = []
    evidence: list[dict[str, Any]] = []
    expected = {(name, "cleanup_failure") for name in CONFIGS}
    if isinstance(raw, list) and any(isinstance(row, dict) and row.get("construction_only") is True for row in raw):
        return {"decision": "HOLD_CONSTRUCTION_ROWS_NOT_FORMAL", "issues": ["CONSTRUCTION_ROWS_NOT_FORMAL"], "cases": []}
    if not isinstance(raw, list) or len(raw) != len(expected):
        return {"decision": "HOLD_RECOVERY_EVIDENCE_INCOMPLETE", "issues": ["DENOMINATOR_INVALID"], "cases": []}
    found = {(r.get("config"), r.get("schedule")) for r in raw if isinstance(r, dict)}
    if found != expected or len(found) != len(raw):
        issues.append("CASE_IDENTITY_MISMATCH")

    for row in raw:
        identity = f"{row.get('config')}/{row.get('schedule')}" if isinstance(row, dict) else "invalid-row"
        if not isinstance(row, dict):
            issues.append(f"{identity}:ROW_NOT_OBJECT")
            continue
        if row.get("allocation") != ALLOCATION:
            issues.append(f"{identity}:ALLOCATION_MISMATCH")
        start = row.get("worker_start_receipt")
        receipt = row.get("worker_receipt")
        observed_ns = row.get("recovery_receipt_observed_ns")
        supervisor = row.get("supervisor_release")
        if not all(isinstance(v, dict) for v in (start, receipt, supervisor)):
            issues.append(f"{identity}:REQUIRED_RECEIPT_MISSING")
            continue
        dispatch = receipt.get("dispatch_result")
        runtime = dispatch.get("result") if isinstance(dispatch, dict) else None
        if not isinstance(runtime, dict) or not isinstance(observed_ns, int):
            issues.append(f"{identity}:RECOVERY_TRIGGER_PROVENANCE_MISSING")
            continue

        typed = runtime.get("status") == "execution_failed" and runtime.get("recovery_required") is True
        if not typed:
            issues.append(f"{identity}:TYPED_RECOVERY_NOT_EXPOSED")
        if runtime.get("error") != "BACKEND_EXECUTION_FAILED":
            issues.append(f"{identity}:EXPECTED_CLEANUP_FAILURE_NOT_OBSERVED")
        if row.get("worker_returncode") != 0:
            issues.append(f"{identity}:WORKER_EXIT_NOT_ZERO")
        if row.get("supervisor_attempt_count") is None:
            issues.append(f"{identity}:SUPERVISOR_ATTEMPT_COUNT_MISSING")
        elif row.get("supervisor_attempt_count") != 1:
            issues.append(f"{identity}:SUPERVISOR_ATTEMPT_COUNT_NOT_ONE")

        deadline = start.get("authority_deadline_ns")
        began = supervisor.get("started_ns")
        finished = supervisor.get("finished_ns")
        limit = deadline + GRACE_MS * 1_000_000 if isinstance(deadline, int) else None
        release = supervisor.get("release")
        if not isinstance(deadline, int) or not isinstance(began, int) or not isinstance(finished, int) or not isinstance(release, dict):
            issues.append(f"{identity}:SUPERVISOR_TIMING_OR_RELEASE_MISSING")
            continue
        if began < observed_ns:
            issues.append(f"{identity}:SUPERVISOR_PRECEDES_TRIGGER_OBSERVATION")
        if finished < began:
            issues.append(f"{identity}:SUPERVISOR_CLOCK_ORDER_INVALID")
        if isinstance(limit, int) and finished > limit:
            issues.append(f"{identity}:SUPERVISOR_FINISH_AFTER_DEADLINE_PLUS_GRACE")
        if release.get("verified") is not True or release.get("keys_down") != [] or release.get("buttons_down") != []:
            issues.append(f"{identity}:SUPERVISOR_RELEASE_UNVERIFIED")
        if row.get("terminal_key_down") is not False or row.get("post_cleanup_key_down") is not False:
            issues.append(f"{identity}:TERMINAL_INPUT_NOT_UP")

        transitions = row.get("keymap_transitions")
        ups = [
            x.get("observed_ns") for x in transitions if isinstance(x, dict)
            and x.get("kind") == "transition" and x.get("down") is False
            and isinstance(x.get("observed_ns"), int)
        ] if isinstance(transitions, list) else []
        keymap_up = min(ups) if ups else None
        if keymap_up is None:
            issues.append(f"{identity}:INDEPENDENT_KEYMAP_RELEASE_MISSING")
        elif keymap_up < began:
            issues.append(f"{identity}:KEYMAP_RELEASE_PRECEDES_SUPERVISOR")
        elif isinstance(limit, int) and keymap_up > limit:
            issues.append(f"{identity}:KEYMAP_RELEASE_AFTER_DEADLINE_PLUS_GRACE")

        evidence.append({
            "case": identity,
            "typed_recovery_required": typed,
            "deadline_ns": deadline,
            "recovery_receipt_observed_ns": observed_ns,
            "supervisor_started_ns": began,
            "supervisor_finished_ns": finished,
            "supervisor_finish_after_deadline_ms": round((finished - deadline) / 1_000_000, 6),
            "keymap_release_upper_bound_ns": keymap_up,
            "keymap_release_after_deadline_ms": round((keymap_up - deadline) / 1_000_000, 6) if keymap_up is not None else None,
            "deadline_plus_grace_ns": limit,
        })

    fail_markers = (
        "TYPED_RECOVERY_NOT_EXPOSED",
        "EXPECTED_CLEANUP_FAILURE_NOT_OBSERVED",
        "WORKER_EXIT_NOT_ZERO",
        "SUPERVISOR_ATTEMPT_COUNT_NOT_ONE",
        "SUPERVISOR_PRECEDES_TRIGGER_OBSERVATION",
        "SUPERVISOR_FINISH_AFTER_DEADLINE_PLUS_GRACE",
        "SUPERVISOR_RELEASE_UNVERIFIED",
        "TERMINAL_INPUT_NOT_UP",
        "KEYMAP_RELEASE_PRECEDES_SUPERVISOR",
        "KEYMAP_RELEASE_AFTER_DEADLINE_PLUS_GRACE",
    )
    if not issues and len(evidence) == 2:
        decision = "PASS_EARLY_SUPERVISOR_RECOVERY_SCOPED"
    elif any(any(marker in issue for marker in fail_markers) for issue in issues):
        decision = "FAIL_EARLY_SUPERVISOR_RECOVERY"
    else:
        decision = "HOLD_RECOVERY_EVIDENCE_INCOMPLETE"
    return {"decision": decision, "issues": issues, "cases": evidence}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("raw", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    raw_bytes = args.raw.read_bytes()
    raw = json.loads(raw_bytes)
    result = score(raw)
    result["allocation"] = ALLOCATION
    result["raw_sha256"] = hashlib.sha256(raw_bytes).hexdigest()
    result["raw_bytes"] = len(raw_bytes)
    args.out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"decision": result["decision"], "issues": result["issues"], "raw_sha256": result["raw_sha256"]}, sort_keys=True))
    return 0 if result["decision"] == "PASS_EARLY_SUPERVISOR_RECOVERY_SCOPED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
