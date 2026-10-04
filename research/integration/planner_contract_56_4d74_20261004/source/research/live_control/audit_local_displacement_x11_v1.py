"""Audit retained and fresh task-relative displacement postconditions."""
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

from audit_local_visual_barrier_v1 import Decoder, Frame, red_bbox


HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def audit_case(directory):
    rows = [json.loads(line) for line in (directory / "events.jsonl").read_text().splitlines()]
    observations = [row for row in rows if row.get("event") == "observation"]
    decoder = Decoder("live-control")
    boxes = []
    for index, observation in enumerate(observations, 1):
        frame = decoder.accept((directory / f"{index:03d}.ait").read_bytes())
        with Image.open(directory / Path(observation["image"]).name) as opened:
            image = opened.convert("RGB")
        assert frame == Frame(image.width, image.height, image.mode, image.tobytes())
        boxes.append(list(red_bbox(image)))
    terminal = next(row for row in rows if row.get("event") == "terminal")
    outcome = next(row for row in rows if row.get("event") == "local_displacement_postcondition")
    started = [row["step"] for row in rows if row.get("event") == "step_started"]
    rectangle = ET.parse(directory / "shape.svg").getroot().find("{http://www.w3.org/2000/svg}rect")
    return {
        "exact_frames": len(boxes), "initial_bbox": boxes[0], "final_bbox": boxes[-1],
        "delta": [boxes[-1][0] - boxes[0][0], boxes[-1][1] - boxes[0][1]],
        "terminal": terminal, "outcome": outcome, "steps_started": started,
        "saved_x": float(rectangle.get("x")),
    }


def main():
    archived = read(HERE / "results/local-displacement-postcondition-v1-probe.json")
    assert archived["passed"] is True
    assert archived["partial_24px_request"]["continue_program"] is False
    assert len(archived["archived_exact_24px_successes"]) == 2
    assert all(row["outcome"]["reason"] == "met"
               for row in archived["archived_exact_24px_successes"])
    assert archived["binding_change_control"]["reason"] == "binding_changed"
    assert all(archived["malformed_controls"].values())

    first = HERE / "results/local-displacement-x11-01"
    first_report = read(first / "report.json")
    assert first_report["passed"] is False
    assert first_report["decision"] == "HOLD_DISPLACEMENT_POSTCONDITION;_PRESERVE_FAILURE"

    root = HERE / "results/local-displacement-x11-02"
    manifest = read(root / "manifest.json")
    for name, expected in manifest["sources"].items():
        assert sha(HERE / name) == expected, name
    report = read(root / "report.json")
    assert report["passed"] is True
    target = audit_case(root / "target")
    partial = audit_case(root / "partial")
    assert target["delta"] == [24, 0]
    assert target["outcome"]["reason"] == "met"
    assert target["outcome"]["tracking"][0]["delta"] == [24, 0]
    assert target["outcome"]["tracking"][1]["delta"] == [24, 0]
    assert 4 in target["steps_started"]
    assert abs((target["saved_x"] - 50) * 1.18 - 24) <= 1
    assert partial["delta"] == [20, 0]
    assert partial["outcome"]["reason"] == "target_not_reached"
    assert partial["outcome"]["tracking"][0]["delta"] == [20, 0]
    assert partial["outcome"]["tracking"][1]["delta"] == [20, 0]
    assert 4 not in partial["steps_started"]
    assert partial["saved_x"] == 50
    assert target["terminal"]["release"]["verified"] is True
    assert partial["terminal"]["release"]["verified"] is True
    audit = {
        "audit_passed": True,
        "archived": {"exact_24px_met": 2, "partial_stopped": True,
                     "binding_change_stopped": True},
        "first_fresh_allocation": {
            "passed": False, "target_observed_delta": [44, 0],
            "partial_observed_delta": [20, 0], "both_stopped": True,
            "reason": "input-to-screen displacement assumption and immediate decoration state were wrong",
        },
        "second_fresh_allocation": {
            "target_delta": target["delta"], "target_reason": target["outcome"]["reason"],
            "target_save_started": True, "target_saved_screen_delta_within_one_px": True,
            "partial_delta": partial["delta"], "partial_reason": partial["outcome"]["reason"],
            "partial_save_started": False,
            "exact_frames": target["exact_frames"] + partial["exact_frames"],
            "all_terminal_releases_verified": True,
            "sample_spans_ms": [target["outcome"]["sample_span_ms"],
                                partial["outcome"]["sample_span_ms"]],
        },
        "decision": report["decision"],
        "scope": "two retained exact-frame checks and one fresh scripted Inkscape met/partial pair after one retained failed pair; no model, cross-domain, speed, token or generalization claim",
        "audit_sha256": sha(Path(__file__)),
    }
    (root / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
