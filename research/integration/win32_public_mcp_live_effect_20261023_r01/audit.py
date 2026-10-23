"""Frozen auditor for public-MCP Win32 input, release and file effect."""
import json
from pathlib import Path

root = Path(__file__).resolve().parent
conditions = json.loads((root / "conditions.json").read_text(encoding="utf-8"))
raw = json.loads((root / "raw.json").read_text(encoding="utf-8"))
checks = {
    "attempt_and_source_match": raw.get("attempt_id") == conditions["attempt_id"]
        and raw.get("source_commit") == conditions["source_commit"],
    "actual_public_stdio_route": raw.get("caller_kind") == "mcp_stdio"
        and {"interface_observe", "interface_dispatch"}.issubset(raw.get("listed_tools", [])),
    "public_preflight_valid": raw.get("program_validation", {}).get("static_valid") is True,
    "owned_fixture_retired": raw.get("fixture_close_posted") is True
        and raw.get("fixture_exit_code") == 0,
    "no_retry": raw.get("dispatch_attempts") == 1,
    "independent_task_effect": raw.get("oracle", {}).get("task_pass") is True,
    "exact_event_count": raw.get("oracle", {}).get("char_event_count")
        == raw.get("oracle", {}).get("expected_char_event_count"),
    "one_save_event": raw.get("oracle", {}).get("save_event_count") == 1,
    "release_verified": raw.get("oracle", {}).get("release_pass") is True,
    "target_generation_recorded": raw.get("target_identity_before")
        == raw.get("target_identity_after"),
    "no_presentation_claim": raw.get("oracle", {}).get("nonclaims")
        == conditions["nonclaims"],
}
result = {
    "schema": "win32-public-mcp-live-effect-audit-v1",
    "attempt_id": conditions["attempt_id"],
    "checks": checks,
    "passed": sum(checks.values()),
    "total": len(checks),
    "status": "PASS" if all(checks.values()) else "FAIL",
    "experiment_outcome": raw.get("status"),
}
(root / "audit.json").write_text(
    json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2, sort_keys=True))
raise SystemExit(0 if all(checks.values()) else 1)
