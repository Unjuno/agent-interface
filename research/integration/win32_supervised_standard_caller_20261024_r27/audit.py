"""Frozen R27 public dispatch/retrieval/effect audit."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
C = json.loads((P / "conditions.json").read_text(encoding="utf-8"))
R = json.loads((P / "raw.json").read_text(encoding="utf-8"))
F = json.loads((P / "preflight.json").read_text(encoding="utf-8"))
REPORT = R.get("retained_report", {})
ACTION = REPORT.get("supervision", {}).get("action", {})
RESULT = REPORT.get("result", {})
CUSTODY = ACTION.get("completion_custody", {})
RELEASE = CUSTODY.get("completion_release_receipt", {})
EVENTS = R.get("fixture_events", [])
CHARS = [e for e in EVENTS if e.get("kind") == "char"]
SAVES = [e for e in EVENTS if e.get("kind") == "save"]
RETRIEVALS = R.get("result_retrievals", [])
CALL_ID = R.get("public_response", {}).get("call_id")
TERMINAL_NS = R.get("result_retrieval_terminal_monotonic_ns", 0)
START_NS = R.get("dispatch", {}).get("started_monotonic_ns", 0)
PENDING_NS = R.get("dispatch", {}).get("returned_monotonic_ns", 0)
RETRIEVAL_START_NS = RETRIEVALS[0].get("started_monotonic_ns", 0) if RETRIEVALS else 0
EXPECTED = C["trial"]["expected_effect"]
hashes = {name: hashlib.sha256((P / name).read_bytes()).hexdigest()
          for name in C["frozen_files"]}

checks = {
    "input_free_preflight_passed": F.get("status") == "PASS",
    "frozen_attempt_and_source_match": (
        R.get("attempt_id") == C["attempt_id"]
        and R.get("source_commit") == C["source_commit"]),
    "frozen_packet_hashes_match": hashes == C["frozen_files"],
    "predecessor_chain_hashes_match": (
        F.get("checks", {}).get("predecessor_hashes_match") is True
        and F.get("checks", {}).get("predecessor_semantics") is True
        and F.get("checks", {}).get("previous_no_input_attempt_hashes_match") is True
        and F.get("checks", {}).get("previous_no_input_attempt_semantics") is True),
    "new_target_generation_matches_owned_fixture": (
        R.get("observation_target_generation_consistency") == "matched"
        and R.get("observed_target_generation") ==
            R.get("target_identity_before", {}).get("generation")
        and R.get("observed_target_generation") != C["predecessor"]["target_generation"]
        and R.get("target_identity_before") == R.get("target_identity_after")
        and R.get("target_identity_before", {}).get("owner", {}).get("pid") == R.get("fixture_pid")),
    "single_pending_public_dispatch": (
        R.get("dispatch_attempts") == 1
        and R.get("program_validation", {}).get("static_valid") is True
        and R.get("public_response", {}).get("status") == "pending"
        and R.get("public_response", {}).get("call_id") == CALL_ID
        and R.get("public_response", {}).get("call", {}).get("response_wait_ms") == 10000
        and R.get("public_response", {}).get("replay_allowed") is False),
    "exact_call_id_read_only_poll_and_terminal_result": (
        bool(RETRIEVALS)
        and all(row.get("call_id") == CALL_ID
                and row.get("operation_invoked") is False
                and row.get("input_dispatched") is False
                for row in RETRIEVALS)
        and RETRIEVALS[-1].get("action_status") == "completed"
        and R.get("result_retrieval_status") == "completed"
        and R.get("retrieved_call_result", {}).get("call_id") == CALL_ID
        and ACTION.get("status") == "completed"
        and RESULT.get("status") == "completed"),
    "retrieval_within_finite_budget": (
        0 < TERMINAL_NS - RETRIEVAL_START_NS
            <= C["retrieval"]["deadline_seconds"] * 1_000_000_000
        and TERMINAL_NS >= PENDING_NS),
    "verified_all_up_release_before_terminal_retrieval": (
        RELEASE.get("verified") is True
        and RELEASE.get("keys_down") == []
        and RELEASE.get("buttons_down") == []
        and RELEASE.get("keys_unknown") == []
        and RELEASE.get("buttons_unknown") == []
        and RELEASE.get("monotonic_ns", 0) <= TERMINAL_NS
        and ACTION.get("release_confirmed") is True),
    "producer_exit_and_neutral_readback": (
        CUSTODY.get("producer_exit_code") == 0
        and CUSTODY.get("completion_readback", {}).get("neutral") is True
        and CUSTODY.get("completion_readback", {}).get("target_generation")
            == R.get("observed_target_generation")),
    "independent_exact_effect_and_events": (
        R.get("effect_file") == EXPECTED
        and R.get("oracle", {}).get("task_pass") is True
        and R.get("oracle", {}).get("event_text") == EXPECTED["text"]
        and len(CHARS) == len(EXPECTED["text"])
        and len(SAVES) == 1
        and sum(e.get("kind") == "click" for e in EVENTS) == 1
        and START_NS <= SAVES[0].get("commit_completed_monotonic_ns", 0)
            <= TERMINAL_NS),
    "public_close_and_owned_cleanup": (
        R.get("public_close", {}).get("response", {}).get("status") == "closed"
        and R.get("fixture_close_posted") is True
        and R.get("fixture_exit_code") == 0),
    "foreground_restored_and_runtime_success_unclaimed": (
        R.get("foreground_restore", {}).get("observed_hwnd")
            == R.get("previous_foreground_hwnd")
        and RESULT.get("task_success") is None
        and ACTION.get("task_success") is None),
    "raw_status_pass": R.get("status") == "PASS",
}
audit = {"schema": "win32-supervised-standard-caller-r27-audit-v1",
         "attempt_id": C["attempt_id"], "checks": checks,
         "passed": sum(checks.values()), "total": len(checks),
         "status": "PASS" if all(checks.values()) else "FAIL_OR_UNKNOWN",
         "nonclaims": C["nonclaims"]}
(P / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n",
                               encoding="utf-8")
print(json.dumps(audit, indent=2, sort_keys=True))
raise SystemExit(0 if all(checks.values()) else 1)
