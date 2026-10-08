"""Independent raw-only audit for #5066; imports neither runner nor protocol."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

OUT = Path("/out")
OLD = 3788
NEW = 3789
PHASE_GENERATION = {
    "atomic_before_validation": OLD,
    "atomic_candidate_ready_unpublished": OLD,
    "atomic_after_publish": NEW,
    "invalid_candidate_refused": NEW,
    "diagnostic_before_write": OLD,
    "diagnostic_partial_write": None,
    "diagnostic_after_write": NEW,
}
PHASES = tuple(PHASE_GENERATION)
READERS = 4
EXPECTED_INPUT_SHA256 = "2e7bff5a2c6ffd35935c5e3c88d08cb686fb736d332c8d5cdb24bb1b67dc873a"
EXPECTED_IMAGE_ID = "sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9"


def validate(raw: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(raw, dict):
        return ["raw_not_object"]
    for key, value in {
        "allocation": "needle-cross-process-publication-5045-v2-20260928-01",
        "issue": 5066,
        "formal_invocations": 1,
        "reader_count_per_arm": READERS,
        "dispatch_count": 0,
        "authority_granted": False,
        "input_git_blob": "45b80150dac503f4eb6f3cb5d82f9afa2c587107",
        "input_sha256": EXPECTED_INPUT_SHA256,
        "old_raw_sha256": EXPECTED_INPUT_SHA256,
        "image_id": EXPECTED_IMAGE_ID,
    }.items():
        if raw.get(key) != value:
            errors.append("top_" + key)
    arms = raw.get("arms")
    if not isinstance(arms, list) or len(arms) != 2:
        return errors + ["arm_count"]
    by_arm = {a.get("arm"): a for a in arms if isinstance(a, dict)}
    if set(by_arm) != {"atomic", "diagnostic"}:
        return errors + ["arm_names"]
    if raw.get("query_count") != 28:
        errors.append("query_count")
    for name in ("atomic", "diagnostic"):
        arm = by_arm[name]
        if not isinstance(arm.get("publisher_pid"), int):
            errors.append(name + "_publisher_pid")
        pids = arm.get("reader_pids")
        if not isinstance(pids, list) or len(pids) != READERS or len(set(pids)) != READERS:
            errors.append(name + "_reader_pid_roster")
        elif arm.get("publisher_pid") in pids:
            errors.append(name + "_publisher_reader_pid_collision")
        exits = arm.get("reader_exit_codes")
        if exits != [0] * READERS:
            errors.append(name + "_reader_exit_codes")
        rows = arm.get("observations")
        expected_phases = PHASES[4:] if name == "diagnostic" else PHASES[:4]
        if not isinstance(rows, list) or len(rows) != len(expected_phases) * READERS:
            errors.append(name + "_observation_count")
            continue
        seen = set()
        for row in rows:
            if not isinstance(row, dict):
                errors.append(name + "_row_type")
                continue
            phase = row.get("phase")
            index = row.get("reader_index")
            key = (phase, index)
            if phase not in expected_phases:
                errors.append(name + "_phase")
                continue
            if index not in range(READERS) or key in seen:
                errors.append(name + "_reader_or_duplicate")
                continue
            seen.add(key)
            if row.get("pid") != arm["reader_pids"][index]:
                errors.append(name + "_pid_binding")
            if not isinstance(row.get("bytes"), int) or not isinstance(row.get("raw_sha256"), str):
                errors.append(name + "_raw_identity")
            expected = PHASE_GENERATION[phase]
            if expected is not None:
                if row.get("generation") != expected or row.get("package_valid") is not True:
                    errors.append(name + "_generation_" + phase)
                expected_payload = raw.get("old_payload_sha256") if expected == OLD else raw.get("candidate_sha256")
                expected_bytes = raw.get("old_raw_sha256") if expected == OLD else raw.get("candidate_raw_sha256")
                expected_length = raw.get("input_bytes") if expected == OLD else raw.get("candidate_raw_bytes")
                if (row.get("embedded_digest") != expected_payload or row.get("raw_sha256") != expected_bytes
                        or row.get("bytes") != expected_length):
                    errors.append(name + "_exact_package_" + phase)
            elif row.get("package_valid") is True:
                errors.append("diagnostic_partial_not_observed")
            else:
                if row.get("parse_ok") is not False or row.get("generation") is not None:
                    errors.append("diagnostic_partial_parse_state")
                if not (0 < row.get("bytes", 0) < raw.get("candidate_raw_bytes", 0)):
                    errors.append("diagnostic_partial_byte_range")
        if seen != {(phase, i) for phase in expected_phases for i in range(READERS)}:
            errors.append(name + "_schedule_incomplete")
    atomic = by_arm["atomic"]
    stale = atomic.get("stale_proposal", {})
    current = atomic.get("current_proposal", {})
    if stale.get("generation") != OLD or stale.get("active_generation") != NEW or stale.get("disposition") != "YIELD_STALE_GENERATION" or stale.get("dispatch") is not False:
        errors.append("stale_proposal")
    if current.get("generation") != NEW or current.get("active_generation") != NEW or current.get("disposition") != "ELIGIBLE_PROPOSAL_ONLY" or current.get("dispatch") is not False:
        errors.append("current_proposal")
    if atomic.get("invalid_candidate_accepted") is not False:
        errors.append("invalid_candidate_accepted")
    if atomic.get("active_before_invalid_sha256") != atomic.get("active_after_invalid_sha256"):
        errors.append("invalid_candidate_mutated_active")
    diagnostic = by_arm["diagnostic"]
    partial_rows = [r for r in diagnostic.get("observations", []) if r.get("phase") == "diagnostic_partial_write"]
    if diagnostic.get("partial_invalid_reader_count") != sum(r.get("package_valid") is not True for r in partial_rows):
        errors.append("partial_invalid_count")
    if not any(r.get("package_valid") is not True for r in partial_rows):
        errors.append("partial_not_exposed")
    if diagnostic.get("dispatch_count") != 0:
        errors.append("diagnostic_dispatch")
    return errors


def corruption_controls(raw: dict) -> dict[str, bool]:
    cases: dict[str, dict] = {}
    changed = copy.deepcopy(raw)
    changed["query_count"] = 27
    cases["missing_query"] = changed
    changed = copy.deepcopy(raw)
    changed["authority_granted"] = True
    cases["authority_escalation"] = changed
    changed = copy.deepcopy(raw)
    changed["arms"][0]["observations"][0]["generation"] = NEW
    cases["prepublication_new_generation"] = changed
    changed = copy.deepcopy(raw)
    changed["arms"][1]["observations"][5]["package_valid"] = True
    cases["partial_claimed_valid"] = changed
    changed = copy.deepcopy(raw)
    changed["arms"][0]["stale_proposal"]["disposition"] = "ELIGIBLE_PROPOSAL_ONLY"
    cases["stale_proposal_admitted"] = changed
    changed = copy.deepcopy(raw)
    changed["arms"][0]["active_after_invalid_sha256"] = "0" * 64
    cases["invalid_candidate_mutation"] = changed
    changed = copy.deepcopy(raw)
    changed["arms"][0]["reader_pids"][0] = changed["arms"][0]["publisher_pid"]
    cases["publisher_reader_pid_collision"] = changed
    changed = copy.deepcopy(raw)
    changed["dispatch_count"] = 1
    cases["dispatch_emitted"] = changed
    changed = copy.deepcopy(raw)
    changed["arms"][0]["reader_exit_codes"][0] = 137
    cases["reader_process_failed"] = changed
    changed = copy.deepcopy(raw)
    changed["candidate_raw_sha256"] = "0" * 64
    cases["wrong_candidate_bytes"] = changed
    changed = copy.deepcopy(raw)
    changed["arms"][1]["observations"][5]["bytes"] = raw.get("candidate_raw_bytes")
    cases["partial_full_length"] = changed
    changed = copy.deepcopy(raw)
    changed["arms"][0]["observations"][0]["bytes"] = raw.get("input_bytes", 0) + 1
    cases["wrong_complete_length"] = changed
    return {name: bool(validate(case)) for name, case in cases.items()}


def main() -> int:
    raw_path = OUT / "raw.json"
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    errors = validate(raw)
    controls = corruption_controls(raw)
    report = {
        "status": "PASS_CROSS_PROCESS_PUBLICATION_SCOPED" if not errors and all(controls.values()) else "FAIL_AUDIT",
        "audit_errors": errors,
        "corruption_controls_rejected": sum(controls.values()),
        "corruption_controls_total": len(controls),
        "corruption_control_results": controls,
        "raw_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
        "query_count": raw.get("query_count"),
        "scope": "single-host Linux local-filesystem multi-process synthetic package publication",
    }
    (OUT / "audit.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "PASS_CROSS_PROCESS_PUBLICATION_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())



