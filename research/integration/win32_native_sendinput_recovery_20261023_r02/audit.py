"""Frozen independent audit of native Win32 SendInput cancellation evidence."""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys

PACKET = Path(__file__).resolve().parent
CONDITIONS = json.loads((PACKET / "conditions.json").read_text(encoding="utf-8"))
RAW = json.loads((PACKET / "raw.json").read_text(encoding="utf-8"))
PREFLIGHT = json.loads((PACKET / "preflight.json").read_text(encoding="utf-8"))
checks = []


def check(name, passed, evidence=None):
    checks.append({"name": name, "passed": bool(passed), "evidence": evidence})


check("attempt_and_source_pinned",
      RAW.get("attempt_id") == CONDITIONS.get("attempt_id")
      and RAW.get("source_commit") == CONDITIONS.get("source_commit"),
      {"attempt_id": RAW.get("attempt_id"), "source_commit": RAW.get("source_commit")})
check("spawn_helper_readiness_preflight",
      PREFLIGHT.get("attempt_id") == CONDITIONS.get("attempt_id")
      and PREFLIGHT.get("source_commit") == CONDITIONS.get("source_commit")
      and PREFLIGHT.get("status") == "PASS"
      and set(PREFLIGHT.get("helpers", {})) == {"recovery", "observer"}
      and all(type(item.get("pid")) is int and item.get("alive") is True
              and type(item.get("identity", {}).get("creation_time_100ns")) is int
              for item in PREFLIGHT.get("helpers", {}).values()),
      PREFLIGHT)
check("native_windows_and_no_wslc",
      "Windows" in RAW.get("platform", "")
      and RAW.get("scope") == CONDITIONS.get("scope")
      and RAW.get("resource_commands") == [],
      {"platform": RAW.get("platform"), "scope": RAW.get("scope"),
       "resource_commands": RAW.get("resource_commands", "")})
schedules = RAW.get("schedules", [])
check("exactly_two_frozen_schedules",
      len(schedules) == 2
      and [row.get("mode") for row in schedules] == [item["name"]
          for item in CONDITIONS["fault_schedules"]],
      [row.get("mode") for row in schedules])

for index, row in enumerate(schedules, 1):
    prefix = f"schedule_{index}"
    fixture = row.get("fixture", {})
    hwnd = fixture.get("hwnd")
    generation = row.get("target_generation")
    owner = fixture.get("owner_identity", {})
    trigger = row.get("producer_trigger") or {}
    expected_trigger = ("before_native_call" if row.get("mode") ==
                        "blocked-before-native-call" else "sendinput_accepted")
    check(prefix + "_owned_fixture_identity",
          type(fixture.get("pid")) is int and owner.get("pid") == fixture.get("pid")
          and type(hwnd) is int and type(generation) is str
          and re.fullmatch(r"[0-9a-f]{64}", generation or "") is not None,
          {"pid": fixture.get("pid"), "hwnd": hwnd, "owner": owner,
           "generation": generation})
    check(prefix + "_frozen_trigger_and_input_state",
          trigger.get("phase") == expected_trigger
          and (row.get("state_before_cancel") or {}).get("state") is
              (False if index == 1 else True)
          and (index == 1 or trigger.get("accepted_emissions") == 1),
          {"trigger": trigger, "state_before_cancel": row.get("state_before_cancel")})
    terminal = row.get("terminal", {})
    check(prefix + "_bounded_cancel_and_exact_producer_retirement",
          row.get("cancel_response_ms", float("inf")) <=
              CONDITIONS["cleanup"]["cancel_response_max_ms"]
          and row.get("terminal_elapsed_ms", float("inf")) <=
              CONDITIONS["cleanup"]["terminal_max_ms"]
          and type(row.get("producer_exitcode")) is int
          and row.get("producer_alive_after_terminal") is False
          and terminal.get("status") == "recovered"
          and terminal.get("release_confirmed") is True
          and terminal.get("task_success") is None
          and terminal.get("replay_allowed") is False
          and "emergency_safety_cleanup" not in row,
          {"cancel_ms": row.get("cancel_response_ms"),
           "terminal_ms": row.get("terminal_elapsed_ms"),
           "exitcode": row.get("producer_exitcode"),
           "alive": row.get("producer_alive_after_terminal"),
           "terminal": terminal})
    events = row.get("helper_events", [])
    recovery = next((event for event in events if event.get("kind") == "recovery"), {})
    observer = next((event for event in events if event.get("kind") == "observer"), {})
    release = recovery.get("release_receipt") or {}
    check(prefix + "_retirement_before_one_verified_recovery_up",
          any(item.get("kind") == "producer_exit_confirmed_by_join"
              and item.get("exitcode") is not None
              for item in row.get("timeline", []))
          and type(recovery.get("monotonic_ns")) is int
          and next((item.get("monotonic_ns") for item in row.get("timeline", [])
                    if item.get("kind") == "producer_exit_confirmed_by_join"),
                   2**63) < recovery.get("monotonic_ns", -1)
          and recovery.get("release_accepted") is True
          and recovery.get("foreground_ok") is True
          and recovery.get("generation_ok") is True
          and release.get("verified") is True
          and release.get("keys_down") == [] and release.get("buttons_down") == []
          and release.get("keys_unknown") == [] and release.get("buttons_unknown") == [],
          {"timeline": row.get("timeline"), "recovery": recovery})
    samples = observer.get("samples", [])
    horizon = CONDITIONS["cleanup"]["late_down_observation_horizon_ms"] * 1_000_000
    observed_duration = (observer.get("ended_ns", 0) - observer.get("started_ns", 0))
    check(prefix + "_independent_neutral_state_through_late_down_horizon",
          observer.get("neutral") is True
          and observer.get("horizon_ns") == horizon
          and observed_duration >= horizon
          and len(samples) >= 30
          and all(item.get("state") is False for item in samples)
          and all(item.get("generation") == generation for item in samples)
          and all(item.get("foreground_hwnd") == hwnd for item in samples)
          and all(item.get("witness") for item in samples),
          {"sample_count": len(samples), "observed_duration_ns": observed_duration,
           "required_horizon_ns": horizon,
           "states": sorted({str(item.get("state")) for item in samples})})

