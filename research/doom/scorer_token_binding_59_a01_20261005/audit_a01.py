from __future__ import annotations

import hashlib
import json
from pathlib import Path

PKG = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[3]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    freeze = json.loads((PKG / "FREEZE.json").read_text(encoding="utf-8"))
    cases = json.loads((PKG / "cases.json").read_text(encoding="utf-8"))
    raw = json.loads((PKG / "results/a01/raw.json").read_text(encoding="utf-8"))
    expected = cases["expected"]
    observed = raw["cases"]
    checks = {
        "frozen_allocation_once_no_retry": (raw.get("allocation_id") ==
                                             "SCORER-INTENT-TOKEN-BINDING-59-A01-20261005-01"
                                             and raw.get("candidate_invocations") == 1
            and raw.get("retries") == 0
            and raw.get("frozen_runner_invocations") == 1
            and raw.get("baseline_evaluations") == 1
            and raw.get("successor_evaluations") == 3),
        "frozen_source_head": raw.get("source_head") ==
                              "a2f85482c6968f9caa9dcbca017bd452b8a2c3b3",
        "parent_source_hashes_match": (
            raw["source_sha256"]["parent_candidate.py"] ==
            digest(ROOT / "research/doom/scorer_eventlog_join_t0_v1/candidate.py")
            and raw["source_sha256"]["parent_file_join.py"] ==
            digest(ROOT / "research/doom/scorer_eventlog_join_t0_v1/file_join.py")),
        "candidate_and_case_hashes_match": (
            raw["source_sha256"]["candidate_v2.py"] == digest(PKG / "candidate_v2.py")
            and raw["source_sha256"]["cases.json"] == digest(PKG / "cases.json")
            and raw["source_sha256"]["run_a01.py"] == digest(PKG / "run_a01.py")
            and raw["source_sha256"]["audit_a01.py"] == digest(PKG / "audit_a01.py")
            and raw["source_sha256"] == freeze["source_sha256"]),
        "input_hash_reconciles": raw.get("input_sha256") == hashlib.sha256(
            json.dumps(cases, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "baseline_false_accept_reproduced": (
            observed["baseline_mismatched_token"].get("decision") ==
            expected["baseline_mismatched_token"]),
        "matched_token_positive_preserved": (
            observed["candidate_matched_token"].get("decision") ==
            expected["candidate_matched_token"]),
        "mismatched_token_rejected": (
            observed["candidate_mismatched_token"].get("decision") ==
            expected["candidate_mismatched_token"]
            and observed["candidate_mismatched_token"].get("reason") ==
            "intent_token_mismatch"),
        "missing_token_rejected": (
            observed["candidate_missing_admission_token"].get("decision") ==
            expected["candidate_missing_admission_token"]
            and observed["candidate_missing_admission_token"].get("reason") ==
            "missing_input_intent_token"),
        "candidate_gate_matches_observations": (raw.get("gate_checks") == {
            "baseline_false_accept_reproduced": expected["baseline_mismatched_token"] ==
                                                observed["baseline_mismatched_token"].get("decision"),
            "matched_token_positive_preserved": expected["candidate_matched_token"] ==
                                                observed["candidate_matched_token"].get("decision"),
            "mismatched_token_rejected": expected["candidate_mismatched_token"] ==
                                          observed["candidate_mismatched_token"].get("decision")
                                          and observed["candidate_mismatched_token"].get("reason") == "intent_token_mismatch",
            "missing_token_rejected": expected["candidate_missing_admission_token"] ==
                                       observed["candidate_missing_admission_token"].get("decision")
                                       and observed["candidate_missing_admission_token"].get("reason") == "missing_input_intent_token",
        }),
        "monotonic_run_bracket": type(raw.get("started_monotonic_ns")) is int
                                 and type(raw.get("finished_monotonic_ns")) is int
                                 and raw["started_monotonic_ns"] <= raw["finished_monotonic_ns"],
        "scope_not_promoted": (raw.get("execution_environment", {}).get("containerized")
                                is False),
    }
    passed = all(checks.values())
    report = {
        "schema": "scorer-intent-token-binding-a01-independent-audit-v1",
        "status": "PASS_RAW_AUDIT" if passed else "FAIL_RAW_AUDIT",
        "errors": [name for name, ok in checks.items() if not ok],
        "checks": checks,
    }
    out = PKG / "results/a01/audit.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
