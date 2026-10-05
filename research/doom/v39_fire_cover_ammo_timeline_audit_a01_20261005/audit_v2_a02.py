#!/usr/bin/env python3
"""Raw-only field-by-field reconstruction of the retained V39 ammo summary."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FREEZE = json.loads((ROOT / "FREEZE_A02.json").read_text(encoding="utf-8"))
OUTPUT = ROOT / "CANDIDATE_A02.json"
FIRE_ACTIONS = {"fire", "retreat_fire", "advance_fire"}


def read_pin(pin):
    source = pin["commit"] + ":" + pin["path"]
    raw = subprocess.check_output(["git", "show", source])
    blob = subprocess.check_output(["git", "rev-parse", source], text=True).strip()
    if blob != pin["git_blob"] or hashlib.sha256(raw).hexdigest() != pin["sha256"]:
        raise ValueError("PIN_MISMATCH:" + pin["path"])
    return raw


def load_inputs():
    report = json.loads(read_pin(FREEZE["raw_inputs"]["report"]))
    events = [json.loads(line) for line in
              read_pin(FREEZE["raw_inputs"]["events"]).splitlines() if line]
    package_blobs = {
        name: read_pin(pin)
        for name, pin in FREEZE["parent_package_files"].items()
    }
    original = json.loads(package_blobs["result"])
    return report, events, original


def build_expected(report, events):
    typed = [row for row in events if row.get("event") == "typed_observation"]
    windows = []
    for decision in report["decisions"]:
        cover = decision.get("cover_policy") or []
        actions = [item["action"] for item in cover]
        if not FIRE_ACTIONS.intersection(actions):
            continue
        start = decision["controller_model_started_ns"]
        end = decision["controller_model_ended_ns"]
        if type(start) is not int or type(end) is not int or end < start:
            raise ValueError("INVALID_MODEL_WAIT_INTERVAL")
        sample = [row for row in typed
                  if type(row.get("capture_ns")) is int
                  and start <= row["capture_ns"] <= end]
        ammo = [signal["value"] for row in sample
                for signal in [row.get("signals", {}).get("ammo", {})]
                if signal.get("status") == "observed"
                and type(signal.get("value")) is int]
        health = [signal["value"] for row in sample
                  for signal in [row.get("signals", {}).get("health", {})]
                  if signal.get("status") == "observed"
                  and type(signal.get("value")) is int]
        invalidation = decision.get("final_action_admission", {}).get(
            "policy_invalidation") or {}
        windows.append({
            "decision": decision["iteration"],
            "cover_actions": actions,
            "model_wait_ms": round((end - start) / 1_000_000, 3),
            "typed_observations": len(sample),
            "ammo_first_last_min": [ammo[0], ammo[-1], min(ammo)] if ammo else None,
            "ammo_decrements": sum(next_value < value
                                   for value, next_value in zip(ammo, ammo[1:])),
            "ammo_zero_observed": any(value == 0 for value in ammo),
            "health_first_last": [health[0], health[-1]] if health else None,
            "policy_invalidation_signal":
                invalidation.get("signal", {}).get("signal_id"),
        })
    scores = [row for row in events if row.get("event") == "post_control_score"]
    zero = any(window["ammo_zero_observed"] for window in windows)
    return {
        "format": "59-v39-fire-cover-ammo-posthoc-result-v1",
        "classification": "posthoc read-only reconstruction; not preregistered",
        "source_base_commit": FREEZE["analysis_base_commit"],
        "source_hashes_verified": True,
        "live_allocation_invocations_added": 0,
        "active_fire_cover_windows": len(windows),
        "windows": windows,
        "typed_observations_total": len(typed),
        "runtime_event_rows_total": len(events),
        "event_names": sorted({row.get("event") for row in events}),
        "post_control_score_rows": len(scores),
        "per_window_useful_effect_events": 0,
        "zero_ammo_exposure": zero,
        "disposition": "ZERO_AMMO_EXPOSED" if zero else "NO_ZERO_EXPOSURE",
    }


def mismatches(expected, observed):
    failures = []
    if not isinstance(observed, dict):
        return ["result.object"]
    if set(observed) != set(expected):
        failures.append("result.keys")
    for field, value in expected.items():
        if field == "windows":
            actual = observed.get(field)
            if not isinstance(actual, list) or len(actual) != len(value):
                failures.append("windows.count")
                continue
            for index, expected_row in enumerate(value):
                if not isinstance(actual[index], dict):
                    failures.append("windows[{}].row".format(index))
                    continue
                if set(actual[index]) != set(expected_row):
                    failures.append("windows[{}].keys".format(index))
                for name, expected_value in expected_row.items():
                    if name not in actual[index] or actual[index][name] != expected_value:
                        failures.append("windows[{}].{}".format(index, name))
        elif observed.get(field) != value:
            failures.append(field)
    return failures


def run():
    if OUTPUT.exists():
        raise SystemExit("STOP_OUTPUT_EXISTS")
    report, events, original = load_inputs()
    expected = build_expected(report, events)
    failures = mismatches(expected, original)
    result = {
        "format": "issue59-v39-fire-cover-ammo-audit-a02-candidate-v1",
        "source_commit": FREEZE["analysis_base_commit"],
        "parent_package_commit": FREEZE["parent_package_commit"],
        "fields_compared": sum(len(row) for row in expected["windows"])
                           + len(expected) - 1,
        "mismatches": failures,
        "disposition": "PASS_EXACT_RECONSTRUCTION" if not failures
                       else "FAIL_RESULT_MISMATCH",
    }
    OUTPUT.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
                      encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return result


if __name__ == "__main__":
    run()
