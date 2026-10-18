#!/usr/bin/env python3
"""Read-only posthoc analysis of pinned retained v39 Git blobs."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FREEZE = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
OUT = ROOT / "RESULT.json"


def blob(path):
    return subprocess.check_output(
        ["git", "show", f"{FREEZE['base_commit']}:{path}"]
    )


def main():
    if OUT.exists():
        raise SystemExit("STOP_OUTPUT_EXISTS")
    documents = {}
    for path, receipt in FREEZE["source_blobs"].items():
        raw = blob(path)
        digest = hashlib.sha256(raw).hexdigest()
        if digest != receipt["sha256"]:
            raise SystemExit("STOP_SOURCE_HASH_MISMATCH:" + path)
        documents[path] = raw
    report_path, events_path = list(FREEZE["source_blobs"])
    report = json.loads(documents[report_path])
    events = [json.loads(line) for line in documents[events_path].splitlines() if line]
    typed = [row for row in events if row.get("event") == "typed_observation"]
    windows = []
    for decision in report["decisions"]:
        cover = decision.get("cover_policy") or []
        if not any(item.get("action") in {"fire", "retreat_fire", "advance_fire"}
                   for item in cover):
            continue
        start = decision["controller_model_started_ns"]
        end = decision["controller_model_ended_ns"]
        rows = [row for row in typed if start <= row.get("capture_ns", -1) <= end]
        ammo = [row["signals"]["ammo"]["value"] for row in rows
                if row.get("signals", {}).get("ammo", {}).get("status") == "observed"
                and type(row["signals"]["ammo"].get("value")) is int]
        health = [row["signals"]["health"]["value"] for row in rows
                  if row.get("signals", {}).get("health", {}).get("status") == "observed"
                  and type(row["signals"]["health"].get("value")) is int]
        invalidation = decision.get("final_action_admission", {}).get("policy_invalidation") or {}
        windows.append({
            "decision": decision["iteration"],
            "cover_actions": [item["action"] for item in cover],
            "model_wait_ms": round((end - start) / 1e6, 3),
            "typed_observations": len(rows),
            "ammo_first_last_min": [ammo[0], ammo[-1], min(ammo)] if ammo else None,
            "ammo_decrements": sum(next_value < value
                                    for value, next_value in zip(ammo, ammo[1:])),
            "ammo_zero_observed": any(value == 0 for value in ammo),
            "health_first_last": [health[0], health[-1]] if health else None,
            "policy_invalidation_signal": invalidation.get("signal", {}).get("signal_id"),
        })
    event_names = sorted({row.get("event") for row in events})
    scorer_rows = [row for row in events if row.get("event") == "post_control_score"]
    zero_exposure = any(window["ammo_zero_observed"] for window in windows)
    result = {
        "format": "59-v39-fire-cover-ammo-posthoc-result-v1",
        "classification": "posthoc read-only reconstruction; not preregistered",
        "source_base_commit": FREEZE["base_commit"],
        "source_hashes_verified": True,
        "live_allocation_invocations_added": 0,
        "active_fire_cover_windows": len(windows),
        "windows": windows,
        "typed_observations_total": len(typed),
        "runtime_event_rows_total": len(events),
        "event_names": event_names,
        "post_control_score_rows": len(scorer_rows),
        "per_window_useful_effect_events": 0,
        "zero_ammo_exposure": zero_exposure,
        "disposition": "ZERO_AMMO_EXPOSED" if zero_exposure else "NO_ZERO_EXPOSURE",
    }
    OUT.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
                   encoding="utf-8")
    print(json.dumps({k: result[k] for k in (
        "classification", "active_fire_cover_windows", "typed_observations_total",
        "runtime_event_rows_total", "post_control_score_rows", "zero_ammo_exposure",
        "disposition", "windows")}, sort_keys=True))


if __name__ == "__main__":
    main()
