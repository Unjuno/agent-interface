"""Frozen offline audit of one valid-generation public Win32 MCP effect trial."""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
CONDITIONS = json.loads((HERE / "conditions.json").read_text(encoding="utf-8"))
RAW = json.loads((HERE / "raw.json").read_text(encoding="utf-8"))
EXPECTED_TEXT = CONDITIONS["text_effect"]
checks = []


def check(name, passed, evidence=None):
    checks.append({"name": name, "passed": bool(passed), "evidence": evidence})


fixture = RAW.get("fixture", {})
identity = fixture.get("target_identity", {})
owner = identity.get("owner", {})
observation = RAW.get("public_observation", {}).get("raw_report", {})
validation = RAW.get("public_validation", {}).get("response", {})
dispatch = RAW.get("public_dispatch", {})
dispatch_report = dispatch.get("raw_report") or {}
result = dispatch_report.get("result", {})
execution = result.get("execution", {})
releases = execution.get("releases", [])
release = releases[-1] if releases else {}
effect = RAW.get("effect_readback")
expected_effect = {"saved": True, "text": EXPECTED_TEXT, "clicked": False}
events = fixture.get("events", [])
expected_events = ([{"kind": "ready", "hwnd": fixture.get("hwnd")}] +
                   [{"kind": "char", "code": ord(ch)} for ch in EXPECTED_TEXT] +
                   [{"kind": "save", **expected_effect}])

check("schema_attempt_and_frozen_source",
      CONDITIONS.get("attempt_id") == RAW.get("attempt_id")
      and CONDITIONS.get("source_commit") == RAW.get("source_commit")
      and RAW.get("caller_kind") == "mcp_stdio",
      {"attempt_id": RAW.get("attempt_id"), "source_commit": RAW.get("source_commit")})
check("one_owned_fixture_process",
      isinstance(fixture.get("pid"), int) and owner.get("pid") == fixture.get("pid")
      and isinstance(fixture.get("hwnd"), int),
      {"pid": fixture.get("pid"), "hwnd": fixture.get("hwnd"), "owner": owner})
check("public_observation_returned_generation",
      RAW.get("public_observation", {}).get("is_error") is False
      and observation.get("target_generation_consistency") == "matched"
      and isinstance(observation.get("target_generation"), str)
      and re.fullmatch(r"[0-9a-f]{64}", observation.get("target_generation", "")) is not None,
      {"target_generation": observation.get("target_generation"),
       "consistency": observation.get("target_generation_consistency")})
check("observed_generation_matches_native_owner",
      observation.get("target_generation") == identity.get("generation"),
      {"observed": observation.get("target_generation"), "owned": identity.get("generation")})
check("public_validation_accepted",
      RAW.get("public_validation", {}).get("is_error") is False
      and validation.get("static_valid") is True,
      validation)
check("program_supplied_observed_generation",
      RAW.get("program", {}).get("source", {}).get("target_generations", {}).get("fixture")
      == observation.get("target_generation"),
      RAW.get("program", {}).get("source", {}).get("target_generations"))
check("exact_frozen_program",
      RAW.get("program", {}).get("ops") == CONDITIONS.get("operations")
      and RAW.get("program", {}).get("program_id") == CONDITIONS.get("program_id"),
      RAW.get("program", {}).get("ops"))
check("single_public_dispatch",
      RAW.get("dispatch_attempts") == 1 and dispatch.get("is_error") is False,
      {"attempts": RAW.get("dispatch_attempts"), "error": dispatch.get("is_error")})
check("dispatch_completed_and_admitted",
      result.get("status") == "completed" and result.get("admission") == "accepted"
      and result.get("recovery_required") is False,
      {"status": result.get("status"), "admission": result.get("admission"),
       "recovery_required": result.get("recovery_required")})
check("verified_release_all",
      bool(releases) and release.get("verified") is True
      and release.get("keys_down") == [] and release.get("buttons_down") == []
      and release.get("keys_unknown", []) == []
      and release.get("buttons_unknown", []) == [],
      release)
check("independent_task_effect_exact",
      effect == expected_effect and fixture.get("effect") == expected_effect,
      {"readback": effect, "after_close": fixture.get("effect"), "expected": expected_effect})
check("independent_event_journal_exact", events == expected_events,
      {"actual": events, "expected": expected_events})
check("clean_fixture_shutdown",
      fixture.get("close_posted") is True and fixture.get("exit_code") == 0
      and fixture.get("window_exists_after_exit") is False,
      {"close_posted": fixture.get("close_posted"), "exit_code": fixture.get("exit_code"),
       "window_exists_after_exit": fixture.get("window_exists_after_exit")})

report = {
    "schema": "win32-public-mcp-valid-generation-effect-audit-v1",
    "attempt_id": CONDITIONS["attempt_id"],
    "source_commit": CONDITIONS["source_commit"],
    "status": "PASS" if all(item["passed"] for item in checks) else "FAIL_OR_UNKNOWN",
    "passed": sum(item["passed"] for item in checks),
    "total": len(checks),
    "checks": checks,
}
(HERE / "audit.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                                  encoding="utf-8")
print(json.dumps(report, indent=2, sort_keys=True))
sys.exit(0 if report["status"] == "PASS" else 1)
