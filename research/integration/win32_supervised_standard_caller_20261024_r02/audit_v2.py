"""Supplemental independent audit of the preserved R02 one-shot raw."""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
CONDITIONS = json.loads((HERE / "conditions.json").read_text(encoding="utf-8"))
RAW = json.loads((HERE / "raw.json").read_text(encoding="utf-8"))
trial = CONDITIONS["trial"]
expected_effect = trial["expected_effect"]
checks = []


def check(name, passed, evidence=None):
    checks.append({"name": name, "passed": bool(passed), "evidence": evidence})


fixture = RAW.get("fixture", {})
identity = fixture.get("target_identity", {})
owner_identity = identity.get("owner", {})
observation = RAW.get("public_observation", {})
observation_raw = observation.get("raw_report", {})
validation = RAW.get("public_validation", {}).get("response", {})
dispatch = RAW.get("public_dispatch", {})
dispatch_response = dispatch.get("response", {})
terminal_readbacks = RAW.get("result_readbacks", [])
terminal_readback = (terminal_readbacks[-1].get("response", {})
                     if terminal_readbacks else {})
terminal_action = terminal_readback.get("action", {})
report = RAW.get("retained_report") or {}
supervision = report.get("supervision", {})
action = supervision.get("action", {})
completion = action.get("completion_custody", {})
readback = completion.get("completion_readback")
release_receipt = completion.get("completion_release_receipt")
action_result = action.get("result", {})
events = fixture.get("events", [])
text = trial["text_effect"]
expected_events = (
    [{"kind": "ready", "hwnd": fixture.get("hwnd")}, {"kind": "click"}]
    + [{"kind": "char", "code": ord(ch)} for ch in text]
    + [{"kind": "save", **expected_effect}]
)

check("attempt_and_source_identity",
      CONDITIONS.get("attempt_id") == RAW.get("attempt_id")
      and CONDITIONS.get("source_commit") == RAW.get("source_commit")
      and RAW.get("source_tracked_tree_clean") is True
      and RAW.get("session_mode") == "supervised-win32"
      and RAW.get("caller_kind") == "mcp_stdio",
      {"attempt_id": RAW.get("attempt_id"),
       "source_commit": RAW.get("source_commit"),
       "tracked_tree_clean": RAW.get("source_tracked_tree_clean"),
       "session_mode": RAW.get("session_mode")})
check("public_tool_surface",
      {"interface_clock", "interface_observe", "interface_validate",
       "interface_dispatch", "interface_results", "interface_close"}
      <= set(RAW.get("tools", [])),
      RAW.get("tools"))
check("one_owned_fixture",
      type(fixture.get("pid")) is int
      and owner_identity.get("pid") == fixture.get("pid")
      and type(fixture.get("hwnd")) is int
      and identity.get("generation") is not None
      and re.fullmatch(r"[0-9a-f]{64}", identity.get("generation", "")) is not None,
      {"pid": fixture.get("pid"), "hwnd": fixture.get("hwnd"),
       "owner": owner_identity, "generation": identity.get("generation")})
check("public_observation_generation_matches_owned_target",
      observation.get("is_error") is False
      and observation_raw.get("target_generation_consistency") == "matched"
      and observation_raw.get("target_generation") == identity.get("generation"),
      {"observed_generation": observation_raw.get("target_generation"),
       "consistency": observation_raw.get("target_generation_consistency"),
       "owned_generation": identity.get("generation")})
check("exact_program_and_generation_forwarding",
      RAW.get("program", {}).get("program_id") == trial["program_id"]
      and RAW.get("program", {}).get("ops") == trial["operations"]
      and RAW.get("program", {}).get("source", {}).get("target_generations")
      == {"fixture": observation_raw.get("target_generation")},
      {"program_id": RAW.get("program", {}).get("program_id"),
       "operations": RAW.get("program", {}).get("ops"),
       "source_generations": RAW.get("program", {}).get("source", {}).get(
           "target_generations")})
check("public_static_validation",
      RAW.get("public_validation", {}).get("is_error") is False
      and validation.get("static_valid") is True,
      validation)
check("single_public_dispatch",
      RAW.get("dispatch_attempts") == 1
      and dispatch.get("is_error") is False
      and dispatch_response.get("status") in ("returned", "pending")
      and isinstance(dispatch_response.get("call_id"), str)
      and dispatch_response.get("replay_allowed") is False,
      {"attempts": RAW.get("dispatch_attempts"),
       "dispatch_error": dispatch.get("is_error"),
       "dispatch_status": dispatch_response.get("status"),
       "call_id": dispatch_response.get("call_id"),
       "replay_allowed": dispatch_response.get("replay_allowed")})
