"""Independent raw-trace audit; does not execute the candidate or runtime."""
import hashlib
import json
import pathlib
import subprocess

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = "14b81dd1f6853623a694266b98538f812847257a"
raw = json.loads((HERE / "raw_trace.json").read_text(encoding="utf-8"))
errors = []
checks = []

for name, source in raw["sources"].items():
    blob = subprocess.check_output(
        ["git", "rev-parse", f"{BASE}:{source['path']}"], cwd=ROOT, text=True
    ).strip()
    content = subprocess.check_output(["git", "show", f"{BASE}:{source['path']}"], cwd=ROOT)
    ok = (blob == source["git_blob"] and hashlib.sha256(content).hexdigest() == source["sha256"]
          and len(content) == source["bytes"])
    checks.append({"check": f"source_identity:{name}", "ok": ok})
    if not ok:
        errors.append(f"source identity mismatch: {name}")

expected = {
    "A-clock-before-cancel-within-lease": ("clock-before-cancel", 600, 400, 2000),
    "B-clock-before-cancel-past-lease": ("clock-before-cancel", 600, 1600, 1500),
    "C-cancel-before-clock-within-lease": ("cancel-before-clock", 600, 400, 2000),
}
for case in raw["cases"]:
    key = case["case"]
    if key not in expected:
        errors.append(f"unexpected case: {key}")
        continue
    ordering, timer_ms, clock_ms, lease_ms = expected[key]
    config_ok = (case["ordering"] == ordering and case["timer_ms"] == timer_ms
                 and case["clock_delay_ms"] == clock_ms
                 and case["lease_ms_from_start"] == lease_ms)
    elapsed_release_ms = (case["release_ns"] - case["started_ns"]) / 1_000_000
    deadline_ms = (case["started_ns"] + lease_ms * 1_000_000 - case["started_ns"]) / 1_000_000
    events = case["events"]
    event_names = [e.get("event") for e in events]
    cooperative = case["terminal_status"] == "cancelled" if ordering == "cancel-before-clock" else True
    release_ok = case["release_verified"] is True and case["release_ns"] is not None
    checks.append({
        "check": f"case:{key}", "configuration_ok": config_ok,
        "elapsed_release_ms": elapsed_release_ms, "lease_deadline_ms": deadline_ms,
        "terminal_status": case["terminal_status"], "release_verified": release_ok,
        "events": event_names,
    })
    if not config_ok or not release_ok:
        errors.append(f"invalid configuration/release receipt: {key}")

# The synthetic backend calls Lease.wait() but ignores its True return and
# therefore never cooperates with cancel. This is detected from the control
# case's terminal status and the fact it releases only at the lease deadline.
control = next(c for c in raw["cases"] if c["case"] == "C-cancel-before-clock-within-lease")
cancel_receipt = next((e for e in control["events"] if e.get("event") == "cancel_requested"), None)
control_delay_after_cancel_ms = (control["release_ns"] - control["cancel_sent_ns"]) / 1_000_000
stop = (cancel_receipt is not None and cancel_receipt.get("matched") is True
        and control["terminal_status"] == "expired" and control_delay_after_cancel_ms > 1000)
if not stop:
    errors.append("expected non-cooperative fake-backend signature was not present")

audit = {
    "schema": "map01-v6-clock-cancel-order-t0-independent-audit-v1",
    "base_commit": BASE,
    "raw_sha256": hashlib.sha256((HERE / "raw_trace.json").read_bytes()).hexdigest(),
    "integrity_checks": checks,
    "candidate_decision": "STOP_HARNESS_CANCEL_NONCOOPERATIVE" if stop and not errors else "FAIL_AUDIT",
    "errors": errors,
    "interpretation": (
        "The fake backend ignored Lease.wait() returning True, so the candidate invocation did not test executor cancellation effect. "
        "Raw timestamps document the invalid run only; no inference about v6 runtime cancellation latency is valid."
    ),
    "audit_invocation_count": 1,
}
(HERE / "independent_audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(audit, indent=2))
if errors:
    raise SystemExit(1)
