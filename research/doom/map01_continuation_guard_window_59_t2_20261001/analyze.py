#!/usr/bin/env python3
"""Extract a counterfactual health-guard boundary from retained v39 telemetry."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RUN = REPO / "research/doom/results/map01-v39-coast-liveness-live-01"
EXPECTED = {
    "report.json": "719db21040b843c5c91c5ff1f3d9fb2051ae1f1e008971547f39f015b4337687",
    "retention-manifest.json": "8dfbac52c298d865b4484aaa51dc0d821bb0d74f8c5995d3117206a1ed0dbda2",
    "runtime/events.jsonl": "2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381",
}


def _decision(report: dict[str, Any], iteration: int) -> dict[str, Any]:
    matches = [d for d in report.get("decisions", []) if d.get("iteration") == iteration]
    if len(matches) != 1:
        raise ValueError(f"expected one decision {iteration}, found {len(matches)}")
    return matches[0]


def analyze_window(report: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    decision = _decision(report, 2)
    start = decision.get("controller_model_started_ns")
    end = decision.get("controller_model_ended_ns")
    source = decision.get("final_action_admission", {}).get("action_validity", {}).get("contract", {}).get("source", {})
    source_sequence = source.get("sequence")
    health = source.get("signals", {}).get("health", {})
    source_health = health.get("value")
    if any(type(v) is not int for v in (start, end, source_sequence, source_health)) or end <= start:
        raise ValueError("incomplete or invalid frozen model/source boundary")

    observations = sorted(
        (r for r in rows if r.get("event") == "typed_observation"
         and type(r.get("capture_ns")) is int and start <= r["capture_ns"] < end),
        key=lambda r: (r["capture_ns"], r.get("sequence", -1)),
    )
    trigger = None
    for row in observations:
        sequence = row.get("sequence")
        signal = row.get("signals", {}).get("health", {})
        if type(sequence) is not int or sequence <= source_sequence:
            reason = "non_fresh_sequence"
        elif signal.get("status") != "observed" or type(signal.get("value")) is not int:
            reason = "health_unavailable"
        elif signal["value"] < source_health:
            reason = "health_below_source"
        else:
            continue
        trigger = {
            "sequence": sequence,
            "capture_ns": row["capture_ns"],
            "typed_ready_ns": row.get("typed_ready_ns"),
            "emit_ns": row.get("emit_ns"),
            "health_status": signal.get("status"),
            "health_value": signal.get("value"),
            "reason": reason,
        }
        break

    result: dict[str, Any] = {
        "schema": "map01-continuation-guard-window-raw-v1",
        "target_iteration": 2,
        "model_start_ns": start,
        "model_end_ns": end,
        "model_wait_ns": end - start,
        "source_sequence": source_sequence,
        "source_health_floor": source_health,
        "typed_observations_in_model_window": len(observations),
        "trigger": trigger,
    }
    if trigger is None:
        result.update(disposition="NO_GUARD_REJECTION_OBSERVED")
        return result
    for field, suffix in (("capture_ns", "capture"), ("typed_ready_ns", "typed_ready"), ("emit_ns", "emit")):
        value = trigger.get(field)
        if type(value) is int:
            result[f"elapsed_after_{suffix}_ns"] = value - start
            result[f"remaining_after_{suffix}_ns"] = end - value
    result["disposition"] = "PASS_RETAINED_WINDOW_DIAGNOSTIC"
    return result


def load_events(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=HERE / "results/raw.json")
    args = parser.parse_args()
    for relative, expected in EXPECTED.items():
        actual = hashlib.sha256((RUN / relative).read_bytes()).hexdigest()
        if actual != expected:
            raise SystemExit(f"STOP_SOURCE_HASH_MISMATCH {relative} {actual}")
    report = json.loads((RUN / "report.json").read_text(encoding="utf-8"))
    rows = load_events(RUN / "runtime/events.jsonl")
    result = analyze_window(report, rows)
    result["input_sha256"] = EXPECTED
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"disposition": result["disposition"], "trigger": result["trigger"],
                      "remaining_after_emit_ns": result.get("remaining_after_emit_ns")}, sort_keys=True))


if __name__ == "__main__":
    main()
