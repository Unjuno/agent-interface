from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "dependencies"))

from producer_scorer_session_envelope_join import attribute_acknowledged_events


def audit() -> dict:
    source_base = json.loads((ROOT / "SOURCE_BASE.json").read_text(encoding="utf-8"))
    source_pairs = (
        ("main", "independent_progress_clock_v2.py"),
        ("pr_7545", "acknowledged_scorer_v1.py"),
        ("pr_7546", "occurrence_attribution.py"),
    )
    for source_name, dependency_name in source_pairs:
        expected = source_base[source_name]["sha256"]
        actual = hashlib.sha256(
            (ROOT / "dependencies" / dependency_name).read_bytes()).hexdigest()
        assert actual == expected, f"source snapshot mismatch: {dependency_name}"
    raw = json.loads((ROOT / "results" / "t1-01" / "raw.json").read_text(encoding="utf-8"))
    assert raw["schema"] == "producer-scorer-session-envelope-raw-v1"
    assert len(raw["producer_samples"]) == len(raw["producer_updates"]) == 2
    assert [row["sample"] for row in raw["producer_updates"]] == raw["producer_samples"]
    assert len(raw["scorer_events"]) == 1

    event = raw["scorer_events"][0]
    linked = [row for row in raw["producer_samples"]
              if row["sample_ns"] == event["observed_ns"]]
    assert len(linked) == 1
    producer = linked[0]["producer"]
    assert producer["run_id"] == raw["run_id"]
    assert producer["sample_sequence"] == producer["update_sequence"] == 2

    lower = raw["producer_samples"][0]["sample_ns"]
    upper = event["observed_ns"]
    admission = raw["admissions"][0]
    receipt = raw["raw_releases"][0]["owner_thread_keyup_receipt"]
    assert admission["session_id"] == receipt_session(raw["raw_releases"][0]) == raw["run_id"]
    assert admission["input_occurrence_id"] == receipt["input_occurrence_id"] == "owner-a:1"
    assert admission["owner_id"] == receipt["owner_id"]
    assert admission["intent_token"] == receipt["intent_token"]
    assert admission["keycode"] == receipt["keycode"]
    assert receipt["server_sync_completed"] is True
    assert receipt["cancel_requested_after_sync"] is False
    assert admission["admitted_ns"] < lower <= upper < receipt["owner_sync_returned_ns"]
    assert len(raw["semantic_bindings"]) == 1
    binding = raw["semantic_bindings"][0]
    assert binding["session_id"] == raw["run_id"]
    assert (binding["program_id"], binding["step"]) == (admission["id"], admission["step"])
    assert len(binding["semantic_action_sha256"]) == 64

    result = raw["attribution"][0]
    assert result["status"] == "SINGLE_POSSIBLE_INTENT_ENVELOPE"
    assert result["possible_occurrence_ids"] == ["owner-a:1"]
    assert result["possible_intent_tokens"] == ["intent-a"]
    assert result["session_id"] == producer["run_id"]
    assert result["producer_sample_sequence"] == producer["sample_sequence"]
    assert result["producer_update_sequence"] == producer["update_sequence"]
    assert result["intent_token"] is None
    assert result["causal_attribution"] == "NOT_ESTABLISHED"
    assert result["causation_claimed"] is False

    cross_session = copy.deepcopy(raw)
    cross_session["raw_releases"][0]["session_id"] = "session-B"
    try:
        attribute_acknowledged_events(
            cross_session["producer_samples"], cross_session["scorer_events"],
            cross_session["admissions"], cross_session["raw_releases"],
            cross_session["semantic_bindings"])
    except ValueError as error:
        assert "session_id mismatch" in str(error)
    else:
        raise AssertionError("cross-session control was accepted")

    endpoint = copy.deepcopy(raw)
    endpoint_ns = endpoint["raw_releases"][0]["owner_thread_keyup_receipt"]["owner_sync_returned_ns"]
    endpoint["producer_samples"][1]["sample_ns"] = endpoint_ns
    endpoint["scorer_events"][0]["observed_ns"] = endpoint_ns
    endpoint_result = attribute_acknowledged_events(
        endpoint["producer_samples"], endpoint["scorer_events"],
        endpoint["admissions"], endpoint["raw_releases"],
        endpoint["semantic_bindings"])
    assert endpoint_result[0]["status"] == "UNRESOLVED"
    assert endpoint_result[0]["reason"] == "endpoint_tie_without_authenticated_order"

    return {
        "schema": "producer-scorer-session-envelope-audit-v1",
        "status": "PASS_SCOPED_SYNTHETIC_SESSION_ENVELOPE_COMPOSITION",
        "producer_link": "session-A/sample-2/update-2",
        "event_detection_bracket_ns": [lower, upper],
        "possible_occurrence_ids": ["owner-a:1"],
        "cross_session_control": "REJECTED",
        "release_endpoint_control": "UNRESOLVED",
        "interpretation": "POSSIBLE_INTENT_ENVELOPE_ONLY",
        "causation": "NOT_ESTABLISHED",
        "actual_owner_session_wiring": False,
        "actual_session_qualification": False,
        "frozen_source_hashes": len(source_pairs),
    }


def receipt_session(row: dict) -> str:
    return row["session_id"]


if __name__ == "__main__":
    result = audit()
    target = ROOT / "results" / "t1-01" / "audit.json"
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
