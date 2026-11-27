"""Strict auditor for input-free Win32 query availability evidence."""
import json
from pathlib import Path
root = Path(__file__).resolve().parent
conditions = json.loads((root / "conditions.json").read_text(encoding="utf-8"))
raw = json.loads((root / "raw.json").read_text(encoding="utf-8"))
keys = raw.get("async_key_state", [])
checks = {
    "attempt_and_source_match": raw.get("attempt_id") == conditions["attempt_id"]
        and raw.get("source_commit") == conditions["source_commit"],
    "input_free": raw.get("input_sent") is False,
    "owned_fixture_foreground": raw.get("foreground", {}).get("is_fixture") is True
        and raw.get("foreground", {}).get("pid") == raw.get("fixture_pid"),
    "input_desktop_access": raw.get("input_desktop", {}).get("opened_with_hookcontrol") is True,
    "active_input_desktop": raw.get("input_desktop_is_receiving_input") is True,
    "same_desktop": len(set(raw.get("desktop_names", {}).values())) == 1
        and raw.get("desktop_names", {}).get("input") is not None,
    "integrity_allows_query": raw.get("integrity", {}).get("probe_at_least_fixture") is True,
    "three_raw_state_samples": [item.get("vk") for item in keys] == [0x11, 0x53, 0x01],
    "neutral_state_reads_zero": len(keys) == 3 and all(item.get("raw_signed") == 0 for item in keys),
    "owned_fixture_retired": raw.get("fixture_close_posted") is True
        and raw.get("fixture_exit_code") == 0,
}
result = {"schema": "win32-release-state-witness-audit-v1",
          "attempt_id": conditions["attempt_id"], "checks": checks,
          "passed": sum(checks.values()), "total": len(checks),
          "status": "DIAGNOSTIC_COMPLETE" if all(checks.values()) else "INCOMPLETE",
          "release_claim": False}
(root / "audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                                  encoding="utf-8")
print(json.dumps(result, indent=2, sort_keys=True))
raise SystemExit(0 if all(checks.values()) else 1)
