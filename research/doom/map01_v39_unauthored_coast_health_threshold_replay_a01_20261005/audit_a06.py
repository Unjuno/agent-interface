#!/usr/bin/env python3
"""Audit-only A06 correction for the retained A04 trace; never runs candidate."""
import hashlib
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parent
INP = Path(os.environ.get("AUDIT_INPUT_DIR", ROOT / "input/a04"))
FREEZE_PATH = Path(os.environ.get("AUDIT_FREEZE_PATH", ROOT / "FREEZE.json"))
FREEZE = json.loads(FREEZE_PATH.read_text())
DEFAULT_OUTPUT = ROOT / "results/a06/audit.json"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sums(path):
    rows = path.read_text().replace("\\n", "\n").splitlines()
    return {name: value for row in rows
            for value, name in [row.split("  ", 1)]}


def main():
    package = sums(INP / "PACKAGE_SHA256SUMS.txt")
    raw_sums = sums(INP / "RAW_SHA256SUMS.txt")
    assert package["results/RAW_SHA256SUMS.txt"] == digest(INP / "RAW_SHA256SUMS.txt")
    assert package["results/raw-a04.zip"] == FREEZE["source_raw_archive_sha256"]
    assert package["SOURCE_MANIFEST.json"] == digest(INP / "SOURCE_MANIFEST.json")
    for name in ("FREEZE.json", "RESULT.json", "AUDIT.json"):
        assert package[name] == digest(INP / name)
    assert raw_sums["runtime/events.jsonl"] == digest(INP / "runtime/events.jsonl") == FREEZE["source_event_sha256"]
    assert raw_sums["report.json"] == digest(INP / "report.json") == FREEZE["source_report_sha256"]

    stream = [json.loads(line) for line in (INP / "runtime/events.jsonl").read_text().splitlines()]
    report = json.loads((INP / "report.json").read_text())
    decision5 = report["decisions"][5]
    contract = decision5["final_action_admission"]["action_validity"]["contract"]
    health_source = contract["source"]["signals"]["health"]["value"]
    start = decision5["controller_model_started_ns"]
    end = decision5["final_action_admission"]["planner_terminal"]["terminal_observed_ns"]
    observations = []
    for event in stream:
        if event.get("event") != "typed_observation":
            continue
        health = event.get("signals", {}).get("health", {}).get("value")
        captured = event.get("capture_ns")
        if type(health) is int and type(captured) is int and start < captured <= end:
            observations.append((captured, event["sequence"], health))
    assert observations and all(
        observations[i][0] < observations[i + 1][0]
        and observations[i][1] < observations[i + 1][1]
        for i in range(len(observations) - 1))

    expected_sweep = []
    for threshold in FREEZE["thresholds_health_loss_points"]:
        crossing = next((row for row in observations if health_source - row[2] >= threshold), None)
        expected_sweep.append({
            "threshold_loss_points": threshold,
            "first_cross": None if crossing is None else {
                "sequence": crossing[1], "capture_ns": crossing[0], "health": crossing[2],
                "loss_points": health_source - crossing[2],
                "elapsed_from_model_start_ms": round((crossing[0] - start) / 1_000_000, 6),
                "remaining_to_planner_terminal_ms": round((end - crossing[0]) / 1_000_000, 6),
            },
        })

    # A06 intentionally audits the immutable A05 candidate bytes; candidate.py is never invoked.
    candidate_path = ROOT / "results/a05/candidate.json"
    candidate = json.loads(candidate_path.read_text())
    assert candidate["sweep"] == expected_sweep
    assert candidate["observations_during_pending_interval"] == len(observations)
    assert candidate["existing_final_action_rule"]["max_allowed_loss_points"] == 20
    assert candidate["existing_final_action_rule"]["observed_final_health"] == 4
    assert candidate["existing_final_action_rule"]["final_action_rejection_reason"] == "health_max_decrease_from_source_failed"

    decision4 = report["decisions"][4]
    source = decision4["cover_validity_admission"]["source_signal"]
    monitor = decision4["policy_invalidation"]["signals"]["health"]
    typed_by_sequence = {}
    for event in stream:
        if event.get("event") == "typed_observation":
            assert event["sequence"] not in typed_by_sequence
            typed_by_sequence[event["sequence"]] = event
    source_event = typed_by_sequence[source["sequence"]]
    monitor_event = typed_by_sequence[monitor["sequence"]]
    source_raw = source_event["signals"]["health"]
    monitor_raw = monitor_event["signals"]["health"]
    assert source_raw["signal_id"] == monitor_raw["signal_id"] == "health"
    assert source_raw["status"] == monitor_raw["status"] == "observed"
    assert source_raw["value"] == source["value"] == 30
    assert monitor_raw["value"] == monitor["value"] == 30
    assert source_event["capture_ns"] == source["capture_ns"] == source_raw["capture_ns"]
    assert monitor_event["capture_ns"] == monitor["capture_ns"] == monitor_raw["capture_ns"]
    assert source_event["sequence"] == source["sequence"]
    assert monitor_event["sequence"] == monitor["sequence"]
    # Bind the negative-control interpretation to temporal order, not just two valid raw rows.
    assert source_event["sequence"] < monitor_event["sequence"]
    assert source_event["capture_ns"] < monitor_event["capture_ns"]
    reason = decision4["policy_invalidation"]["reason"]
    assert reason == "health:source_expired"
    assert candidate["negative_control_decision4"]["source_health"] == source_raw["value"]
    assert candidate["negative_control_decision4"]["monitor_health"] == monitor_raw["value"]
    assert candidate["negative_control_decision4"]["reason"] == reason

    result = {
        "status": "PASS_A04_TRACE_AUDIT_CORRECTION_A06",
        "checks": 27,
        "observations": len(observations),
        "thresholds": len(expected_sweep),
        "archive_sha256": FREEZE["source_raw_archive_sha256"],
        "candidate_sha256": digest(candidate_path),
        "parent_a05_audit_sha256": digest(ROOT / "results/a05/audit.json"),
        "negative_control_raw_join": {
            "source_sequence": source["sequence"], "source_health": source_raw["value"],
            "source_capture_ns": source_raw["capture_ns"],
            "monitor_sequence": monitor["sequence"], "monitor_health": monitor_raw["value"],
            "monitor_capture_ns": monitor_raw["capture_ns"], "invalidation_reason": reason,
        },
    }
    output = Path(os.environ.get("AUDIT_OUTPUT", DEFAULT_OUTPUT))
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
