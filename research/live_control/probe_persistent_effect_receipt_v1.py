"""Calibrate the visual receipt on retained new-effect and repeat-drag cases."""
import copy
import json
from pathlib import Path

from PIL import Image

from openttd_drag_effect_v1 import drag_box
from persistent_effect_receipt_v1 import build


HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def observation_image(applied):
    return Path(applied["result"]["state"]["continuation"]["observation"]["image"]).name


def effect(root, drag_turn, latest_turn):
    proposal = read(root / f"typed-{drag_turn}.json")
    drags = [step for step in proposal["steps"] if step.get("op") == "pointer_drag"]
    assert len(drags) == 1
    applied = read(root / f"applied-{drag_turn}.json")
    after = [row for row in applied["result"]["reply"]["records"]
             if row.get("event") == "observation"][-1]
    before = applied["fresh_observation"]
    with Image.open(root / "runtime" / Path(before["image"]).name) as opened:
        size = opened.size
    memory = {
        "source_turn": drag_turn,
        "before_image": Path(before["image"]).name,
        "after_image": Path(after["image"]).name,
        "before_sequence": before["sequence"],
        "after_sequence": after["sequence"],
        "crop_box": list(drag_box(drags[0], size)),
        "inspection_turns": latest_turn - drag_turn,
    }
    latest = observation_image(read(root / f"applied-{latest_turn}.json"))
    return build(memory, latest, root / "runtime"), memory, latest


def root(study):
    return RESULTS / f"timing-envelope-openttd-l-{study:02d}/fixed-astra"


def refused(call):
    try:
        call()
    except (ValueError, TypeError):
        return True
    return False


def main():
    positive_cases = [
        (6, 5, 6),
        (8, 5, 6),
        (9, 5, 6), (9, 7, 8),
        (10, 5, 6), (10, 7, 8),
        (11, 5, 6), (11, 5, 10), (11, 11, 12),
    ]
    limited_cases = [(6, 9, 10), (6, 11, 12)]
    positives = []
    for study, drag_turn, latest_turn in positive_cases:
        receipt, _, _ = effect(root(study), drag_turn, latest_turn)
        assert receipt["classification"] == "substantial_persistent_visual_change"
        assert receipt["semantic_authority"] == "none"
        assert receipt["permits_new_mutation"] is False
        positives.append({"study": study, "drag_turn": drag_turn,
                          "latest_turn": latest_turn, **receipt})
    limited = []
    for study, drag_turn, latest_turn in limited_cases:
        receipt, _, _ = effect(root(study), drag_turn, latest_turn)
        assert receipt["classification"] == "limited_or_transient_visual_change"
        limited.append({"study": study, "drag_turn": drag_turn,
                        "latest_turn": latest_turn, **receipt})

    sample, memory, latest = effect(root(11), 5, 6)
    no_change = copy.deepcopy(memory)
    no_change["after_image"] = no_change["before_image"]
    receipt = build(no_change, no_change["before_image"], root(11) / "runtime")
    assert receipt["persistent_changed_pixels"] == 0
    assert receipt["classification"] == "limited_or_transient_visual_change"
    malformed = copy.deepcopy(memory)
    malformed["crop_box"] = [-1, 0, 10, 10]
    controls = {
        "extra_field": refused(lambda: build({**memory, "success": True}, latest, root(11) / "runtime")),
        "bad_crop": refused(lambda: build(malformed, latest, root(11) / "runtime")),
        "bad_threshold": refused(lambda: build(memory, latest, root(11) / "runtime", threshold=256)),
        "bad_substantial_threshold": refused(lambda: build(memory, latest, root(11) / "runtime", substantial_pixels=0)),
        "missing_image": refused(lambda: build(memory, "missing.png", root(11) / "runtime")),
    }
    assert all(controls.values())
    report = {
        "passed": True,
        "thresholds": {"rgb_difference": 20, "substantial_pixels": 1000},
        "substantial_new_effects": positives,
        "limited_repeat_drags": limited,
        "exact_no_change_pixels": receipt["persistent_changed_pixels"],
        "invalid_controls": controls,
        "decision": "RETAIN_AS_PLANNER_EVIDENCE_CANDIDATE;_NO_ACTION_AUTHORITY",
        "scope": "archived OpenTTD calibration only; labels selected from independent observer history; no live model, general effect, correctness, speed or token claim",
    }
    destination = RESULTS / "persistent-effect-receipt-v1-probe.json"
    destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