check("same_call_pending_to_completed_readback",
      dispatch_response.get("status") == "pending"
      and report.get("status") == "returned"
      and report.get("operation_invoked") is True
      and report.get("result", {}).get("status") == "completed"
      and report.get("call_id") == dispatch_response.get("call_id")
      and terminal_readback.get("call_id") == dispatch_response.get("call_id")
      and terminal_action.get("status") == "completed"
      and terminal_action.get("operation_id") == report.get("operation_id"),
      {"dispatch_call_id": dispatch_response.get("call_id"),
       "dispatch_status": dispatch_response.get("status"),
       "retained_call_id": report.get("call_id"),
       "terminal_readback_call_id": terminal_readback.get("call_id"),
       "retained_status": report.get("status"),
       "action_status": terminal_action.get("status"),
       "operation_id": report.get("operation_id")})
check("retained_standard_action_completed",
      action.get("status") == "completed"
      and completion.get("phase") == "completed"
      and action_result.get("status") == "completed"
      and terminal_readback.get("call_id") == dispatch_response.get("call_id")
      and terminal_action.get("operation_id") == action.get("operation_id")
      and action.get("target_generation") == observation_raw.get("target_generation")
      and action.get("operation_id") == report.get("operation_id"),
      {"action_status": action.get("status"),
       "completion_phase": completion.get("phase"),
       "result_status": action_result.get("status"),
       "operation_id": action.get("operation_id"),
       "call_id": action.get("call_id"),
       "target_generation": action.get("target_generation")})
check("verified_empty_release_receipt_retained",
      type(release_receipt) is dict
      and release_receipt.get("verified") is True
      and release_receipt.get("keys_down") == []
      and release_receipt.get("buttons_down") == []
      and release_receipt.get("keys_unknown") == []
      and release_receipt.get("buttons_unknown") == []
      and completion.get("release_confirmed") is True
      and completion.get("producer_exit_code") == 0
      and ((action_result.get("execution") or {}).get("releases") or [])[-1:]
      == [release_receipt],
      release_receipt)
check("independent_neutral_readback_retained",
      type(readback) is dict
      and set(readback) == {"operation_id", "target_generation",
          "producer_exit_confirmed_ns", "observed_monotonic_ns", "neutral"}
      and readback.get("operation_id") == action.get("operation_id")
      and readback.get("target_generation") == action.get("target_generation")
      and type(readback.get("producer_exit_confirmed_ns")) is int
      and type(readback.get("observed_monotonic_ns")) is int
      and readback.get("observed_monotonic_ns")
      >= readback.get("producer_exit_confirmed_ns")
      and readback.get("neutral") is True,
      readback)
check("task_effect_independent_of_runtime_success",
      RAW.get("effect_readback") == expected_effect
      and fixture.get("effect") == expected_effect
      and dispatch_response.get("task_success") is None,
      {"effect_readback": RAW.get("effect_readback"),
       "fixture_effect_after_close": fixture.get("effect"),
       "runtime_task_success": dispatch_response.get("task_success"),
       "expected_effect": expected_effect})
check("event_journal_exact",
      events == expected_events,
      {"actual": events, "expected": expected_events})
check("fixture_shutdown_and_foreground_restore",
      fixture.get("close_posted") is True
      and fixture.get("exit_code") == 0
      and fixture.get("window_exists_after_exit") is False
      and (RAW.get("foreground_restore", {}).get("prior_hwnd_exists") is not True
           or RAW.get("foreground_restore", {}).get("restored") is True),
      {"close_posted": fixture.get("close_posted"),
       "exit_code": fixture.get("exit_code"),
       "window_exists_after_exit": fixture.get("window_exists_after_exit"),
       "foreground_restore": RAW.get("foreground_restore")})
close_report = RAW.get("session_close_report")
check("supervised_session_closed",
      type(close_report) is dict and close_report.get("status") == "closed"
      and RAW.get("public_close", {}).get("is_error") is False,
      {"close_report": close_report,
       "public_close": RAW.get("public_close", {}).get("response")})

audit_result = {
    "schema": "win32-supervised-standard-caller-audit-v2",
    "attempt_id": CONDITIONS["attempt_id"],
    "source_commit": CONDITIONS["source_commit"],
    "status": "PASS" if all(row["passed"] for row in checks) else "FAIL_OR_UNKNOWN",
    "passed": sum(row["passed"] for row in checks),
    "total": len(checks),
    "checks": checks,
    "known_signal_gap": {
        "retained_report_input_dispatched": report.get("input_dispatched"),
        "execution_emissions": (action_result.get("execution") or {}).get("emissions"),
        "fixture_events_and_effect_independently_checked": True,
        "note": "R02 retained a null input_dispatched field despite positive native emissions. R03 is reserved to verify the corrected caller summary field.",
    },
}
(HERE / "audit_v2.json").write_text(
    json.dumps(audit_result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
    encoding="utf-8")
print(json.dumps(audit_result, indent=2, sort_keys=True, ensure_ascii=False))
sys.exit(0 if audit_result["status"] == "PASS" else 1)
