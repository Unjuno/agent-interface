from __future__ import annotations

import copy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "dependencies"))

from producer_scorer_occurrence_join import attribute_acknowledged_events


def audit() -> dict:
    raw = json.loads((ROOT / "results" / "t0-01" / "raw.json").read_text(encoding="utf-8"))
    assert raw["schema"] == "producer-scorer-occurrence-join-raw-v1"
    assert len(raw["samples"]) == 2 and len(raw["producer_updates"]) == 2
    assert [row["sample"] for row in raw["producer_updates"]] == raw["samples"]
    assert len(raw["events"]) == 1

    event = raw["events"][0]
    matching = [row for row in raw["samples"]
                if row["sample_ns"] == event["observed_ns"]]
    assert len(matching) == 1
    producer = matching[0]["producer"]
    assert producer["run_id"] == raw["run_id"]
    assert producer["sample_sequence"] == 2
    assert producer["update_sequence"] == 2

    # Independent temporal oracle for this one frozen event and one occurrence.
    admission = raw["admissions"][0]
    receipt = raw["raw_releases"][0]["owner_thread_keyup_receipt"]
    assert admission["run_id"] == receipt_run_id(raw["raw_releases"][0]) == raw["run_id"]
    assert admission["input_occurrence_id"] == receipt["input_occurrence_id"] == "owner-a:1"
    assert admission["owner_id"] == receipt["owner_id"]
    assert admission["intent_token"] == receipt["intent_token"]
    assert admission["keycode"] == receipt["keycode"]
    assert receipt["server_sync_completed"] is True
    assert receipt["cancel_requested_after_sync"] is False
    assert admission["input_ack_ns"] <= event["observed_ns"]
    assert event["observed_ns"] < receipt["owner_keyrelease_started_ns"]
    assert len(raw["semantic_bindings"]) == 1
    binding = raw["semantic_bindings"][0]
    assert (binding["run_id"], binding["program_id"], binding["step"]) == (
        raw["run_id"], admission["id"], admission["step"])
    assert len(binding["semantic_action_sha256"]) == 64

    result = raw["attribution"][0]
    assert result["status"] == "unique_temporal_occurrence"
    assert result["producer_run_id"] == raw["run_id"]
    assert result["producer_sample_sequence"] == producer["sample_sequence"]
    assert result["producer_update_sequence"] == producer["update_sequence"]
    assert result["input_occurrence_id"] == admission["input_occurrence_id"]
    assert result["causation_claimed"] is False

    cross_run = copy.deepcopy(raw)
    cross_run["raw_releases"][0]["run_id"] = "different-run"
    try:
        attribute_acknowledged_events(
            cross_run["samples"], cross_run["events"], cross_run["admissions"],
            cross_run["raw_releases"], cross_run["semantic_bindings"])
    except ValueError as error:
        assert "run_id mismatch" in str(error)
    else:
        raise AssertionError("cross-run control was accepted")

    boundary = copy.deepcopy(raw)
    boundary["events"][0]["observed_ns"] = receipt["owner_keyrelease_started_ns"]
    boundary_result = attribute_acknowledged_events(
        boundary["samples"], boundary["events"], boundary["admissions"],
        boundary["raw_releases"], boundary["semantic_bindings"])
    assert boundary_result[0]["status"] == "unresolved_release_boundary"

    return {
        "schema": "producer-scorer-occurrence-join-audit-v1",
        "status": "PASS_SCOPED_SYNTHETIC_SOURCE_COMPOSITION",
        "raw_event_count": 1,
        "sample_sidecar_exact_matches": 2,
        "producer_link": "run-A/sample-2/update-2",
        "occurrence_link": "owner-a:1",
        "cross_run_control": "REJECTED",
        "release_boundary_control": "UNRESOLVED",
        "causation": "NOT_ESTABLISHED",
        "actual_session_qualification": False,
    }


def receipt_run_id(row: dict) -> str:
    return row["run_id"]


if __name__ == "__main__":
    result = audit()
    target = ROOT / "results" / "t0-01" / "audit.json"
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
