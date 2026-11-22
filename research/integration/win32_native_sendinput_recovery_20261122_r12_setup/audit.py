"""Audit R12 timeout custody, excluding a post-stop CUA receipt."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACKET = Path(__file__).resolve().parent
RUN = PACKET / "run"


def verify(path, base):
    errors = []
    lines = path.read_text(encoding="ascii").splitlines()
    for line in lines:
        expected, rel = line.split("  ", 1)
        target = base / rel
        actual = hashlib.sha256(target.read_bytes()).hexdigest() if target.is_file() else None
        if actual != expected:
            errors.append(rel)
    return {"entries": len(lines), "errors": errors}


pretrial = verify(PACKET / "PRETRIAL_SHA256SUMS", ROOT)
raw = verify(RUN / "SHA256SUMS", RUN)
d = json.loads((RUN / "probe.json").read_text(encoding="utf-8"))
ready = json.loads((RUN / "ready.json").read_text(encoding="utf-8"))
late = json.loads((RUN / "computer-use-activation-post-stop.json").read_text(encoding="utf-8"))
events = [json.loads(row) for row in (RUN / "events.jsonl").read_text(
    encoding="utf-8").splitlines()]
probe_time = (RUN / "probe.json").stat().st_mtime_ns
late_receipt_time = (RUN / "computer-use-activation-post-stop.json").stat().st_mtime_ns
checks = {
    "attempt_and_timeout_recorded": d.get("attempt_id") ==
        "win32-r12-cua-foreground-state-readback-20261122"
        and d.get("classification") == "HOLD_COMPUTER_USE_ACTIVATION_TIMEOUT",
    "no_native_state_read_or_input": d.get("input_dispatched") is False
        and "shift_down" not in d,
    "post_stop_receipt_is_not_joined": late.get("fixture_window_id") ==
        ready["fixture"]["hwnd"] and probe_time < late_receipt_time,
    "no_fixture_effect": not (RUN / "effect.json").exists()
        and events == [{"hwnd": ready["fixture"]["hwnd"], "kind": "ready"}],
    "fixture_cleanup_passed": d.get("cleanup_pass") is True
        and d.get("fixture_exit_code") == 0,
    "pretrial_and_raw_manifests_valid": not pretrial["errors"] and not raw["errors"],
}
audit = {"attempt_id": d.get("attempt_id"), "disposition": "EXCLUDED_TIMEOUT",
    "checks": checks, "pretrial_hash_audit": pretrial, "raw_hash_audit": raw,
    "custody_and_exclusion_audit_pass": all(checks.values()),
    "setup_acceptance_pass": False,
    "note": "The post-stop Computer Use receipt is retained but does not provide paired native state evidence."}
(PACKET / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n",
    encoding="utf-8", newline="\n")
print(json.dumps(audit, indent=2, sort_keys=True))
if not audit["custody_and_exclusion_audit_pass"]:
    raise SystemExit(1)

