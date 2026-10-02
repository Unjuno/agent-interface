"""Independent raw-only audit for the one-shot T1 clock/cancel probe."""
import hashlib
import json
import pathlib
import subprocess

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BASE = "673763554192ae26636e07d5a48f03b3cd7fb044"
raw_bytes = (HERE / "raw_trace.json").read_bytes()
raw = json.loads(raw_bytes)
errors = []
checks = []

for name, source in raw["sources"].items():
    content = subprocess.check_output(["git", "show", f"{BASE}:{source['path']}"], cwd=ROOT)
    blob = subprocess.check_output(["git", "rev-parse", f"{BASE}:{source['path']}"], cwd=ROOT, text=True).strip()
    okay = (blob == source["git_blob"] and hashlib.sha256(content).hexdigest() == source["sha256"]
            and len(content) == source["bytes"])
    checks.append({"check": f"source:{name}", "ok": okay})
    if not okay:
        errors.append(f"source identity mismatch: {name}")

v6 = subprocess.check_output(["git", "show", f"{BASE}:{raw['sources']['v6_runner']['path']}"], cwd=ROOT).decode()
end_pos = v6.index("planner_end_ns = session.runtime_clock()")
cancel_pos = v6.index('session.send({"op": "cancel", "id": fallback_id})', end_pos)
source_order_ok = end_pos < cancel_pos
checks.append({"check": "frozen_v6_clock_before_fallback_cancel", "ok": source_order_ok,
               "clock_source_offset": end_pos, "cancel_source_offset": cancel_pos})
if not source_order_ok:
    errors.append("frozen v6 source order did not match hypothesis")

expected = {
    "A-clock-before-cancel-within-lease": ("clock-before-cancel", 600, 400, 2000),
    "B-clock-before-cancel-past-lease": ("clock-before-cancel", 600, 1600, 1500),
    "C-cancel-before-clock-within-lease": ("cancel-before-clock", 600, 400, 2000),
}
derived = {}
for case in raw["cases"]:
    name = case["case"]
    if name not in expected:
        errors.append(f"unexpected case {name}")
        continue
    ordering, timer_ms, clock_ms, lease_ms = expected[name]
    config_ok = (case["ordering"] == ordering and case["timer_ms"] == timer_ms
                 and case["clock_delay_ms"] == clock_ms and case["lease_ms_from_start"] == lease_ms)
    timer_delta = (case["timer_expired_ns"] - case["started_ns"]) / 1e6
    cancel_offset = (case["cancel_requested_ns"] - case["timer_expired_ns"]) / 1e6
    release_from_timer = (case["release_ns"] - case["timer_expired_ns"]) / 1e6
    release_from_cancel = (case["release_ns"] - case["cancel_requested_ns"]) / 1e6
    release_from_start = (case["release_ns"] - case["started_ns"]) / 1e6
    deadline_from_start = lease_ms
    event_names = [event.get("event") for event in case["events"]]
    if ordering == "clock-before-cancel":
        timing_order = (case["timer_expired_ns"] < case["clock_return_ns"] <= case["cancel_requested_ns"])
    else:
        timing_order = (case["timer_expired_ns"] <= case["cancel_requested_ns"] < case["clock_return_ns"])
    cancellation_order = (case["cancel_observed_ns"] is not None
                          and case["cancel_requested_ns"] <= case["cancel_observed_ns"] <= case["release_ns"])
    release_verified = case["release_verified"] is True
    if name.startswith("A-"):
        decision_gate = (case["cancel_matched"] is True and cancellation_order and release_verified
                         and release_from_timer >= 350 and release_from_cancel <= 50
                         and release_from_start < deadline_from_start)
    elif name.startswith("B-"):
        decision_gate = (case["cancel_matched"] is False and case["cancel_observed_ns"] is None
                         and release_verified and abs(release_from_start - deadline_from_start) <= 50
                         and case["release_ns"] < case["clock_return_ns"]
                         and case["terminal_status"] == "expired")
    else:
        decision_gate = (case["cancel_matched"] is True and cancellation_order and release_verified
                         and release_from_timer <= 50 and case["release_ns"] < case["clock_return_ns"])
    checks.append({
        "check": f"case:{name}", "configuration_ok": config_ok, "timing_order_ok": timing_order,
        "cancel_observation_order_ok": cancellation_order, "release_verified": release_verified,
        "timer_delta_ms": timer_delta, "cancel_offset_from_timer_ms": cancel_offset,
        "release_from_timer_ms": release_from_timer, "release_from_cancel_ms": release_from_cancel,
        "release_from_start_ms": release_from_start, "cancel_matched": case["cancel_matched"],
        "terminal_status": case["terminal_status"], "events": event_names,
        "preregistered_decision_gate": decision_gate,
    })
    if not config_ok or not timing_order or not decision_gate:
        errors.append(f"preregistered gate failed for {name}")
    derived[name] = {"release_from_timer_ms": release_from_timer, "release_from_cancel_ms": release_from_cancel}

if len(derived) != 3:
    errors.append("candidate case count was not exactly three")
if len(derived) == 3:
    if derived["A-clock-before-cancel-within-lease"]["release_from_timer_ms"] - derived["C-cancel-before-clock-within-lease"]["release_from_timer_ms"] < 300:
        errors.append("A versus C release contrast was below the preregistered 300 ms margin")

audit = {
    "schema": "map01-v6-clock-cancel-order-t1-independent-audit-v1",
    "allocation": raw.get("allocation"),
    "base_commit": BASE,
    "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
    "checks": checks,
    "decision": "PASS_CLOCK_DELAY_EXTENDS_WITHIN_LEASE_SCOPED" if not errors else "FAIL_OR_HOLD_PREREGISTERED_GATE",
    "errors": errors,
    "audit_invocation_count": 1,
}
(HERE / "independent_audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(audit, indent=2))
if errors:
    raise SystemExit(1)
