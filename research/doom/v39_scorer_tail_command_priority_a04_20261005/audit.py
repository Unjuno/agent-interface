"""Independent raw-only audit for scorer-tail command priority A04."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    raw_path = HERE / "results" / "a04" / "RAW.json"
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    source_checks = {}
    for relative, expected in freeze["sha256"].items():
        actual = sha256(ROOT / relative)
        source_checks[relative] = {"expected": expected, "actual": actual,
                                   "matches": actual == expected}
    tail = raw["tail"]
    checks = {
        "raw_schema": raw.get("schema") == "v39-scorer-tail-command-priority-raw-a04-v1",
        "release_precedes_callback": raw["scenario"]["release_returned_ns"]
        <= raw["scenario"]["callback_start_ns"],
        "callback_crossed_deadline": raw["scenario"]["callback_finish_ns"]
        > raw["scenario"]["tail_deadline_ns"],
        "command_was_ready": raw["scenario"]["command_became_readable_during_callback"] is True,
        "tail_is_censored": tail.get("disposition") == "CENSORED",
        "command_ready_termination": tail.get("termination") == "command_ready",
        "overrun_retained": tail.get("deadline_overrun") is True,
        "one_tail_sample": tail.get("tail_samples") == 1,
        "no_tail_read": raw.get("reads_before_resume") == 0,
        "one_tail_row": len(raw.get("tail_rows", [])) == 1,
        "exact_command_returned": raw.get("command_returned_after_resume") == '{"op":"finish"}',
        "no_extra_sample": raw.get("callback_count_after_resume") == 1,
        "single_read": raw.get("read_count_after_resume") == 1,
        "single_command": raw.get("command_count_after_resume") == 1,
    }
    hashes_pass = all(row["matches"] for row in source_checks.values())
    passed = hashes_pass and all(checks.values())
    audit = {
        "schema": "v39-scorer-tail-command-priority-audit-a04-v1",
        "status": "PASS_CONSTRUCTION" if passed else "FAIL",
        "raw_sha256": sha256(raw_path),
        "source_checks": source_checks,
        "checks": checks,
        "scope": "Deterministic V1 adapter boundary; V2 inheritance covered by adjacent unit suite only. No real stdin, Doom, model, task effect, recovery, or MAP01 outcome.",
    }
    result = {
        "schema": "v39-scorer-tail-command-priority-result-a04-v1",
        "status": audit["status"],
        "candidate_invocations": 1,
        "auditor_invocations": 1,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "raw_sha256": audit["raw_sha256"],
        "scope": audit["scope"],
    }
    (HERE / "AUDIT.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (HERE / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
