"""Additive audit of R26's persisted report after the public 10 s wait."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

PACKET = Path(__file__).resolve().parent
RAW = json.loads((PACKET / "raw.json").read_text(encoding="utf-8"))
C = json.loads((PACKET / "conditions.json").read_text(encoding="utf-8"))
CALL_ID = RAW["public_response"]["call_id"]
CALL_DIR = PACKET / "run" / "mcp-calls" / CALL_ID
REPORT = json.loads((CALL_DIR / "report.json").read_text(encoding="utf-8"))
SESSION_CLOSE_PATH = next((PACKET / "run" / "mcp-calls").glob("session-*-close.json"))
SESSION_CLOSE = json.loads(SESSION_CLOSE_PATH.read_text(encoding="utf-8"))
ACTION = REPORT["supervision"]["action"]
CUSTODY = ACTION["completion_custody"]
RELEASE = CUSTODY["completion_release_receipt"]
READBACK = CUSTODY["completion_readback"]
EVENTS = RAW["fixture_events"]
CHARS = [e for e in EVENTS if e.get("kind") == "char"]
SAVES = [e for e in EVENTS if e.get("kind") == "save"]
START = RAW["dispatch"]["started_monotonic_ns"]
PENDING_RETURN = RAW["dispatch"]["returned_monotonic_ns"]
EFFECT_COMMIT = SAVES[0]["commit_completed_monotonic_ns"]
EXPECTED = C["trial"]["expected_effect"]
checks = {
    "one_dispatch_only": RAW.get("dispatch_attempts") == 1,
    "public_wait_expired_without_replay": (
        RAW.get("public_response", {}).get("status") == "pending"
        and RAW.get("public_response", {}).get("call", {}).get("response_wait_ms") == 10000
        and RAW.get("public_response", {}).get("replay_allowed") is False),
    "public_close_busy_and_close_receipt_release_unconfirmed": (
        RAW.get("public_close", {}).get("response", {}).get("status") == "busy"
        and RAW.get("public_close", {}).get("response", {}).get("release_confirmed") is False
        and SESSION_CLOSE.get("status") == "closed"
        and SESSION_CLOSE.get("release_confirmed") is False),
    "persisted_action_completed_after_public_deadline": (
        REPORT.get("status") == "returned"
        and REPORT.get("result", {}).get("status") == "completed"
        and ACTION.get("status") == "completed"
        and ACTION.get("release_confirmed") is True
        and RELEASE.get("monotonic_ns", 0) > PENDING_RETURN),
    "verified_all_up_release_with_owned_desktop_witnesses": (
        RELEASE.get("verified") is True
        and RELEASE.get("keys_down") == []
        and RELEASE.get("buttons_down") == []
        and RELEASE.get("keys_unknown") == []
        and RELEASE.get("buttons_unknown") == []
        and all(w.get("hwnd") == RAW["fixture_hwnd"]
                and w.get("pid") == RAW["fixture_pid"]
                and w.get("input_desktop_active") is True
                and w.get("desktop_hookcontrol_opened") is True
                for rows in RELEASE.get("state_query_witnesses", {}).values()
                for w in rows)),
    "producer_exit_and_neutral_readback": (
        CUSTODY.get("producer_exit_code") == 0
        and READBACK.get("neutral") is True
        and READBACK.get("target_generation") == RAW["observed_target_generation"]
        and READBACK.get("observed_monotonic_ns", 0) >= RELEASE.get("monotonic_ns", 1)),
    "independent_effect_and_exact_event_journal": (
        RAW.get("effect_file") == EXPECTED
        and RAW.get("oracle", {}).get("event_text") == EXPECTED["text"]
        and len(CHARS) == len(EXPECTED["text"])
        and len(SAVES) == 1
        and sum(e.get("kind") == "click" for e in EVENTS) == 1
        and EFFECT_COMMIT > PENDING_RETURN),
    "owned_fixture_and_foreground_cleanup": (
        RAW.get("fixture_exit_code") == 0
        and RAW.get("fixture_close_posted") is True
        and RAW.get("foreground_restore", {}).get("observed_hwnd")
            == RAW.get("previous_foreground_hwnd")),
    "runtime_task_success_remains_null": (
        REPORT.get("task_success") is None
        and ACTION.get("task_success") is None
        and RAW.get("public_response", {}).get("task_success") is None),
    "raw_does_not_claim_unknown_release_as_confirmed": (
        RAW.get("public_response", {}).get("release_confirmed") is False
        and RAW.get("timing", {}).get("release_receipt_monotonic_ns") is None),
}
result = {
    "schema": "win32-supervised-standard-caller-r26-followup-audit-v1",
    "audited_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    "attempt_id": C["attempt_id"],
    "raw_sha256": hashlib.sha256((PACKET / "raw.json").read_bytes()).hexdigest(),
    "runtime_report_sha256": hashlib.sha256((CALL_DIR / "report.json").read_bytes()).hexdigest(),
    "session_close_sha256": hashlib.sha256(SESSION_CLOSE_PATH.read_bytes()).hexdigest(),
    "checks": checks, "passed": sum(checks.values()), "total": len(checks),
    "classification": "POST_DISPATCH_EFFECT_AND_RELEASE_VERIFIED_BUT_PUBLIC_WAIT_AND_CLOSE_RELEASE_UNCONFIRMED" if all(checks.values()) else "FAIL_OR_UNKNOWN",
    "formal_trial_outcome": "FAIL_OR_UNKNOWN",
    "timing_ms_from_public_dispatch_start": {
        "pending_response": (PENDING_RETURN - START) / 1_000_000,
        "effect_commit": (EFFECT_COMMIT - START) / 1_000_000,
        "verified_release": (RELEASE["monotonic_ns"] - START) / 1_000_000,
        "producer_exit_neutral_readback": (READBACK["observed_monotonic_ns"] - START) / 1_000_000,
    },
    "interpretation": (
        "At the supported 10 s public response-wait maximum the dispatch remained pending, "
        "and public close returned busy with release unconfirmed. Persisted runtime records "
        "later show completed execution, a verified all-up release, producer exit, and neutral "
        "readback; the independent fixture journal confirms the exact effect after the public "
        "deadline. The session-close record is closed but does not itself confirm release. "
        "The frozen trial remains FAIL_OR_UNKNOWN; this additive audit does not rewrite it."
    ),
}
(PACKET / "audit_followup.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                                              encoding="utf-8")
print(json.dumps(result, indent=2, sort_keys=True))
raise SystemExit(0 if all(checks.values()) else 1)
