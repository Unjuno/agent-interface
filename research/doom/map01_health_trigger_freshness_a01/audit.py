#!/usr/bin/env python3
"""Independent verification of analyze.py's retained-trace result."""
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]


def read_jsonl(path):
    with path.open(encoding="utf-8") as handle:
        return list(map(json.loads, filter(str.strip, handle)))


def image_name(path):
    return str(path).replace("\\", "/").rsplit("/", 1)[-1]


def summarize(event):
    return {
        "sequence": event["sequence"],
        "id": event["id"],
        "health": event["signals"]["health"]["value"],
        "capture_ns": event["capture_ns"],
        "emit_ns": event["emit_ns"],
    }


def reconstruct_v38_context(report, events):
    decision = next(row for row in report["decisions"] if row["iteration"] == 2)
    terminal = decision["final_action_admission"]["planner_terminal"]["terminal_observed_ns"]
    assert terminal == decision["planner_terminal_observed_ns"]
    source = image_name(decision["source_image"])
    observations = [row for row in events if row.get("event") == "observation"]
    source_observation = next(row for row in observations if image_name(row.get("image", "")) == source)
    typed = sorted((row for row in events if row.get("event") == "typed_observation"), key=lambda row: row["sequence"])
    baseline_row = next(row for row in typed if row["sequence"] == source_observation["sequence"])
    assert baseline_row["id"] == source_observation["id"]
    assert baseline_row["capture_ns"] == source_observation["capture_ns"]
    assert baseline_row["frame_rgb_sha256"] == source_observation["frame_rgb_sha256"]
    assert all(first["capture_ns"] <= second["capture_ns"] for first, second in zip(typed, typed[1:]))
    assert all(row["capture_ns"] <= row["emit_ns"] for row in typed)
    baseline = baseline_row["signals"]["health"]["value"]
    start = decision["controller_model_started_ns"]
    qualifying = [row for row in typed if start <= row["capture_ns"] and row["emit_ns"] < terminal and row["signals"]["health"]["value"] < baseline]
    trigger = max(qualifying, key=lambda row: row["emit_ns"])
    following = next(row for row in typed if row["sequence"] > trigger["sequence"])
    next_after_terminal = following["capture_ns"] > terminal
    one_sample = len(qualifying) == 1
    return {
        "decision_iteration": decision["iteration"],
        "source_sequence": baseline_row["sequence"],
        "baseline_health": baseline,
        "planner_terminal_ns": terminal,
        "preterminal_below_baseline_count": len(qualifying),
        "selected_rows": [summarize(baseline_row), summarize(trigger), summarize(following)],
        "trigger_emit_to_terminal_ms": round((terminal - trigger["emit_ns"]) / 1_000_000, 3),
        "next_row_capture_after_terminal": next_after_terminal,
        "single_below_baseline_health_row": one_sample,
        "censoring_disposition": "SINGLE_SAMPLE_BEFORE_TERMINAL_NEXT_AFTER" if one_sample and next_after_terminal else "OTHER",
    }


def main():
    result = json.loads((BASE / "RESULT.json").read_text(encoding="utf-8"))
    freeze = json.loads((BASE / "FREEZE.json").read_text(encoding="utf-8"))
    assert result["status"] == "PASS_SCOPED"
    assert len(result["v39_candidate_pairs"]) == 2
    all_ok = True
    for pair in result["v39_candidate_pairs"]:
        rows = pair["rows"]
        assert len(rows) == 2
        assert pair["distinct_frame_hashes"] is True
        assert rows[0]["frame_rgb_sha256"] != rows[1]["frame_rgb_sha256"]
        assert rows[0]["observation_exact_match"] and rows[1]["observation_exact_match"]
        assert rows[0]["capture_ns"] < rows[1]["capture_ns"]
        assert rows[0]["emit_ns"] < rows[1]["emit_ns"]
        for row in rows:
            assert row["emit_ns"] >= row["capture_ns"]
    for name, item in result["inputs"].items():
        source = ROOT / item["path"]
        assert freeze["source_sha256"][name] == item["sha256"], name
        assert hashlib.sha256(source.read_bytes()).hexdigest() == item["sha256"], name
    events = read_jsonl(ROOT / result["inputs"]["v39_events"]["path"])
    indexed = {(e.get("event"), e.get("sequence")): e for e in events if e.get("event") in ("typed_observation", "observation")}
    for pair in result["v39_candidate_pairs"]:
        for row in pair["rows"]:
            typed = indexed[("typed_observation", row["sequence"])]
            observed = indexed[("observation", row["sequence"])]
            assert typed["id"] == observed["id"] == row["id"]
            assert typed["capture_ns"] == observed["capture_ns"] == row["capture_ns"]
            assert typed["frame_rgb_sha256"] == observed["frame_rgb_sha256"] == row["frame_rgb_sha256"]
            assert typed["signals"]["health"]["value"] == row["health"]
    v38report = json.loads((ROOT / result["inputs"]["v38_report"]["path"]).read_text(encoding="utf-8"))
    v38events = read_jsonl(ROOT / result["inputs"]["v38_events"]["path"])
    reconstructed = reconstruct_v38_context(v38report, v38events)
    recorded = result["v38_censoring_context"]
    for key, value in reconstructed.items():
        assert recorded[key] == value, key
    assert recorded["next_row_capture_after_terminal"] is True
    assert recorded["single_below_baseline_health_row"] is True
    audit = {"status": "PASS_SCOPED", "independent_checks": ["source hashes match freeze", "monotonic capture and emission", "different frame hashes within each candidate pair", "typed/exact same-sequence capture identity", "health value and sequence preservation", "v38 d2 source baseline, terminal boundary, qualifying-row count, and censor relation independently recomputed"], "v38_censoring_reconstruction": reconstructed, "semantic_independence_proven": False, "all_checks_passed": all_ok}
    with (BASE / "AUDIT.json").open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(audit, stream, indent=2)
        stream.write("\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
