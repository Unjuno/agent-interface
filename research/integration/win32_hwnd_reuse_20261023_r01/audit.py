"""Frozen structural auditor for the HWND reuse probe receipt."""
import json
from pathlib import Path

root = Path(__file__).resolve().parent
conditions = json.loads((root / "conditions.json").read_text(encoding="utf-8"))
raw = json.loads((root / "raw.json").read_text(encoding="utf-8"))
checks = {
    "attempt_id_matches": raw.get("attempt_id") == conditions["attempt_id"],
    "source_commit_matches": raw.get("source_commit") == conditions["source_commit"],
    "no_input": raw.get("input_sent") is False,
    "not_activated": raw.get("window_activated") is False,
    "first_destroyed": raw.get("first_destroy_succeeded") is True
        and raw.get("first_is_window_after_destroy") is False,
    "second_destroyed": raw.get("second_destroy_succeeded") is True
        and raw.get("second_is_window_after_destroy") is False,
    "outcome_consistent": (
        raw.get("same_hwnd") is True
        and raw.get("same_owner_identity") is True
        and raw.get("generation_equal") is True
    ) == (raw.get("status") == "COUNTEREXAMPLE_CONFIRMED"),
}
result = {
    "schema": "win32-hidden-hwnd-reuse-audit-v1",
    "attempt_id": conditions["attempt_id"],
    "checks": checks,
    "passed": sum(checks.values()),
    "total": len(checks),
    "status": "PASS" if all(checks.values()) else "FAIL",
    "observed_outcome": raw.get("status"),
}
(root / "audit.json").write_text(
    json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2, sort_keys=True))
raise SystemExit(0 if all(checks.values()) else 1)
