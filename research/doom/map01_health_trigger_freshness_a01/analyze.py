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
    v38 = load_events(ROOT / SOURCES["v38_events"][0])
    v38typed = {e.get("sequence"): e for e in v38 if e.get("event") == "typed_observation"}
    v38rows = []
    for sequence in (91, 100, 101):
        row = v38typed.get(sequence)
        if row:
            v38rows.append({"sequence": sequence, "id": row["id"], "health": row["signals"]["health"]["value"], "capture_ns": row["capture_ns"], "emit_ns": row["emit_ns"]})
    terminals = [e for e in v38 if e.get("event") in {"run_terminal", "planner_terminal", "terminal"}]
    v38result = {"selected_rows": v38rows, "planner_terminal_ns": 54894834592186, "next_row_after_terminal": v38rows[-1]["capture_ns"] > 54894834592186, "single_below_baseline_health_row": v38rows[1]["health"] == 79 and v38rows[0]["health"] == 85, "note": "The single qualifying health sample is 119.635 ms before planner terminal; next selected sample is after terminal. Retained only as censoring context; not replayed or treated as a matched control."}
    result = {"status": "PASS_SCOPED", "method": "posthoc raw-trace identity reconstruction", "inputs": inputs, "v39_candidate_pairs": pairs, "v38_censoring_context": v38result, "scope": "Distinct sequence-matched captures with exact observation identity; not independent semantic evidence."}
    out = Path(__file__).with_name("RESULT.json")
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
