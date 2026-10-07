#!/usr/bin/env python3
"""Reconstruct freshness and identity of candidate health-trigger rows."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCES = {
    "v38_events": ("research/doom/results/map01-v38-integrated-threat-live-01/runtime/events.jsonl", "80b964c9ab7d86fbd0b2bc56957157e018e9dbb90457f286995a2e6036192bc3"),
    "v38_report": ("research/doom/results/map01-v38-integrated-threat-live-01/report.json", "7fa222f9b273ee10ad1ed3e24b8f7f234f46cc137265a90d70c6073981602f58"),
    "v39_events": ("research/doom/results/map01-v39-coast-liveness-live-01/runtime/events.jsonl", "2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381"),
    "v39_report": ("research/doom/results/map01-v39-coast-liveness-live-01/report.json", "719db21040b843c5c91c5ff1f3d9fb2051ae1f1e008971547f39f015b4337687"),
}


def load_events(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def ms(delta_ns):
    return round(delta_ns / 1_000_000, 3)


def image_name(path):
    return str(path).replace("\\", "/").rsplit("/", 1)[-1]


def row_summary(event):
    return {
        "sequence": event["sequence"],
        "id": event["id"],
        "health": event["signals"]["health"]["value"],
        "capture_ns": event["capture_ns"],
        "emit_ns": event["emit_ns"],
    }


def reconstruct_v38_censoring(report, events):
    """Derive the retained d2 censor boundary and adjacent typed-health rows."""
    decision = next(item for item in report["decisions"] if item["iteration"] == 2)
    terminal_ns = decision["planner_terminal_observed_ns"]
    admission = decision["final_action_admission"]
    assert admission["planner_terminal"]["terminal_observed_ns"] == terminal_ns
    assert decision["planner_turn_status"] == "interrupted"
    source_name = image_name(decision["source_image"])

    typed = sorted(
        (event for event in events if event.get("event") == "typed_observation"),
        key=lambda event: event["sequence"],
    )
    exact = [event for event in events if event.get("event") == "observation"]
    source_exact = [event for event in exact if image_name(event.get("image", "")) == source_name]
    assert len(source_exact) == 1
    source_sequence = source_exact[0]["sequence"]
    source_typed = next(event for event in typed if event["sequence"] == source_sequence)
    assert source_typed["id"] == source_exact[0]["id"]
    assert source_typed["capture_ns"] == source_exact[0]["capture_ns"]
    assert source_typed["frame_rgb_sha256"] == source_exact[0]["frame_rgb_sha256"]
    assert all(left["capture_ns"] <= right["capture_ns"] for left, right in zip(typed, typed[1:]))
    assert all(event["capture_ns"] <= event["emit_ns"] for event in typed)
    baseline = source_typed["signals"]["health"]["value"]

    start_ns = decision["controller_model_started_ns"]
    below_baseline = [
        event for event in typed
        if start_ns <= event["capture_ns"]
        and event["emit_ns"] < terminal_ns
        and event["signals"]["health"]["value"] < baseline
    ]
    assert below_baseline
    trigger = max(below_baseline, key=lambda event: event["emit_ns"])
    following = next(event for event in typed if event["sequence"] > trigger["sequence"])
    next_after_terminal = following["capture_ns"] > terminal_ns
    one_sample = len(below_baseline) == 1
    return {
        "decision_iteration": decision["iteration"],
        "source_sequence": source_sequence,
        "baseline_health": baseline,
        "planner_terminal_ns": terminal_ns,
        "preterminal_below_baseline_count": len(below_baseline),
        "selected_rows": [row_summary(source_typed), row_summary(trigger), row_summary(following)],
        "trigger_emit_to_terminal_ms": ms(terminal_ns - trigger["emit_ns"]),
        "next_row_capture_after_terminal": next_after_terminal,
        "single_below_baseline_health_row": one_sample,
        "censoring_disposition": (
            "SINGLE_SAMPLE_BEFORE_TERMINAL_NEXT_AFTER"
            if one_sample and next_after_terminal
            else "OTHER"
        ),
    }


def write_json_lf(path, value):
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def main():
    inputs = {}
    for name, (relative, expected) in SOURCES.items():
        path = ROOT / relative
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise SystemExit(f"source hash mismatch: {name}: {actual}")
        inputs[name] = {"path": relative, "sha256": actual}
    events = load_events(ROOT / SOURCES["v39_events"][0])
    by_sequence = {}
    for event in events:
        if event.get("event") in {"typed_observation", "observation"}:
            by_sequence.setdefault(event.get("sequence"), {})[event["event"]] = event
    pairs = []
    for name, sequences in (("d2", (81, 82)), ("d3", (103, 104))):
        rows = []
        for sequence in sequences:
            typed = by_sequence[sequence]["typed_observation"]
            exact = by_sequence[sequence]["observation"]
            assert typed["id"] == exact["id"]
            assert typed["capture_ns"] == exact["capture_ns"]
            assert typed["frame_rgb_sha256"] == exact["frame_rgb_sha256"]
            assert typed["signals"]["health"]["sequence"] == sequence
            rows.append({"sequence": sequence, "id": typed["id"], "health": typed["signals"]["health"]["value"], "capture_ns": typed["capture_ns"], "emit_ns": typed["emit_ns"], "frame_rgb_sha256": typed["frame_rgb_sha256"], "observation_exact_match": True})
        assert rows[0]["id"] == f"cover-{name[-1]}"
        assert rows[0]["frame_rgb_sha256"] != rows[1]["frame_rgb_sha256"]
        assert rows[0]["capture_ns"] < rows[1]["capture_ns"]
        assert rows[0]["emit_ns"] < rows[1]["emit_ns"]
        pairs.append({"decision": name, "rows": rows, "capture_spacing_ms": ms(rows[1]["capture_ns"] - rows[0]["capture_ns"]), "emit_spacing_ms": ms(rows[1]["emit_ns"] - rows[0]["emit_ns"]), "capture_to_emit_ms": [ms(row["emit_ns"] - row["capture_ns"]) for row in rows], "distinct_frame_hashes": True})
    v38report = json.loads((ROOT / SOURCES["v38_report"][0]).read_text(encoding="utf-8"))
    v38events = load_events(ROOT / SOURCES["v38_events"][0])
    v38result = reconstruct_v38_censoring(v38report, v38events)
    result = {"status": "PASS_SCOPED", "method": "posthoc raw-trace identity reconstruction", "inputs": inputs, "v39_candidate_pairs": pairs, "v38_censoring_context": v38result, "scope": "Distinct sequence-matched captures with exact observation identity; not independent semantic evidence."}
    out = Path(__file__).with_name("RESULT.json")
    write_json_lf(out, result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
