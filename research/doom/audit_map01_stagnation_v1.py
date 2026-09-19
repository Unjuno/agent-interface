"""Freeze calibration of the conservative revisit detector on the failed 30-turn run."""
import json
from pathlib import Path

from map01_stagnation_v1 import descriptor, find_revisit

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
RAW = HERE / "results/map01-stagnation-v1-calibration"
OUT = HERE / "results/map01-stagnation-v1-audit.json"
EXPECTED = [5, 6, 7, 9, 10, 11, 15, 17, 23, 24, 29]


def main() -> None:
    manifest = json.loads((RAW / "manifest.json").read_text())
    history = []
    detections = []
    for row in manifest["frames"]:
        current = descriptor(RAW / "frames" / row["file"])
        revisit = find_revisit(current, history)
        if revisit:
            detections.append({"iteration": row["iteration"], **revisit})
        history.append(current)
    observed = [row["iteration"] for row in detections]
    assert observed == EXPECTED, (observed, EXPECTED)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "status": "passed",
        "source_run": "map01-motor-reflex-live-01",
        "source_outcome": "unfinished after 30 decisions",
        "calibration_scope": "one retained failure; threshold is a candidate, not general validation",
        "viewport": [320, 162, 962, 610],
        "descriptor_size": [64, 45],
        "threshold_normalized_mae_lte": 0.065,
        "excluded_adjacent_frames": True,
        "history_decisions": 8,
        "expected_and_observed_iterations": EXPECTED,
        "detections": detections,
    }, indent=2) + "\n")
    print(OUT)


if __name__ == "__main__":
    main()
