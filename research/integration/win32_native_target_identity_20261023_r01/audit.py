"""Audit the retained one-shot native identity receipt."""
import json
from pathlib import Path

root = Path(__file__).resolve().parent
raw = json.loads((root / "raw.json").read_text(encoding="utf-8"))
checks = {
    "status_pass": raw.get("status") == "PASS",
    "owned_window_created": raw.get("is_window_after_create") is True,
    "identity_repeatable": raw.get("identity_stable") is True,
    "generation_repeatable": raw.get("generation_stable") is True,
    "input_not_sent": raw.get("input_sent") is False,
    "window_not_activated": raw.get("window_activated") is False,
    "owned_window_destroyed": raw.get("destroy_succeeded") is True,
    "hwnd_absent_after_destroy": raw.get("is_window_after_destroy") is False,
}
result = {"schema": "win32-native-target-identity-audit-v1",
          "checks": checks,
          "passed": sum(checks.values()),
          "total": len(checks),
          "status": "PASS" if all(checks.values()) else "FAIL"}
(root / "audit.json").write_text(
    json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2, sort_keys=True))
raise SystemExit(0 if all(checks.values()) else 1)
