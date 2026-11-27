"""Audit an R11 fixture setup stop without counting it as a recovery trial."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACKET = Path(__file__).resolve().parent
RUN = PACKET / "run"


def verify(path, base):
    errors = []
    rows = path.read_text(encoding="ascii").splitlines()
    for line in rows:
        expected, rel = line.split("  ", 1)
        target = base / rel
        actual = hashlib.sha256(target.read_bytes()).hexdigest() if target.is_file() else None
        if actual != expected:
            errors.append(rel)
    return {"entries": len(rows), "errors": errors}


pretrial = verify(PACKET / "PRETRIAL_SHA256SUMS", ROOT)
raw = verify(RUN / "SHA256SUMS", RUN)
d = json.loads((RUN / "probe.json").read_text(encoding="utf-8"))
events = [json.loads(row) for row in (RUN / "events.jsonl").read_text(
    encoding="utf-8").splitlines()]
checks = {
    "correct_attempt_and_hold": d.get("attempt_id") == "win32-r11-fixture-state-readback-20261122"
        and d.get("classification") == "HOLD_STATE_READBACK_UNKNOWN",
    "foreground_activation_failed_and_recorded": d["activation"]["set_foreground_return"] is False
        and d["activation"]["foreground_is_fixture"] is False,
    "probe_import_failure_prevented_state_read": d.get("error_type") == "ModuleNotFoundError"
        and d.get("error") == "No module named 'runtime'"
        and "shift_down" not in d,
    "no_input_or_effect": d.get("input_dispatched") is False
        and d.get("effect_file_present", False) is False and not (RUN / "effect.json").exists()
        and events == [{"hwnd": d["fixture"]["hwnd"], "kind": "ready"}],
    "fixture_closed_and_foreground_restored": d.get("cleanup_pass") is True
        and d.get("fixture_exit_code") == 0,
    "frozen_source_and_raw_hashes_valid": not pretrial["errors"] and not raw["errors"],
}
audit = {"attempt_id": d.get("attempt_id"), "classification": "EXCLUDED_PRE_DISPATCH",
    "checks": checks, "pretrial_hash_audit": pretrial, "raw_hash_audit": raw,
    "custody_and_exclusion_audit_pass": all(checks.values()),
    "recovery_acceptance_pass": False}
(PACKET / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n",
    encoding="utf-8", newline="\n")
print(json.dumps(audit, indent=2, sort_keys=True))
if not audit["custody_and_exclusion_audit_pass"]:
    raise SystemExit(1)

