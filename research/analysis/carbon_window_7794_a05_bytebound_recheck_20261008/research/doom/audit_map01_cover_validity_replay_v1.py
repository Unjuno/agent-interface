"""Audit the model-free v28 typed health-envelope replay."""
import hashlib
import json
from pathlib import Path
import re

from doom_hud_signal_v1 import DoomStatusNumberReader


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = HERE / "results/map01-cover-validity-replay-v1"
SOURCE = HERE / "results/map01-fixed-threat-v28-live-01"
CROSS_SOURCE = HERE / "results/map01-cover-threat-v23-live-02"
WAD = REPO / "_vizdoom/vizdoom/freedoom2.wad"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    report = read(ROOT / "report.json")
    for path, expected in report["source_sha256"].items():
        assert sha(REPO / path) == expected, path
    assert report["status"] == "DEVELOPMENT_REPLAY_PASS" and report["model_calls"] == 0
    assert report["exact_observations_scanned"] == report["observed_signals"] == 70
    assert report["unknown_signals"] == 0 and report["reviewed_values_match"]

    cross = report["independent_cross_trace"]
    assert cross["source_allocation"] == "map01-cover-threat-v23-live-02"
    assert cross["exact_retained_decision_frames"] == 12
    assert cross["manually_reviewed_values_matched"] == 12
    assert cross["unknown_signals"] == 0
    cross_index = read(CROSS_SOURCE / "decision-frame-index.json")
    cross_audit = read(CROSS_SOURCE / "audit.json")
    cross_events = [json.loads(line) for line in
                    (CROSS_SOURCE / "runtime/events.jsonl").read_text().splitlines()]
    cross_observations = {row["sequence"]: row for row in cross_events
                          if row.get("event") == "observation"}
    cross_reader = DoomStatusNumberReader(WAD)
    expected_health = cross_audit["visual_transcription"]["health"]
    assert len(cross_index) == len(cross["rows"]) == len(expected_health) == 12
    observed_health = []
    for item, reported, expected in zip(cross_index, cross["rows"], expected_health):
        frame = CROSS_SOURCE / item["retained"]
        assert sha(frame) == item["sha256"] == reported["frame_sha256"]
        sequence = int(Path(item["original"]).stem)
        observation = dict(cross_observations[sequence])
        assert observation["exact"] is reported["exact"] is True
        observation["image"] = str(frame)
        reading = cross_reader.read(observation)
        assert reading["status"] == reported["status"] == "observed"
        assert reading["value"] == reported["observed_health"] == expected
        observed_health.append(reading["value"])
    assert observed_health == expected_health

    events = [json.loads(line) for line in (SOURCE / "runtime/events.jsonl").read_text().splitlines()]
    observations = [row for row in events if row.get("event") == "observation"]
    assert len(observations) == 70 and all(row["exact"] is True for row in observations)
    reader = DoomStatusNumberReader(
        WAD, image_resolver=lambda value: SOURCE / "runtime" / Path(value).name)
    readings = [reader.read(row) for row in observations]
    assert all(row["status"] == "observed" for row in readings)
    by_sequence = {row["sequence"]: row["value"] for row in readings}
    manual = {int(sequence): value for sequence, value in report["manually_reviewed_values"].items()}
    assert {sequence: by_sequence[sequence] for sequence in manual} == manual
    transitions = []
    previous = None
    for row in readings:
        if row["value"] != previous:
            transitions.append((row["sequence"], row["value"]))
            previous = row["value"]
    assert transitions == [(1, 100), (11, 97), (33, 100), (36, 93),
                           (51, 87), (60, 81), (68, 79), (70, 73)]
    assert [(row["sequence"], row["health"]) for row in report["health_transitions"]] == transitions

    candidate = report["candidate"]
    assert (candidate["source_sequence"], candidate["source_health"],
            candidate["hard_minimum"]) == (37, 93, 80)
    assert candidate["soft_transition_count"] == 2
    assert candidate["latest_soft_event"]["sequence"] == 60
    assert candidate["latest_soft_event"]["signal"]["value"] == 81
    assert candidate["latest_soft_event"]["outcome"]["status"] == "SOFT_CHANGED"
    assert candidate["latest_soft_event"]["outcome"]["keep_existing_policy"] is True
    hard = candidate["hard_event"]
    assert hard["sequence"] == 68 and hard["signal"]["value"] == 79
    assert hard["outcome"]["status"] == "HARD_INVALIDATED"
    assert hard["outcome"]["keep_existing_policy"] is False
    assert hard["outcome"]["requires_new_decision"] is True
    assert candidate["grants_new_input_authority"] is False
    assert report["baseline_first_change_sequence"] == 51
    assert report["candidate_hard_sequence"] == 68
    assert report["additional_exact_samples_before_hard_stop"] == 17
    assert report["baseline_change_to_candidate_hard_ms"] == 5240.235886
    assert 0 < report["extraction_ms"]["median"] <= report["extraction_ms"]["p95"] <= report["extraction_ms"]["max"]

    suspect = re.compile(rb"(?:sk-[A-Za-z0-9_-]{20,}|Authorization:\s*Bearer\s+\S+)", re.I)
    assert not suspect.search((ROOT / "report.json").read_bytes())
    audit = {
        "schema": "map01-cover-validity-replay-audit-v1",
        "passed": True,
        "status": report["status"],
        "model_calls": 0,
        "exact_frames_read": 82,
        "unknown_signal_reads": 0,
        "reviewed_values_matched": len(manual) + len(observed_health),
        "independent_cross_trace_frames": len(observed_health),
        "health_transitions": transitions,
        "soft_transitions_coalesced": 2,
        "hard_invalidation_sequence": 68,
        "additional_exact_samples_vs_v28_first_change": 17,
        "additional_observed_ms_vs_v28_first_change": 5240.235886,
        "extraction_ms": report["extraction_ms"],
        "credential_pattern_matches": 0,
        "decision": "retain as a development construction pass; add independent signal fixtures and integrate only after the typed envelope remains fail-closed outside this trace",
        "limits": report["limits"],
    }
    (ROOT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n",
                                      encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
