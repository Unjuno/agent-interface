"""Independent frozen-condition audit for the R24 one-shot receipt."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

PACKET = Path(__file__).resolve().parent
CONDITIONS = json.loads((PACKET / "conditions.json").read_text(encoding="utf-8"))
RAW = json.loads((PACKET / "raw.json").read_text(encoding="utf-8"))
PREFLIGHT = json.loads((PACKET / "preflight.json").read_text(encoding="utf-8"))
expected = CONDITIONS["trial"]["expected_effect"]
report = RAW.get("retained_report", {})
result = report.get("result", {})
execution = result.get("execution", {})
releases = execution.get("releases", [])
release = releases[-1] if releases else {}
events = RAW.get("fixture_events", [])
chars = [event for event in events if event.get("kind") == "char"]
saves = [event for event in events if event.get("kind") == "save"]
frozen_hashes = {
    name: hashlib.sha256((PACKET / name).read_bytes()).hexdigest()
    for name in CONDITIONS["frozen_files"]
}
checks = {
    "frozen_preflight_passed": PREFLIGHT.get("status") in (
        "PASS", "PASS_WITH_RECORDED_PREDECESSOR_HASH_LIMITATION"),
    "attempt_and_source_match": (
        RAW.get("attempt_id") == CONDITIONS["attempt_id"]
        and RAW.get("source_commit") == CONDITIONS["source_commit"]
    ),
    "frozen_packet_hashes_match": frozen_hashes == CONDITIONS["frozen_files"],
    "predecessor_r23_recovered_and_closed": (
        CONDITIONS["predecessor"]["recovery_status"] == "recovered"
        and CONDITIONS["predecessor"]["release_confirmed"] is True
        and CONDITIONS["predecessor"]["public_close_status"] == "closed"
        and CONDITIONS["predecessor"]["fixture_exit_code"] == 0
    ),
    "supervised_public_stdio_caller": (
        RAW.get("caller_kind") == "mcp_stdio"
        and RAW.get("session_mode") == "supervised-win32"
        and {"interface_observe", "interface_validate", "interface_dispatch",
             "interface_close"}.issubset(RAW.get("listed_tools", []))
    ),
    "one_dispatch_and_valid_program": (
        RAW.get("dispatch_attempts") == 1
        and RAW.get("program_validation", {}).get("static_valid") is True
    ),
    "fresh_public_generation_matches_new_fixture": (
        RAW.get("observation_target_generation_consistency") == "matched"
        and RAW.get("observed_target_generation")
            == RAW.get("target_identity_before", {}).get("generation")
        and RAW.get("target_identity_before") == RAW.get("target_identity_after")
        and RAW.get("observed_target_generation")
            != CONDITIONS["predecessor"]["target_generation"]
    ),
    "runtime_completed_and_success_not_overclaimed": (
        result.get("status") == "completed"
        and result.get("task_success") is None
    ),
    "independent_fixture_effect": (
        RAW.get("effect_file") == expected
        and RAW.get("oracle", {}).get("task_pass") is True
    ),
    "exact_fixture_event_journal": (
        RAW.get("oracle", {}).get("event_text") == expected["text"]
        and len(chars) == len(expected["text"])
        and len(saves) == 1
        and sum(event.get("kind") == "click" for event in events) == 1
    ),
    "verified_all_up_release": (
        len(releases) == 1
        and release.get("verified") is True
        and release.get("keys_down") == []
        and release.get("buttons_down") == []
        and release.get("keys_unknown") == []
        and release.get("buttons_unknown") == []
    ),
    "public_close_and_owned_fixture_cleanup": (
        RAW.get("public_close", {}).get("response", {}).get("status") == "closed"
        and RAW.get("fixture_close_posted") is True
        and RAW.get("fixture_exit_code") == 0
        and RAW.get("target_identity_after", {}).get("owner", {}).get("pid")
            == RAW.get("fixture_pid")
    ),
    "prior_foreground_restored": RAW.get("foreground_restore", {}).get("attempted") is False
        or RAW.get("foreground_restore", {}).get("observed_hwnd")
            == RAW.get("previous_foreground_hwnd"),
    "raw_status_pass": RAW.get("status") == "PASS",
}
audit = {
    "schema": "win32-supervised-standard-caller-r24-audit-v1",
    "attempt_id": CONDITIONS["attempt_id"],
    "checks": checks,
    "passed": sum(checks.values()),
    "total": len(checks),
    "status": "PASS" if all(checks.values()) else "FAIL_OR_UNKNOWN",
    "nonclaims": CONDITIONS["nonclaims"],
}
(PACKET / "audit.json").write_text(
    json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(audit, indent=2, sort_keys=True))
raise SystemExit(0 if all(checks.values()) else 1)