fresh = RAW.get("fresh_effect_fixture", {})
effect = RAW.get("effect_readback")
expected_effect = CONDITIONS["task_effect"]["expected"]
fresh_generation = fresh.get("target_generation")
old_generations = {row.get("target_generation") for row in schedules}
expected_effect_events = ([{"kind": "ready", "hwnd": fresh.get("hwnd")}] +
    [{"kind": "char", "code": ord(ch)} for ch in expected_effect["text"]] +
    [{"kind": "save", **expected_effect}])
check("fresh_target_independent_task_effect",
      len(schedules) == 2 and all(row.get("terminal", {}).get("status") == "recovered"
                                  for row in schedules)
      and fresh_generation not in old_generations
      and effect == expected_effect and fresh.get("effect") == expected_effect
      and fresh.get("exit_code") == 0
      and fresh.get("window_exists_after_exit") is False
      and fresh.get("events") == expected_effect_events,
      {"effect_readback": effect, "effect_after_close": fresh.get("effect"),
       "fresh_generation": fresh_generation, "prior_generations": sorted(old_generations),
       "exit_code": fresh.get("exit_code"), "hwnd_gone": fresh.get("window_exists_after_exit"),
       "event_count": len(fresh.get("events", []))})
dispatch = (RAW.get("public_dispatch", {}).get("raw_report") or {}).get("result", {})
releases = dispatch.get("execution", {}).get("releases", [])
task_release = releases[-1] if releases else {}
check("fresh_public_mcp_task_and_verified_release",
      RAW.get("public_observation", {}).get("is_error") is False
      and {"interface_observe", "interface_validate", "interface_dispatch"}
          .issubset(set(RAW.get("public_tools", [])))
      and RAW.get("public_dispatch_attempts") == 1
      and RAW.get("public_observation", {}).get("response", {}).get("receipt", {})
          .get("source", {}).get("raw_report", {}).get("target_generation") == fresh_generation
      and RAW.get("public_validation", {}).get("response", {}).get("static_valid") is True
      and RAW.get("public_dispatch", {}).get("is_error") is False
      and dispatch.get("status") == "completed"
      and RAW.get("public_program", {}).get("source", {}).get("target_generations", {})
          .get("fixture") == fresh_generation
      and task_release.get("verified") is True
      and task_release.get("keys_down") == [] and task_release.get("buttons_down") == []
      and task_release.get("keys_unknown", []) == []
      and task_release.get("buttons_unknown", []) == [],
      {"status": dispatch.get("status"), "release": task_release})
check("runner_cleanup_confirmed",
      RAW.get("cleanup_errors") == []
      and all(row.get("fixture", {}).get("exit_code") == 0
              and row.get("fixture", {}).get("window_exists_after_exit") is False
              for row in schedules)
      and fresh.get("exit_code") == 0 and fresh.get("window_exists_after_exit") is False,
      RAW.get("cleanup_errors"))

report = {"schema": "win32-native-sendinput-recovery-audit-v1",
    "attempt_id": CONDITIONS["attempt_id"],
    "source_commit": CONDITIONS["source_commit"],
    "status": "PASS" if checks and all(item["passed"] for item in checks)
        and RAW.get("status") == "PASS" else "FAIL_OR_UNKNOWN",
    "passed": sum(item["passed"] for item in checks),
    "total": len(checks), "checks": checks}
(PACKET / "audit.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                                   encoding="utf-8")
print(json.dumps(report, indent=2, sort_keys=True))
sys.exit(0 if report["status"] == "PASS" else 1)
