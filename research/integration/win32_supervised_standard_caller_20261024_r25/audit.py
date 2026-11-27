"""Independent frozen-condition audit for the R25 terminal-response trial."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

PACKET = Path(__file__).resolve().parent
C = json.loads((PACKET / "conditions.json").read_text(encoding="utf-8"))
RAW = json.loads((PACKET / "raw.json").read_text(encoding="utf-8"))
PREFLIGHT = json.loads((PACKET / "preflight.json").read_text(encoding="utf-8"))
EFFECT = C["trial"]["expected_effect"]
REPORT = RAW.get("retained_report", {})
RESULT = REPORT.get("result", {})
RELEASES = RESULT.get("execution", {}).get("releases", [])
RELEASE = RELEASES[-1] if RELEASES else {}
EVENTS = RAW.get("fixture_events", [])
CHARS = [e for e in EVENTS if e.get("kind") == "char"]
SAVES = [e for e in EVENTS if e.get("kind") == "save"]
packet_hashes = {name: hashlib.sha256((PACKET / name).read_bytes()).hexdigest()
                 for name in C["frozen_files"]}

checks = {
    "input_free_preflight_passed": PREFLIGHT.get("status") == "PASS",
    "frozen_attempt_and_source_match": (
        RAW.get("attempt_id") == C["attempt_id"]
        and RAW.get("source_commit") == C["source_commit"]),
    "frozen_packet_hashes_match": packet_hashes == C["frozen_files"],
    "predecessor_hashes_and_r24_boundary_match": (
        PREFLIGHT.get("checks", {}).get("predecessor_hashes_match") is True
        and PREFLIGHT.get("checks", {}).get("predecessor_semantics") is True
        and RAW.get("predecessor", {}).get("attempt_id") == C["predecessor"]["attempt_id"]),
    "new_public_session_and_generation": (
        RAW.get("session_mode") == "supervised-win32"
        and RAW.get("caller_kind") == "mcp_stdio"
        and RAW.get("observation_target_generation_consistency") == "matched"
        and RAW.get("observed_target_generation") ==
            RAW.get("target_identity_before", {}).get("generation")
        and RAW.get("observed_target_generation") != C["predecessor"]["target_generation"]
        and RAW.get("target_identity_before") == RAW.get("target_identity_after")),
    "single_dispatch_returned_completed": (
        RAW.get("dispatch_attempts") == 1
        and RAW.get("dispatch", {}).get("is_error") is False
        and RAW.get("public_response", {}).get("status") == "returned"
        and RESULT.get("status") == "completed"
        and RAW.get("public_response", {}).get("call", {}).get("state") == "completed"),
    "runtime_success_unclaimed": RESULT.get("task_success") is None,
    "exact_independent_fixture_effect": (
        RAW.get("effect_file") == EFFECT
        and RAW.get("oracle", {}).get("task_pass") is True
        and RAW.get("oracle", {}).get("event_text") == EFFECT["text"]
        and len(CHARS) == len(EFFECT["text"])
        and len(SAVES) == 1
        and sum(e.get("kind") == "click" for e in EVENTS) == 1),
    "verified_all_up_release_and_timing": (
        len(RELEASES) == 1
        and RELEASE.get("verified") is True
        and RELEASE.get("keys_down") == []
        and RELEASE.get("buttons_down") == []
        and RELEASE.get("keys_unknown") == []
        and RELEASE.get("buttons_unknown") == []
        and RAW.get("timing", {}).get("release_receipt_monotonic_ns") ==
            RELEASE.get("monotonic_ns")
        and RAW.get("timing", {}).get("dispatch_start_monotonic_ns", 0)
            <= RELEASE.get("monotonic_ns", -1)
        and RELEASE.get("monotonic_ns", 0)
            <= RAW.get("dispatch", {}).get("returned_monotonic_ns", -1)),
    "public_close_closed_and_fixture_cleanup": (
        RAW.get("public_close", {}).get("response", {}).get("status") == "closed"
        and RAW.get("fixture_close_posted") is True
        and RAW.get("fixture_exit_code") == 0
        and RAW.get("target_identity_after", {}).get("owner", {}).get("pid")
            == RAW.get("fixture_pid")),
    "foreground_restored": (
        RAW.get("foreground_restore", {}).get("observed_hwnd")
        == RAW.get("previous_foreground_hwnd")),
    "raw_pass": RAW.get("status") == "PASS",
}

audit = {"schema": "win32-supervised-standard-caller-r25-audit-v1",
         "attempt_id": C["attempt_id"], "checks": checks,
         "passed": sum(checks.values()), "total": len(checks),
         "status": "PASS" if all(checks.values()) else "FAIL_OR_UNKNOWN",
         "nonclaims": C["nonclaims"]}
(PACKET / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n",
                                   encoding="utf-8")
print(json.dumps(audit, indent=2, sort_keys=True))
raise SystemExit(0 if all(checks.values()) else 1)
