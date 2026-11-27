from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONDITIONS = json.loads((ROOT / "conditions.json").read_text(encoding="utf-8"))
RAW = json.loads((ROOT / "raw.json").read_text(encoding="utf-8"))

checks = []


def check(name, passed, evidence=None):
    checks.append({"name": name, "passed": bool(passed), "evidence": evidence})


check("schema_and_attempt", RAW.get("schema") == "win32-public-mcp-generation-fence-raw-v1"
      and RAW.get("attempt_id") == CONDITIONS["attempt_id"], RAW.get("attempt_id"))
check("source_commit", RAW.get("source_commit") == CONDITIONS["source_commit"], RAW.get("source_commit"))
check("actual_public_stdio_caller", RAW.get("caller_kind") == "mcp_stdio",
      RAW.get("caller_kind"))
old = RAW.get("fixture_a", {})
new = RAW.get("fixture_b", {})
old_gen = old.get("target_identity", {}).get("generation")
new_gen = new.get("target_identity", {}).get("generation")
check("two_owned_processes", isinstance(old.get("pid"), int)
      and isinstance(new.get("pid"), int) and old["pid"] != new["pid"],
      [old.get("pid"), new.get("pid")])
check("generation_digests_valid", all(isinstance(value, str)
      and re.fullmatch(r"[0-9a-f]{64}", value) for value in (old_gen, new_gen)),
      [old_gen, new_gen])
check("generation_changed", isinstance(old_gen, str) and isinstance(new_gen, str)
      and old_gen != new_gen, {"old": old_gen, "new": new_gen})
observation = RAW.get("public_observation", {})
old_report = observation.get("raw_report", {})
check("public_observation_returned", observation.get("is_error") is False
      and old_report.get("status") == "returned", observation.get("is_error"))
check("observation_generation_exposed", old_report.get("target_generation") == old_gen
      and old_report.get("target_generation_consistency") == "matched",
      {"report_generation": old_report.get("target_generation"), "expected": old_gen})
validation = RAW.get("public_validation", {})
check("public_validation_accepts_program", validation.get("is_error") is False
      and validation.get("report", {}).get("static_valid") is True,
      validation.get("report"))
dispatch = RAW.get("public_dispatch", {})
report = dispatch.get("raw_report", {})
result = report.get("result", {})
check("one_dispatch_attempt", RAW.get("dispatch_attempts") == 1,
      RAW.get("dispatch_attempts"))
check("stale_generation_refusal", dispatch.get("is_error") is False
      and result.get("status") == "refused"
      and result.get("error") == "TARGET_GENERATION_CHANGED",
      {"status": result.get("status"), "error": result.get("error")})
check("no_input_claimed", result.get("input_dispatched") is False
      and result.get("operation_invoked") is False, result)
events = RAW.get("fixture_b_events", [])
check("no_fixture_input_effect", [row.get("kind") for row in events] == ["ready"]
      and not RAW.get("fixture_b_effect_exists"),
      {"event_kinds": [row.get("kind") for row in events],
       "effect_exists": RAW.get("fixture_b_effect_exists")})
check("both_owned_fixtures_cleaned", all(
      row.get("close_posted") is True and row.get("exit_code") == 0
      and row.get("window_exists_after_exit") is False
      for row in (old, new)),
      [{"close_posted": row.get("close_posted"), "exit_code": row.get("exit_code"),
        "window_exists_after_exit": row.get("window_exists_after_exit")} for row in (old, new)])

result_row = {
    "schema": "win32-public-mcp-generation-fence-audit-v1",
    "attempt_id": CONDITIONS["attempt_id"],
    "source_commit": RAW.get("source_commit"),
    "passed": sum(row["passed"] for row in checks),
    "total": len(checks),
    "status": "PASS" if all(row["passed"] for row in checks) else "FAIL_OR_UNKNOWN",
    "checks": checks,
}
encoded = json.dumps(result_row, indent=2, sort_keys=True) + "\n"
(ROOT / "audit.json").write_text(encoded, encoding="utf-8")
print(encoded, end="")
raise SystemExit(0 if result_row["status"] == "PASS" else 1)
