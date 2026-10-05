#!/usr/bin/env python3
"""Independent grouped-stream reconstruction and candidate-output audit."""
import hashlib
import json
import subprocess
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FREEZE = json.loads((ROOT / "FREEZE_A02.json").read_text(encoding="utf-8"))
CANDIDATE = ROOT / "CANDIDATE_A02.json"
OUTPUT = ROOT / "AUDIT_A02.json"
FIRE_ACTIONS = frozenset(("fire", "retreat_fire", "advance_fire"))


def pinned_bytes(pin):
    source = "{}:{}".format(pin["commit"], pin["path"])
    raw = subprocess.check_output(["git", "show", source])
    actual_blob = subprocess.check_output(["git", "rev-parse", source], text=True).strip()
    if actual_blob != pin["git_blob"]:
        raise ValueError("GIT_BLOB_MISMATCH:" + pin["path"])
    if hashlib.sha256(raw).hexdigest() != pin["sha256"]:
        raise ValueError("SHA256_MISMATCH:" + pin["path"])
    return raw


def independently_reconstruct():
    report = json.loads(pinned_bytes(FREEZE["raw_inputs"]["report"]))
    stream = [json.loads(line) for line in
              pinned_bytes(FREEZE["raw_inputs"]["events"]).splitlines() if line]
    package = {name: pinned_bytes(pin)
               for name, pin in FREEZE["parent_package_files"].items()}
    previous = json.loads(package["result"])
    typed_by_time = defaultdict(list)
    for row in stream:
        if row.get("event") == "typed_observation" and type(row.get("capture_ns")) is int:
            typed_by_time[row["capture_ns"]].append(row)
    windows = []
    for decision in report["decisions"]:
        policy = decision.get("cover_policy") or []
        action_names = [item["action"] for item in policy]
        if all(name not in FIRE_ACTIONS for name in action_names):
            continue
        first = decision["controller_model_started_ns"]
        last = decision["controller_model_ended_ns"]
        observations = []
        for capture_ns, frames in typed_by_time.items():
            if first <= capture_ns <= last:
                observations.extend(frames)
        observations.sort(key=lambda item: item["capture_ns"])
        ammo = []
        health = []
        for frame in observations:
            for label, target in (("ammo", ammo), ("health", health)):
                signal = frame.get("signals", {}).get(label, {})
                value = signal.get("value")
                if signal.get("status") == "observed" and type(value) is int:
                    target.append(value)
        admission = decision.get("final_action_admission") or {}
        invalidation = admission.get("policy_invalidation") or {}
        windows.append({
            "decision": decision["iteration"],
            "cover_actions": action_names,
            "model_wait_ms": round((last - first) / 1_000_000, 3),
            "typed_observations": len(observations),
            "ammo_first_last_min": [ammo[0], ammo[-1], min(ammo)] if ammo else None,
            "ammo_decrements": sum(1 for left, right in zip(ammo, ammo[1:])
                                   if right < left),
            "ammo_zero_observed": 0 in ammo,
            "health_first_last": [health[0], health[-1]] if health else None,
            "policy_invalidation_signal":
                (invalidation.get("signal") or {}).get("signal_id"),
        })
    zero = any(row["ammo_zero_observed"] for row in windows)
    expected = {
        "format": "59-v39-fire-cover-ammo-posthoc-result-v1",
        "classification": "posthoc read-only reconstruction; not preregistered",
        "source_base_commit": FREEZE["analysis_base_commit"],
        "source_hashes_verified": True,
        "live_allocation_invocations_added": 0,
        "active_fire_cover_windows": len(windows),
        "windows": windows,
        "typed_observations_total": sum(
            1 for row in stream if row.get("event") == "typed_observation"),
        "runtime_event_rows_total": len(stream),
        "event_names": sorted({row.get("event") for row in stream}),
        "post_control_score_rows": sum(
            1 for row in stream if row.get("event") == "post_control_score"),
        "per_window_useful_effect_events": previous.get(
            "per_window_useful_effect_events"),
        "zero_ammo_exposure": zero,
        "disposition": "ZERO_AMMO_EXPOSED" if zero else "NO_ZERO_EXPOSURE",
    }
    return expected, previous


def differences(expected, observed):
    failed = []
    if not isinstance(observed, dict):
        return ["result.object"]
    if set(observed) != set(expected):
        failed.append("result.keys")
    for field, value in expected.items():
        if field != "windows":
            if observed.get(field) != value:
                failed.append(field)
            continue
        rows = observed.get("windows")
        if not isinstance(rows, list) or len(rows) != len(value):
            failed.append("windows.count")
            continue
        for index, wanted in enumerate(value):
            if not isinstance(rows[index], dict):
                failed.append("windows[{}].row".format(index))
                continue
            if set(rows[index]) != set(wanted):
                failed.append("windows[{}].keys".format(index))
            for key, item in wanted.items():
                if key not in rows[index] or rows[index][key] != item:
                    failed.append("windows[{}].{}".format(index, key))
    return failed


def run():
    if OUTPUT.exists():
        raise SystemExit("STOP_OUTPUT_EXISTS")
    if not CANDIDATE.exists():
        raise SystemExit("HOLD_CANDIDATE_MISSING")
    candidate = json.loads(CANDIDATE.read_text(encoding="utf-8"))
    expected, original = independently_reconstruct()
    failed = differences(expected, original)
    candidate_ok = (
        candidate.get("disposition") == "PASS_EXACT_RECONSTRUCTION"
        and candidate.get("mismatches") == []
        and candidate.get("fields_compared")
        == sum(len(row) for row in expected["windows"]) + len(expected) - 1
    )
    checks = {
        "independent_raw_reconstruction": not failed,
        "candidate_disposition_matches": candidate_ok,
    }
    result = {
        "format": "issue59-v39-fire-cover-ammo-audit-a02-independent-v1",
        "checks": checks,
        "raw_result_mismatches": failed,
        "passed": sum(checks.values()),
        "total": len(checks),
        "disposition": "PASS_INDEPENDENT_RECONSTRUCTION"
                       if all(checks.values()) else "AUDIT_FAILED",
    }
    OUTPUT.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
                      encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return result


if __name__ == "__main__":
    run()
