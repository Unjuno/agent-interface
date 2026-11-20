"""Replay retained paired V39 HUD observations through exact frozen main."""
import hashlib
import json
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = Path(__file__).resolve().parent
RUN = ROOT / "research/doom/results/map01-v39-coast-liveness-live-01"
sys.path.insert(0, str(ROOT / "research/doom"))
sys.path.insert(0, str(ROOT / "research/live_control"))
import map01_overlap_controller_v39 as controller


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class RetainedSignalReader:
    def __init__(self, signal_id):
        self.signal_id = signal_id

    def read(self, observation):
        return observation["signals"][self.signal_id]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=PACKAGE / "RESULT.json")
    args = parser.parse_args()
    freeze = json.loads((PACKAGE / "FREEZE.json").read_text(encoding="utf-8"))
    event_path = RUN / "runtime/events.jsonl"
    report_path = RUN / "report.json"
    if sha256(event_path) != freeze["events_sha256"]:
        raise SystemExit("STOP: retained event stream hash mismatch")
    expected_blob = freeze["controller_blob"]
    import subprocess
    blob = subprocess.check_output(
        ["git", "rev-parse", f"{freeze['main_commit']}:{freeze['controller_path']}"],
        cwd=ROOT, text=True).strip()
    source_path = ROOT / freeze["controller_path"]
    if blob != expected_blob or sha256(source_path) != freeze["controller_sha256"]:
        raise SystemExit("STOP: current-main controller identity mismatch")
    if sha256(report_path) != freeze["report_sha256"]:
        raise SystemExit("STOP: retained report hash mismatch")
    for name, digest in freeze["png_sha256"].items():
        if sha256(RUN / "runtime" / name) != digest:
            raise SystemExit(f"STOP: {name} hash mismatch")

    rows = [json.loads(line) for line in event_path.read_text(encoding="utf-8").splitlines()
            if line.strip()]
    typed = [row for row in rows if row.get("event") == "typed_observation"
             and 166 <= row.get("sequence", -1) <= 218
             and (row.get("sequence") == 166 or row.get("id") == "cover-5")]
    source_rows = [row for row in typed if row["sequence"] == 166]
    if len(source_rows) != 1:
        raise SystemExit("STOP: expected exactly one source observation")
    source = source_rows[0]
    monitor, admission = controller.build_cover_monitor(
        RetainedSignalReader("health"), source, freeze["authored_validity"], 5,
        ammo_reader=RetainedSignalReader("ammo"), requires_ammo=True)
    if admission["effective"]["hard_minimum"] != 51:
        raise SystemExit("STOP: unexpected derived health floor")

    outcomes = []
    for row in typed:
        if row["sequence"] == 166:
            continue
        invalidation = monitor.observe(row)
        outcomes.append({
            "sequence": row["sequence"],
            "capture_ns": row["capture_ns"],
            "health": row["signals"]["health"].get("value"),
            "ammo": row["signals"]["ammo"].get("value"),
            "invalidation": None if invalidation is None else {
                "reason": invalidation["reason"],
                "requires_new_decision": invalidation["requires_new_decision"],
                "grants_input_authority": invalidation["grants_input_authority"],
            },
            "frame_rgb_sha256": row.get("frame_rgb_sha256"),
        })
    if len(typed) != 53:
        raise SystemExit(f"STOP: expected source plus 52 typed rows, got {len(typed)}")

    report = json.loads(report_path.read_text(encoding="utf-8"))
    decision = report["decisions"][5]
    started = decision["controller_model_started_ns"]
    result = {
        "classification": freeze["classification"],
        "source_commit": freeze["main_commit"],
        "controller_blob": blob,
        "source_blob": blob,
        "controller_sha256": sha256(source_path),
        "events_sha256": sha256(event_path),
        "report_sha256": sha256(report_path),
        "input_row_count_including_source": len(typed),
        "source": {
            "sequence": 166, "capture_ns": source["capture_ns"],
            "health": source["signals"]["health"]["value"],
            "ammo": source["signals"]["ammo"]["value"],
            "health_floor": admission["effective"]["hard_minimum"],
        },
        "model_started_ns": started,
        "sequence_200": next(row for row in outcomes if row["sequence"] == 200),
        "first_invalidation": next((row for row in outcomes
                                    if row["invalidation"] is not None), None),
        "model_terminal": {
            "status": decision["planner_turn_status"],
            "answer_eligible": decision["planner_answer_eligible"],
            "terminal_observed_ns": decision["planner_terminal_observed_ns"],
        },
        "timing_ms": {
            "model_start_to_sequence_200_capture": round(
                (next(row for row in outcomes if row["sequence"] == 200)["capture_ns"] - started) / 1e6, 6),
            "sequence_200_to_218_capture": round(
                (next(row for row in outcomes if row["sequence"] == 218)["capture_ns"] -
                 next(row for row in outcomes if row["sequence"] == 200)["capture_ns"]) / 1e6, 6),
            "sequence_218_capture_to_planner_terminal": round(
                (decision["planner_terminal_observed_ns"] -
                 next(row for row in outcomes if row["sequence"] == 218)["capture_ns"]) / 1e6, 6),
        },
        "timing_ms": {
            "model_start_to_sequence_200_capture": round(
                (next(row for row in outcomes if row["sequence"] == 200)["capture_ns"] - started) / 1e6, 6),
            "sequence_200_to_218_capture": round(
                (next(row for row in outcomes if row["sequence"] == 218)["capture_ns"] -
                 next(row for row in outcomes if row["sequence"] == 200)["capture_ns"]) / 1e6, 6),
            "sequence_218_capture_to_planner_terminal": round(
                (decision["planner_terminal_observed_ns"] -
                 next(row for row in outcomes if row["sequence"] == 218)["capture_ns"]) / 1e6, 6),
        },
        "counts": {
            "processed_after_source": len(outcomes),
            "no_invalidation_before_first": sum(
                row["invalidation"] is None for row in outcomes
                if row["sequence"] < 218),
        },
        "scope": "Historical-input replay through frozen main only; no live game, model, GUI, OS input, or efficacy claim.",
    }
    output = args.output if args.output.is_absolute() else ROOT / args.output
    if output.exists():
        raise SystemExit("STOP: refusing to overwrite retained result")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in (
        "input_row_count_including_source", "source", "sequence_200",
        "first_invalidation", "model_terminal", "counts")}, indent=2))


if __name__ == "__main__":
    main()
