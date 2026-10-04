#!/usr/bin/env python3
"""Versioned independent audit that validates every reported window field."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
F = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))


def pinned(path):
    raw = subprocess.check_output(["git", "show", F["base_commit"] + ":" + path])
    if hashlib.sha256(raw).hexdigest() != F["source_blobs"][path]["sha256"]:
        raise SystemExit("STOP_SOURCE_HASH_MISMATCH:" + path)
    return raw


def reconstruct(report, records):
    typed = [row for row in records if row.get("event") == "typed_observation"]
    scores = sum(row.get("event") == "post_control_score" for row in records)
    windows = []
    for decision in report["decisions"]:
        cover = decision.get("cover_policy") or []
        actions = [item["action"] for item in cover]
        if not any(action in {"fire", "retreat_fire", "advance_fire"} for action in actions):
            continue
        start = decision["controller_model_started_ns"]
        end = decision["controller_model_ended_ns"]
        rows = [row for row in typed if start <= row.get("capture_ns", -1) <= end]

        def values_for(signal):
            return [row["signals"][signal]["value"] for row in rows
                    if row.get("signals", {}).get(signal, {}).get("status") == "observed"
                    and type(row["signals"][signal].get("value")) is int]

        ammo = values_for("ammo")
        health = values_for("health")
        invalidation = decision.get("final_action_admission", {}).get(
            "policy_invalidation") or {}
        windows.append({
            "decision": decision["iteration"],
            "cover_actions": actions,
            "model_wait_ms": round((end - start) / 1e6, 3),
            "typed_observations": len(rows),
            "ammo_first_last_min": [ammo[0], ammo[-1], min(ammo)] if ammo else None,
            "ammo_decrements": sum(b < a for a, b in zip(ammo, ammo[1:])),
            "ammo_zero_observed": any(value == 0 for value in ammo),
            "health_first_last": [health[0], health[-1]] if health else None,
            "policy_invalidation_signal": invalidation.get("signal", {}).get("signal_id"),
        })
    return windows, len(typed), len(records), sorted({row.get("event") for row in records}), scores


def main():
    report_path, events_path = F["source_blobs"].keys()
    report = json.loads(pinned(report_path))
    records = [json.loads(line) for line in pinned(events_path).splitlines() if line]
    windows, typed_total, event_total, event_names, score_rows = reconstruct(report, records)
    result = json.loads((ROOT / "RESULT.json").read_text(encoding="utf-8"))
    zero = any(row["ammo_zero_observed"] for row in windows)
    expected_disposition = "ZERO_AMMO_EXPOSED" if zero else "NO_ZERO_EXPOSURE"

    checks = {
        "all_window_fields_reconstructed": result.get("windows") == windows,
        "active_window_count_matches": result.get("active_fire_cover_windows") == len(windows),
        "typed_observation_count_matches": result.get("typed_observations_total") == typed_total,
        "event_row_count_matches": result.get("runtime_event_rows_total") == event_total,
        "event_names_match": result.get("event_names") == event_names,
        "score_row_count_matches": result.get("post_control_score_rows") == score_rows,
        "zero_exposure_matches": result.get("zero_ammo_exposure") is zero,
        "disposition_matches_raw": result.get("disposition") == expected_disposition,
        "posthoc_classification_preserved": "posthoc" in result.get("classification", ""),
        "live_allocations_added_zero": result.get("live_allocation_invocations_added") == 0,
        "no_per_window_effect_events_claimed": result.get("per_window_useful_effect_events") == 0,
    }
    audit = {"format": "59-v39-fire-cover-ammo-posthoc-audit-v2",
             "checks": checks, "passed": sum(checks.values()), "total": len(checks),
             "disposition": "PASS" if all(checks.values()) else "AUDIT_FAILED"}
    (ROOT / "AUDIT_V2.json").write_text(
        json.dumps(audit, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps(audit, sort_keys=True))


if __name__ == "__main__":
    main()
