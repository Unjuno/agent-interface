"""Audit archived calibration, Executor behavior and fresh X11 barrier evidence."""
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "observation_tiles"))
from tile_transport import Decoder, Frame


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def events(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines()]


def red_bbox(image):
    pixels = image.convert("RGB").load()
    candidates = []
    active = None
    for y in range(image.height):
        spans = []
        start = None
        for x in range(image.width + 1):
            red = x < image.width and pixels[x, y][0] > 180 and pixels[x, y][1] < 100 and pixels[x, y][2] < 100
            if red and start is None:
                start = x
            elif not red and start is not None:
                if x - start >= 24:
                    spans.append((start, x))
                start = None
        if spans:
            left, right = max(spans, key=lambda span: span[1] - span[0])
            if active is not None and left < active[2] and right > active[0]:
                active = (min(left, active[0]), active[1], max(right, active[2]), y + 1)
            else:
                if active is not None:
                    candidates.append(active)
                active = (left, y, right, y + 1)
        elif active is not None:
            candidates.append(active)
            active = None
    if active is not None:
        candidates.append(active)
    return max(candidates, key=lambda box: (box[2] - box[0]) * (box[3] - box[1]))


def audit_frames(directory):
    rows = events(directory / "events.jsonl")
    observations = [row for row in rows if row.get("event") == "observation"]
    decoder = Decoder("live-control")
    boxes = []
    for index, observation in enumerate(observations, 1):
        frame = decoder.accept((directory / f"{index:03d}.ait").read_bytes())
        with Image.open(directory / Path(observation["image"]).name) as opened:
            image = opened.convert("RGB")
        assert frame == Frame(image.width, image.height, image.mode, image.tobytes())
        boxes.append(list(red_bbox(image)))
    return rows, boxes


def main():
    calibration = read(HERE / "results/local-visual-barrier-v1-probe.json")
    program = read(HERE / "results/local-visual-barrier-program-v1-probe.json")
    assert calibration["passed"] is True
    assert calibration["archived_selected_first_effects_met"] == 9
    assert calibration["archived_selected_repeat_drags_unmet"] == 2
    assert all(calibration[name]["needs_decision"] is True
               for name in ("transient_control", "binding_control", "timeout_control"))
    assert all(calibration["malformed_controls"].values())
    assert program["passed"] is True
    assert program["met"]["executed"] == ["pointer_drag", "pointer_click"]
    assert program["unmet"]["executed"] == ["pointer_drag"]
    assert program["binding_changed"]["executed"] == ["pointer_drag"]
    assert all(program["pre_input_controls"].values())

    failed_before_input = read(HERE / "results/local-visual-barrier-x11-01/failure.json")
    false_accept = read(HERE / "results/local-visual-barrier-x11-02/failure.json")
    assert failed_before_input["input_issued"] is False
    assert false_accept["observed_red_bbox_delta_x"] == 12
    assert false_accept["later_save_step_started"] is True

    root = HERE / "results/local-visual-barrier-x11-03"
    manifest = read(root / "manifest.json")
    for name, expected in manifest["sources"].items():
        assert sha(HERE / name) == expected, name
    report = read(root / "report.json")
    assert report["passed"] is False
    assert report["decision"] == "REJECT_SINGLE_ROI_CHANGE_AS_CONTINUATION_BARRIER;_KEEP_ADVISORY_ONLY"
    met_events, met_boxes = audit_frames(root / "met")
    unmet_events, unmet_boxes = audit_frames(root / "unmet")
    met_barrier = next(row for row in met_events if row.get("event") == "local_visual_barrier")
    unmet_barrier = next(row for row in unmet_events if row.get("event") == "local_visual_barrier")
    met_terminal = next(row for row in met_events if row.get("event") == "terminal")
    unmet_terminal = next(row for row in unmet_events if row.get("event") == "terminal")
    assert met_boxes[0][0] == 596 and met_boxes[-1][0] == 608
    assert met_barrier["reason"] == "met" and met_barrier["persistent_changed_pixels"] == 163
    assert met_terminal["status"] == "completed" and met_terminal["release"]["verified"] is True
    assert any(row.get("event") == "step_started" and row.get("step") == 2 for row in met_events)
    assert unmet_barrier["reason"] == "unmet" and unmet_barrier["persistent_changed_pixels"] == 0
    assert unmet_terminal["status"] == "needs_decision" and unmet_terminal["release"]["verified"] is True
    assert not any(row.get("event") == "step_started" and row.get("step") == 2 for row in unmet_events)
    audit = {
        "audit_passed": True,
        "archived_calibration": {"selected_first_effects_met": 9, "selected_repeat_drags_unmet": 2},
        "executor_boundary": {"met_continued": True, "unmet_stopped": True,
                              "binding_change_stopped": True},
        "fresh_x11": {
            "met_barrier_pixels": 163, "requested_delta_x": 24,
            "independently_reconstructed_final_delta_x": met_boxes[-1][0] - met_boxes[0][0],
            "later_step_started": True, "unmet_later_step_started": False,
            "exact_frames": len(met_boxes) + len(unmet_boxes),
            "all_terminal_releases_verified": True,
        },
        "decision": report["decision"],
        "next_requirement": "task-relative postconditions such as target displacement or per-region target/guard structure; total changed pixels cannot admit continuation",
        "scope": "selected archived OpenTTD calibration plus two fresh scripted Inkscape X11 sessions; no model, semantic correctness, speed, token or generalization claim",
        "audit_sha256": sha(Path(__file__)),
    }
    (root / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
