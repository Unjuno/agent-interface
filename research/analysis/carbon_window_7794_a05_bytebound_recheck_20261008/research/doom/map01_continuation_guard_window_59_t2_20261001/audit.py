#!/usr/bin/env python3
"""Independent raw-only verifier for the retained-data window calculation."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RUN = REPO / "research/doom/results/map01-v39-coast-liveness-live-01"
PINS = {
    "report.json": "719db21040b843c5c91c5ff1f3d9fb2051ae1f1e008971547f39f015b4337687",
    "retention-manifest.json": "8dfbac52c298d865b4484aaa51dc0d821bb0d74f8c5995d3117206a1ed0dbda2",
    "runtime/events.jsonl": "2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381",
}
EXPECTED = {
    "model_start_ns": 55518326410055,
    "model_end_ns": 55524633283877,
    "model_wait_ns": 6306873822,
    "source_sequence": 70,
    "source_health_floor": 85,
    "typed_observations_in_model_window": 20,
    "trigger": {
        "sequence": 76,
        "capture_ns": 55519816371806,
        "typed_ready_ns": 55519826917497,
        "emit_ns": 55519829635969,
        "health_status": "observed",
        "health_value": 82,
        "reason": "health_below_source",
    },
    "elapsed_after_capture_ns": 1489961751,
    "remaining_after_capture_ns": 4816912071,
    "elapsed_after_typed_ready_ns": 1500507442,
    "remaining_after_typed_ready_ns": 4806366380,
    "elapsed_after_emit_ns": 1503225914,
    "remaining_after_emit_ns": 4803647908,
    "disposition": "PASS_RETAINED_WINDOW_DIAGNOSTIC",
}


def verify(raw: dict, report: dict, lines: list[str]) -> dict:
    actual_pins = {name: hashlib.sha256((RUN / name).read_bytes()).hexdigest() for name in PINS}
    if actual_pins != PINS or raw.get("input_sha256") != PINS:
        return {"audit": "FAIL_SOURCE_IDENTITY", "actual_input_sha256": actual_pins}
    decisions = [d for d in report["decisions"] if d.get("iteration") == 2]
    if len(decisions) != 1:
        return {"audit": "FAIL_DECISION_IDENTITY", "matches": len(decisions)}
    d = decisions[0]
    source = d["final_action_admission"]["action_validity"]["contract"]["source"]
    start, end = d["controller_model_started_ns"], d["controller_model_ended_ns"]
    source_seq = source["sequence"]
    floor = source["signals"]["health"]["value"]
    observations = []
    for line in lines:
        row = json.loads(line)
        if row.get("event") != "typed_observation":
            continue
        capture = row.get("capture_ns")
        if type(capture) is int and start <= capture < end:
            observations.append(row)
    observations.sort(key=lambda r: (r["capture_ns"], r.get("sequence", -1)))
    first = None
    for row in observations:
        sig = row.get("signals", {}).get("health", {})
        seq = row.get("sequence")
        if type(seq) is not int or seq <= source_seq:
            reason = "non_fresh_sequence"
        elif sig.get("status") != "observed" or type(sig.get("value")) is not int:
            reason = "health_unavailable"
        elif sig["value"] < floor:
            reason = "health_below_source"
        else:
            continue
        first = {"sequence": seq, "capture_ns": row["capture_ns"],
                 "typed_ready_ns": row.get("typed_ready_ns"), "emit_ns": row.get("emit_ns"),
                 "health_status": sig.get("status"), "health_value": sig.get("value"),
                 "reason": reason}
        break
    recomputed = {
        "model_start_ns": start, "model_end_ns": end, "model_wait_ns": end - start,
        "source_sequence": source_seq, "source_health_floor": floor,
        "typed_observations_in_model_window": len(observations), "trigger": first,
    }
    if first is not None:
        for key, suffix in (("capture_ns", "capture"), ("typed_ready_ns", "typed_ready"), ("emit_ns", "emit")):
            t = first.get(key)
            if type(t) is int:
                recomputed[f"elapsed_after_{suffix}_ns"] = t - start
                recomputed[f"remaining_after_{suffix}_ns"] = end - t
        recomputed["disposition"] = "PASS_RETAINED_WINDOW_DIAGNOSTIC"
    else:
        recomputed["disposition"] = "NO_GUARD_REJECTION_OBSERVED"
    gate_mismatches = {k: {"expected": v, "recomputed": recomputed.get(k)}
                       for k, v in EXPECTED.items() if recomputed.get(k) != v}
    mismatches = {k: {"raw": raw.get(k), "recomputed": v}
                  for k, v in recomputed.items() if raw.get(k) != v}
    return {"audit": "PASS_FROZEN_GATE_AND_RAW_RECOMPUTE"
            if not mismatches and not gate_mismatches else "FAIL_AUDIT",
            "mismatches": mismatches, "gate_mismatches": gate_mismatches,
            "recomputed": recomputed,
            "event_lines": len(lines), "within_invocation_retries": 0}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, default=HERE / "results/raw.json")
    args = parser.parse_args()
    raw = json.loads(args.raw.read_text(encoding="utf-8"))
    report = json.loads((RUN / "report.json").read_text(encoding="utf-8"))
    lines = (RUN / "runtime/events.jsonl").read_text(encoding="utf-8").splitlines()
    result = verify(raw, report, lines)
    (HERE / "results/audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"audit": result["audit"], "mismatches": result["mismatches"]}, sort_keys=True))
    if result["audit"] != "PASS_FROZEN_GATE_AND_RAW_RECOMPUTE":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
