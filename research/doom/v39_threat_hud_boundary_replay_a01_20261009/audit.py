"""Independent raw-event audit for the retained-input current-main replay."""
import hashlib
import json
from pathlib import Path
import argparse
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RUN = ROOT / "research/doom/results/map01-v39-coast-liveness-live-01"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, default=HERE / "RESULT.json")
    parser.add_argument("--output", type=Path, default=HERE / "AUDIT.json")
    args = parser.parse_args()
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    result = json.loads(args.result.read_text(encoding="utf-8"))
    events_path = RUN / "runtime/events.jsonl"
    report_path = RUN / "report.json"
    source_path = ROOT / freeze["controller_path"]
    blob = subprocess.check_output(
        ["git", "rev-parse", f"{freeze['main_commit']}:{freeze['controller_path']}"],
        cwd=ROOT, text=True).strip()
    assert blob == freeze["controller_blob"]
    assert sha(source_path) == freeze["controller_sha256"]
    assert sha(events_path) == freeze["events_sha256"] == result["events_sha256"]
    assert sha(report_path) == freeze["report_sha256"] == result["report_sha256"]
    rows = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()
            if line.strip()]
    typed = [r for r in rows if r.get("event") == "typed_observation"
             and 166 <= r.get("sequence", -1) <= 218
             and (r.get("sequence") == 166 or r.get("id") == "cover-5")]
    assert [r["sequence"] for r in typed] == list(range(166, 219))
    for previous, current in zip(typed, typed[1:]):
        assert current["capture_ns"] > previous["capture_ns"]
        assert current["pointer_binding"] == previous["pointer_binding"]
        for signal_id in ("health", "ammo"):
            signal = current["signals"][signal_id]
            assert signal["sequence"] == current["sequence"]
            assert signal["capture_ns"] == current["capture_ns"]
            assert signal["binding"] == current["pointer_binding"]
    source = typed[0]
    assert (source["signals"]["health"]["value"],
            source["signals"]["ammo"]["value"]) == (61, 40)
    assert result["source"]["health_floor"] == max(30, 61 - 10) == 51
    floor_crossings = [r for r in typed[1:] if
                       r["signals"]["health"]["value"] < 51 or
                       r["signals"]["ammo"]["value"] < 1]
    assert floor_crossings and floor_crossings[0]["sequence"] == 218
    boundary = next(r for r in typed if r["sequence"] == 200)
    trigger = floor_crossings[0]
    assert (boundary["signals"]["health"]["value"],
            boundary["signals"]["ammo"]["value"]) == (51, 38)
    assert result["sequence_200"]["invalidation"] is None
    assert result["first_invalidation"]["sequence"] == 218
    assert result["first_invalidation"]["health"] == trigger["signals"]["health"]["value"] == 48
    assert result["first_invalidation"]["invalidation"] == {
        "reason": "health:below_hard_minimum",
        "requires_new_decision": True,
        "grants_input_authority": False,
    }
    assert result["controller_blob"] == blob
    assert result["controller_sha256"] == sha(source_path)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    decision = report["decisions"][5]
    assert decision["planner_turn_status"] == "interrupted"
    assert decision["planner_answer_eligible"] is False
    assert result["timing_ms"]["sequence_200_to_218_capture"] == round(
        (trigger["capture_ns"] - boundary["capture_ns"]) / 1e6, 6)
    for name, digest in freeze["png_sha256"].items():
        assert sha(RUN / "runtime" / name) == digest
    audit = {
        "verdict": "PASS_RETAINED_TRACE_CURRENT_MAIN_GUARD_REPLAY",
        "source_plus_observations": len(typed),
        "post_source_observations": len(typed) - 1,
        "first_crossing_sequence": floor_crossings[0]["sequence"],
        "controller_blob": blob,
        "controller_sha256": sha(source_path),
        "sequence_200_to_218_ms": round(
            (trigger["capture_ns"] - boundary["capture_ns"]) / 1e6, 6),
        "model_start_to_sequence_200_ms": round(
            (boundary["capture_ns"] - decision["controller_model_started_ns"]) / 1e6, 6),
        "sequence_218_capture_to_planner_terminal_ms": round(
            (decision["planner_terminal_observed_ns"] - trigger["capture_ns"]) / 1e6, 6),
        "boundary_sequence_200_preserved": True,
        "trigger_sequence_218_requires_new_decision": True,
        "input_authority_granted": False,
        "source_and_image_hashes_match": True,
        "scope": "historical-input offline replay; no live efficacy or current V15 integration claim",
    }
    output = args.output
    if output.exists():
        raise SystemExit("STOP: refusing to overwrite audit")
    output.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
