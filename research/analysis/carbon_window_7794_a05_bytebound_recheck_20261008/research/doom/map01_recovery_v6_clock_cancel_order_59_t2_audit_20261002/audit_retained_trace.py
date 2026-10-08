"""Fresh raw-only independent audit of the immutable #6232 candidate output."""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
BASE = "673763554192ae26636e07d5a48f03b3cd7fb044"
RAW_COMMIT = "05e050fdcdf179d9559324bcbc72cfdc82b77a2a"
RAW_PATH = "research/doom/map01_recovery_v6_clock_cancel_order_59_t1_20261002/raw_trace.json"
RAW_SHA256 = "f487b79a16920cc584167722098ea446b51c81f8e0788caee1b7bdd147b22c67"
OUT = pathlib.Path(__file__).resolve().parent


def git_bytes(spec: str) -> bytes:
    return subprocess.check_output(["git", "show", spec], cwd=ROOT)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--construct-only", action="store_true")
    args = parser.parse_args()
    raw_bytes = git_bytes(f"{RAW_COMMIT}:{RAW_PATH}")
    raw_digest = hashlib.sha256(raw_bytes).hexdigest()
    if raw_digest != RAW_SHA256:
        raise SystemExit(f"frozen raw SHA-256 mismatch: {raw_digest}")
    raw = json.loads(raw_bytes)
    if raw.get("allocation") != "MAP01-V6-CLOCK-CANCEL-ORDER-59-T1-20261002-01":
        raise SystemExit("frozen raw allocation identity mismatch")

    source_checks = []
    for name, record in raw["sources"].items():
        content = git_bytes(f"{BASE}:{record['path']}")
        blob = subprocess.check_output(["git", "rev-parse", f"{BASE}:{record['path']}"], cwd=ROOT, text=True).strip()
        okay = (blob == record["git_blob"] and hashlib.sha256(content).hexdigest() == record["sha256"]
                and len(content) == record["bytes"])
        source_checks.append({"name": name, "path": record["path"], "git_blob": blob,
                              "sha256": hashlib.sha256(content).hexdigest(), "ok": okay})
    if args.construct_only:
        print(json.dumps({"construction": "PASS_FROZEN_RAW_AND_SOURCE_IDENTITIES",
                          "raw_sha256": raw_digest, "source_checks": source_checks}, indent=2))
        if not all(check["ok"] for check in source_checks):
            raise SystemExit(1)
        return

    errors = []
    checks = []
    if not all(check["ok"] for check in source_checks):
        errors.append("one or more source blob/SHA/byte identities differ")

    v6 = git_bytes(f"{BASE}:{raw['sources']['v6_runner']['path']}").decode("utf-8")
    clock_offset = v6.index("planner_end_ns = session.runtime_clock()")
    cancel_offset = v6.index('session.send({"op": "cancel", "id": fallback_id})', clock_offset)
    order_ok = clock_offset < cancel_offset
    checks.append({"check": "v6 clock query before fallback cancel", "ok": order_ok,
                   "clock_offset": clock_offset, "cancel_offset": cancel_offset})
    if not order_ok:
        errors.append("frozen v6 source order mismatch")

    expected = {
        "A-clock-before-cancel-within-lease": ("clock-before-cancel", 600, 400, 2000),
        "B-clock-before-cancel-past-lease": ("clock-before-cancel", 600, 1600, 1500),
        "C-cancel-before-clock-within-lease": ("cancel-before-clock", 600, 400, 2000),
    }
    derived = {}
    for case in raw["cases"]:
        name = case["case"]
        if name not in expected:
            errors.append(f"unexpected case: {name}")
            continue
        ordering, timer_ms, delay_ms, lease_ms = expected[name]
        config_ok = (case["ordering"] == ordering and case["timer_ms"] == timer_ms
                     and case["clock_delay_ms"] == delay_ms and case["lease_ms_from_start"] == lease_ms)
        start, timer, clock, cancel = (case[k] for k in
                                      ("started_ns", "timer_expired_ns", "clock_return_ns", "cancel_requested_ns"))
        observed, release = case["cancel_observed_ns"], case["release_ns"]
        t_ms = (timer - start) / 1e6
        clock_from_timer_ms = (clock - timer) / 1e6
        cancel_from_timer_ms = (cancel - timer) / 1e6
        release_from_timer_ms = (release - timer) / 1e6
        release_from_cancel_ms = (release - cancel) / 1e6
        release_from_start_ms = (release - start) / 1e6
        if ordering == "clock-before-cancel":
            timing_order_ok = timer < clock <= cancel
        else:
            timing_order_ok = timer <= cancel < clock
        event_names = [event.get("event") for event in case["events"]]
        cancel_event_index = next((j for j, event in enumerate(case["events"])
                                   if event.get("event") == "cancel_requested"), None)
        terminal_index = next((j for j, event in enumerate(case["events"])
                               if event.get("event") == "terminal"), None)
        event_order_ok = cancel_event_index is not None and terminal_index is not None
        if name.startswith("A-") or name.startswith("C-"):
            event_order_ok = (event_order_ok and cancel_event_index < terminal_index and observed is not None
                              and cancel <= observed <= release)
        else:
            event_order_ok = (event_order_ok and terminal_index < cancel_event_index and observed is None)
        release_ok = case["release_verified"] is True and release <= case["terminal_ns"]
        if name.startswith("A-"):
            gate = (case["cancel_matched"] is True and release_ok and timing_order_ok and event_order_ok
                    and 350 <= release_from_timer_ms < lease_ms - t_ms
                    and 0 <= release_from_cancel_ms <= 50)
        elif name.startswith("B-"):
            gate = (case["cancel_matched"] is False and release_ok and timing_order_ok and event_order_ok
                    and abs(release_from_start_ms - lease_ms) <= 50 and release < clock
                    and case["terminal_status"] == "expired")
        else:
            gate = (case["cancel_matched"] is True and release_ok and timing_order_ok and event_order_ok
                    and 0 <= release_from_timer_ms <= 50 and release < clock)
        checks.append({"check": f"case:{name}", "configuration_ok": config_ok,
                       "timer_from_start_ms": t_ms, "clock_from_timer_ms": clock_from_timer_ms,
                       "cancel_from_timer_ms": cancel_from_timer_ms,
                       "release_from_timer_ms": release_from_timer_ms,
                       "release_from_cancel_ms": release_from_cancel_ms,
                       "release_from_start_ms": release_from_start_ms,
                       "timing_order_ok": timing_order_ok, "event_order_ok": event_order_ok,
                       "cancel_matched": case["cancel_matched"], "terminal_status": case["terminal_status"],
                       "release_verified": release_ok, "event_names": event_names,
                       "preregistered_gate": gate})
        if not config_ok or not gate:
            errors.append(f"preregistered gate not met: {name}")
        derived[name] = release_from_timer_ms

    if set(derived) != set(expected):
        errors.append("candidate case set mismatch")
    if set(derived) == set(expected):
        contrast = derived["A-clock-before-cancel-within-lease"] - derived["C-cancel-before-clock-within-lease"]
        checks.append({"check": "A-minus-C release delay", "milliseconds": contrast,
                       "ok": contrast >= 300})
        if contrast < 300:
            errors.append("A/C contrast below 300 ms")

    decision = "PASS_CLOCK_DELAY_EXTENDS_WITHIN_LEASE_SCOPED" if not errors else "FAIL_OR_HOLD_PREREGISTERED_GATE"
    audit = {"schema": "map01-v6-clock-cancel-order-t2-audit-v1", "allocation":
             "MAP01-V6-CLOCK-CANCEL-ORDER-59-T2-AUDIT-20261002-01", "raw_commit": RAW_COMMIT,
             "raw_path": RAW_PATH, "raw_sha256": raw_digest, "base_commit": BASE,
             "source_checks": source_checks, "checks": checks, "decision": decision,
             "errors": errors, "audit_invocations": 1, "candidate_invocations": 0}
    (OUT / "candidate_raw_snapshot.json").write_bytes(raw_bytes)
    (OUT / "independent_audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
