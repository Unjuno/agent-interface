"""Reconstruct HUD signal changes during retained V39 model-pending intervals."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reconstruct(root: Path, hash_override: dict[str, str] | None = None) -> dict:
    report_path = root / "report.json"
    events_path = root / "events.jsonl"
    delivered_path = root / "delivered.jsonl"
    freeze = json.loads((root / "FREEZE.json").read_text(encoding="utf-8"))
    for name, expected in freeze["inputs"].items():
        actual_hash = (hash_override or {}).get(name, sha(root / name))
        if actual_hash != expected:
            raise ValueError(f"frozen input hash mismatch: {name}")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()]
    delivered = [json.loads(line) for line in delivered_path.read_text(encoding="utf-8").splitlines()]
    if events != delivered:
        raise ValueError("delivered event stream differs from source event stream")
    obs = {row["sequence"]: row for row in events if row.get("event") == "typed_observation"}
    if len(obs) != 218 or sorted(obs) != list(range(1, 219)):
        raise ValueError("expected the complete typed observation sequence 1..218")
    for sequence, row in obs.items():
        if row["signals"]["health"]["sequence"] != sequence or row["signals"]["ammo"]["sequence"] != sequence:
            raise ValueError(f"signal sequence mismatch at observation {sequence}")

    windows = []
    for decision in report["decisions"]:
        source = decision["cover_validity_admission"]["source_signal"]
        start_seq = source["sequence"]
        terminal_ns = decision["planner_terminal_observed_ns"]
        eligible = [
            (seq, row) for seq, row in obs.items()
            if seq >= start_seq and row["capture_ns"] <= terminal_ns
        ]
        if not eligible or eligible[0][0] != start_seq:
            raise ValueError(f"missing source observation for decision {decision['iteration']}")
        changes = []
        previous = None
        for seq, row in eligible:
            signals = row["signals"]
            values = {key: signals[key]["value"] for key in ("health", "ammo")}
            if previous is None or values != previous:
                changes.append({
                    "sequence": seq,
                    **values,
                    "elapsed_ms_from_source": round((row["capture_ns"] - source["capture_ns"]) / 1e6, 3),
                })
            previous = values
        effective = decision["cover_validity_admission"]["effective"]
        windows.append({
            "decision": decision["iteration"],
            "source_sequence": start_seq,
            "source_health": source["value"],
            "source_capture_ns": source["capture_ns"],
            "planner_terminal_observed_ns": terminal_ns,
            "pending_duration_ms": round((terminal_ns - source["capture_ns"]) / 1e6, 3),
            "last_pending_sequence": eligible[-1][0],
            "mode": decision["cover_validity_admission"]["monitor_mode"],
            "authored_policy": decision["cover_validity_admission"]["authored"],
            "effective_hard_minimum": effective["hard_minimum"],
            "pending_changes": changes,
        })

    all_typed_artifacts = report.get("typed_artifact_reconciled") == 218 and report.get("typed_artifact_reconciliation_failures") == 0
    invalidations = report.get("policy_invalidations")
    authored = [w for w in windows if w["authored_policy"]]
    threshold_events = [
        {"decision": w["decision"], "sequence": c["sequence"], "health": c["health"], "hard_minimum": w["effective_hard_minimum"]}
        for w in authored for c in w["pending_changes"] if c["health"] <= w["effective_hard_minimum"]
        and (c["sequence"] == next((row["sequence"] for row in w["pending_changes"] if row["health"] <= w["effective_hard_minimum"]), None))
    ]
    loss_guard_events = []
    for w in authored:
        for c in w["pending_changes"]:
            if w["source_health"] - c["health"] >= w["authored_policy"]["maximum_health_loss"]:
                loss_guard_events.append({"decision": w["decision"], "sequence": c["sequence"], "health": c["health"], "source_health": w["source_health"], "maximum_health_loss": w["authored_policy"]["maximum_health_loss"]})
                break
    result = {
        "schema": "v39-retained-pending-signal-trajectory-v1",
        "run_id": "map01-v39-coast-liveness-live-01",
        "input_sha256": {name: sha(root / name) for name in ("report.json", "events.jsonl", "delivered.jsonl")},
        "observation_count": len(obs),
        "typed_artifact_reconciliation_passed": all_typed_artifacts,
        "event_and_delivered_streams_identical": True,
        "decision_windows": windows,
        "authored_threshold_events": threshold_events,
        "authored_loss_guard_events": loss_guard_events,
        "recorded_policy_invalidations": invalidations,
        "limitations": [
            "Signal values are HUD-template interpretations in the retained run, not independent game-state ground truth.",
            "This is posthoc analysis of a historical run, not a fresh current-main execution or a controller intervention.",
            "Temporal correlation does not establish causation or recovery efficacy; the run remained unfinished.",
        ],
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).parent)
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "RESULT.json")
    args = parser.parse_args()
    result = reconstruct(args.root)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
