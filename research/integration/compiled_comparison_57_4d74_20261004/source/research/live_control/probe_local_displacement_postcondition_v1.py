"""Probe target-relative displacement on retained exact X11 frames."""
import json
from pathlib import Path

import numpy as np
from PIL import Image

from local_displacement_postcondition_v1 import LocalDisplacementPostcondition, validate


HERE = Path(__file__).resolve().parent


def image(path):
    with Image.open(path) as opened:
        return np.asarray(opened.convert("RGB"))


def spec(sequence, box, target):
    return {
        "op": "local_displacement_postcondition",
        "postcondition_id": "rectangle-target",
        "source_sequence": sequence,
        "box": box,
        "target_delta": target,
        "tolerance_px": 1,
        "required_samples": 2,
        "sample_interval_ms": 50,
        "timeout_ms": 500,
        "on_unmet": "needs_decision",
    }


def evaluate(root, source_name, sample_names, source_sequence, sample_sequences, box, target):
    condition = LocalDisplacementPostcondition(
        spec(source_sequence, box, target), image(root / source_name), source_sequence, "inkscape-window")
    return condition.evaluate([image(root / name) for name in sample_names], sample_sequences,
                              ["inkscape-window"] * 2, [1_000_000_000, 1_050_000_000])


def refused(call):
    try:
        call()
    except (TypeError, ValueError):
        return True
    return False


def main():
    partial_root = HERE / "results/local-visual-barrier-x11-03/met"
    box = [592, 369, 56, 44]
    partial = evaluate(partial_root, "001.png", ["003.png", "004.png"],
                       1, [3, 4], box, [24, 0])
    assert partial["reason"] in ("lost", "target_not_reached")
    assert partial["continue_program"] is False
    partial_as_twelve = evaluate(partial_root, "001.png", ["003.png", "004.png"],
                                 1, [3, 4], box, [12, 1])
    assert partial_as_twelve["reason"] == "lost"

    successes = []
    for offset in (0, 40):
        root = HERE / f"results/patch-servo-03/{offset}"
        result = json.loads((root / "result.json").read_text())
        tracking = result["controller"][-1]["tracking"]
        source_sequence = tracking["source_observation"]
        rows = [json.loads(line) for line in (root / "events.jsonl").read_text().splitlines()]
        by_sequence = {row["sequence"]: row for row in rows if row.get("event") == "observation"}
        final_sequence = tracking["observation"]
        outcome = evaluate(
            root, Path(by_sequence[source_sequence]["image"]).name,
            [Path(by_sequence[final_sequence]["image"]).name,
             Path(by_sequence[final_sequence + 1]["image"]).name],
            source_sequence, [final_sequence, final_sequence + 1],
            result["source_box"], [24, 0])
        assert outcome["reason"] == "met"
        successes.append({"setup_offset": offset, "outcome": outcome})

    source = image(partial_root / "001.png")
    baseline = spec(1, box, [24, 0])
    condition = LocalDisplacementPostcondition(baseline, source, 1, "inkscape-window")
    changed_binding = condition.evaluate(
        [image(partial_root / "003.png"), image(partial_root / "004.png")], [3, 4],
        ["inkscape-window", "other-window"], [2_000_000_000, 2_050_000_000])
    assert changed_binding["reason"] == "binding_changed"
    malformed = {
        "extra_field": refused(lambda: validate({**baseline, "success": True}, source.shape, 1)),
        "empty_id": refused(lambda: validate({**baseline, "postcondition_id": ""}, source.shape, 1)),
        "stale_sequence": refused(lambda: validate(baseline, source.shape, 2)),
        "outside_box": refused(lambda: validate({**baseline, "box": [-1, 0, 10, 10]}, source.shape, 1)),
        "target_outside_radius": refused(lambda: validate({**baseline, "target_delta": [33, 0]}, source.shape, 1)),
        "large_tolerance": refused(lambda: validate({**baseline, "tolerance_px": 4}, source.shape, 1)),
        "one_sample": refused(lambda: validate({**baseline, "required_samples": 1}, source.shape, 1)),
        "continue_on_unmet": refused(lambda: validate({**baseline, "on_unmet": "continue"}, source.shape, 1)),
    }
    assert all(malformed.values())
    report = {
        "passed": True,
        "partial_24px_request": partial,
        "same_frames_12px_target_control": partial_as_twelve,
        "archived_exact_24px_successes": successes,
        "binding_change_control": changed_binding,
        "malformed_controls": malformed,
        "decision": "ADVANCE_TO_FRESH_X11_MET_AND_PARTIAL_CONTINUATION_PROBE;_NO_MODEL_OR_BENCHMARK_USE",
        "scope": "retained exact Inkscape frames; task-relative displacement only; no fresh input, model, cross-domain, speed or token claim",
    }
    destination = HERE / "results/local-displacement-postcondition-v1-probe.json"
    destination.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
