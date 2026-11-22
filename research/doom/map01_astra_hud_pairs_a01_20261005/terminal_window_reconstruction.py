"""Reconstruct the retained final 4%-to-0% observation window from raw clocks."""
import hashlib
import json
from pathlib import Path, PurePosixPath

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RESULTS = REPO / "research/doom/results/map01-astra-attempt-v1"


def read_inputs():
    pins = json.loads((HERE / "TERMINAL_WINDOW_INPUTS.json").read_text())
    for rel, expected in pins["inputs"].items():
        actual = hashlib.sha256((REPO / rel).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"INPUT_HASH_MISMATCH {rel}")
    report = json.loads((RESULTS / "report.json").read_text())
    events = [json.loads(line) for line in (RESULTS / "events.jsonl").read_text().splitlines()]
    manifest = json.loads((RESULTS / "frame-manifest.json").read_text())
    failure = json.loads((RESULTS / "failure-analysis-v1.json").read_text())
    return pins, report, events, manifest, failure


def analyze(report, events, manifest, failure):
    decisions = report["decisions"]
    before, terminal = decisions[11], decisions[12]
    by_sequence = {
        row["sequence"]: row
        for row in events
        if row.get("event") == "observation" and row.get("sequence") in (459, 498, 501, 504)
    }
    if set(by_sequence) != {459, 498, 501, 504}:
        raise ValueError("REQUIRED_OBSERVATION_SEQUENCE_MISSING")
    if any(row.get("exact") is not True for row in by_sequence.values()):
        raise ValueError("OBSERVATION_NOT_EXACT")
    if PurePosixPath(before["source_image"]).name != PurePosixPath(by_sequence[459]["image"]).name:
        raise ValueError("PRECALL_SOURCE_SEQUENCE_MISMATCH")
    if PurePosixPath(terminal["source_image"]).name != PurePosixPath(by_sequence[504]["image"]).name:
        raise ValueError("TERMINAL_SOURCE_SEQUENCE_MISMATCH")

    trace = before["execution_trace"]
    if [row["receipt"]["after_sequence"] for row in trace] != [498, 501, 504]:
        raise ValueError("ACTION_RECEIPT_SEQUENCE_MISMATCH")
    if [row["receipt"]["effect_observed_ns"] for row in trace] != [by_sequence[n]["capture_ns"] for n in (498, 501, 504)]:
        raise ValueError("ACTION_RECEIPT_CLOCK_MISMATCH")

    capture_before = by_sequence[459]["capture_ns"]
    capture_terminal = by_sequence[504]["capture_ns"]
    model_start = before["controller_model_started_ns"]
    model_end = before["controller_model_ended_ns"]
    action_accept = trace[0]["accepted_ns"]
    health = failure["visual_transcription"]["health"]
    frame_rows = {row["iteration"]: row for row in manifest}
    return {
        "schema": "map01-astra-terminal-window-v1",
        "disposition": "PASS_POSTHOC_CLOCK_RECONSTRUCTION",
        "decision_before": 11,
        "decision_terminal": 12,
        "observed_health_labels_manual": [health[11], health[12]],
        "observation_sequences": [459, 498, 501, 504],
        "capture_ns": {str(n): by_sequence[n]["capture_ns"] for n in (459, 498, 501, 504)},
        "timing_ms": {
            "precall_capture_to_model_start": (model_start - capture_before) / 1e6,
            "controller_model_start_to_end": (model_end - model_start) / 1e6,
            "controller_end_to_terminal_capture": (capture_terminal - model_end) / 1e6,
            "action_accept_to_terminal_capture": (capture_terminal - action_accept) / 1e6,
            "precall_capture_to_terminal_capture": (capture_terminal - capture_before) / 1e6,
        },
        "reported_model_ns": before["model_ns"],
        "actions": [row["command"] for row in trace],
        "selected_frame_sha256": {str(i): frame_rows[i]["sha256"] for i in (11, 12)},
        "interpretation": "The next retained exact observation with a manually transcribed health label is 0 after the three-command response. An enemy is visually present in selected terminal frame 12; selected frame 11 faces a close wall without a visible enemy. Intermediate image bytes are missing, so the time health reached 0, threat onset, and damage cause are unknown.",
        "limits": [
            "posthoc single-run reconstruction, not a prospective allocation",
            "health labels and visual scene descriptions are manual transcriptions of selected frames",
            "capture clocks establish endpoint timing only; absent intermediate PNG bytes prevent health-ROI re-evaluation",
            "no causal attribution to model latency, action choice, threat, or damage source",
            "no safe reaction, recovery, physical input, or MAP01 success established"
        ]
    }


def main():
    pins, report, events, manifest, failure = read_inputs()
    result = analyze(report, events, manifest, failure)
    result["input_sha256"] = pins["inputs"]
    (HERE / "TERMINAL_WINDOW_RESULT.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"disposition": result["disposition"], "timing_ms": result["timing_ms"], "health": result["observed_health_labels_manual"]}, separators=(",", ":")))


if __name__ == "__main__":
    main()
