"""Audit archived and fresh target/guard postcondition evidence."""
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
    outcomes = [row for row in rows if row.get("event") == "local_target_guard_postcondition"]
    started = [row["step"] for row in rows if row.get("event") == "step_started"]
    rectangle = ET.parse(directory / "shape.svg").getroot().find("{http://www.w3.org/2000/svg}rect")
    return {
        "exact_frames": len(boxes), "initial_bbox": boxes[0], "final_bbox": boxes[-1],
        "delta": [boxes[-1][0] - boxes[0][0], boxes[-1][1] - boxes[0][1]],
        "terminal": terminal, "outcomes": outcomes, "steps_started": started,
        "saved_x": float(rectangle.get("x")), "saved_y": float(rectangle.get("y")),
    }


def main():
    pure = __import__("probe_local_target_guard_postcondition_v1")
    assert pure is not None
    prereg_failure = read(HERE / "results/openttd-target-guard-archive-01/failure.json")
    assert prereg_failure["status"] == "preregistration_failed_before_heldout_pixel_read"
    assert prereg_failure["input_issued"] is False
    archived_failed = read(HERE / "results/openttd-target-guard-archive-02/report.json")
    assert archived_failed["passed"] is False
    failed = {row["name"]: row for row in archived_failed["cases"]}
    assert failed["v7-first-segment"]["outcome"]["measurements"][0]["target_changed_total"] == 12
    assert failed["v7-first-segment"]["outcome"]["measurements"][1]["target_changed_total"] == 169
    assert failed["v8-first-segment"]["outcome"]["measurements"][0]["guard_changed_total"] == 36
    assert failed["v8-first-segment"]["outcome"]["measurements"][1]["guard_changed_total"] == 0

    archived = HERE / "results/openttd-target-guard-archive-03"
    archived_plan = read(archived / "preregistration.json")
    for name, expected in archived_plan["sources"].items():
        assert sha(HERE / name) == expected, name
    archived_report = read(archived / "report.json")
    assert archived_report["passed"] is True
    assert [row["outcome"]["reason"] for row in archived_report["cases"]] == [
        "met", "target_not_reached", "target_not_reached", "met", "guard_changed", "met"]

    first = HERE / "results/local-target-guard-x11-01"
    first_report = read(first / "report.json")
    assert first_report["passed"] is False
    first_cases = {row["name"]: row for row in first_report["cases"]}
    assert first_cases["target"]["postcondition"] is None
    assert first_cases["target"]["owner_focus_release"] is True
    assert first_cases["target"]["terminal"]["release"]["verified"] is True
    assert first_cases["partial"]["postcondition"]["reason"] == "target_not_reached"
    assert first_cases["guard"]["postcondition"]["reason"] == "guard_changed"

    root = HERE / "results/local-target-guard-x11-02"
    plan = read(root / "preregistration.json")
    for name, expected in plan["sources"].items():
        assert sha(HERE / name) == expected, name
    report = read(root / "report.json")
    assert report["passed"] is True
    cases = {name: audit_case(root / name) for name in plan["order"]}
    target, partial, guard = cases["target"], cases["partial"], cases["guard"]
    assert target["delta"] == [24, 0] and target["outcomes"][0]["reason"] == "met"
    assert target["outcomes"][0]["measurements"][0]["target_changed_total"] == 84
    assert target["outcomes"][0]["measurements"][0]["guard_changed_total"] == 0
    assert 4 in target["steps_started"] and abs((target["saved_x"] - 50) * 1.18 - 24) <= 1
    assert partial["delta"] == [20, 0] and partial["outcomes"][0]["reason"] == "target_not_reached"
    assert partial["outcomes"][0]["measurements"][0]["target_changed_total"] == 0
    assert 4 not in partial["steps_started"] and partial["saved_x"] == 50
    assert guard["delta"] == [0, -20] and guard["outcomes"][0]["reason"] == "guard_changed"
    assert guard["outcomes"][0]["measurements"][0]["guard_changed_total"] == 450
    assert 4 not in guard["steps_started"] and guard["saved_y"] == 50
    assert all(case["terminal"]["release"]["verified"] is True for case in cases.values())
    source_sha = sha(root / "target/001.png")
    assert all(sha(root / f"{name}/001.png") == source_sha for name in plan["order"])
    audit = {
        "audit_passed": True,
        "retained_failures": {"missing_preregistration_frame": True,
                              "pre_settle_false_stops": 2,
                              "fresh_target_focus_interruption": True},
        "archived_settle_aligned": {"cases": 6, "expected_reasons": 6,
                                    "first_effects_met": 3, "repeats_stopped": 2,
                                    "guard_change_stopped": 1},
        "fresh_x11": {"cases": 3, "target_delta": target["delta"],
                      "target_changed_pixels": 84, "target_save_started": True,
                      "partial_delta": partial["delta"], "partial_save_started": False,
                      "guard_delta": guard["delta"], "guard_changed_pixels": 450,
                      "guard_save_started": False,
                      "sample_spans_ms": [cases[name]["outcomes"][0]["sample_span_ms"]
                                          for name in plan["order"]],
                      "exact_frames": sum(case["exact_frames"] for case in cases.values()),
                      "all_terminal_releases_verified": True,
                      "fresh_initial_sources_identical": True,
                      "fresh_initial_source_sha256": source_sha},
        "decision": "RETAIN_TARGET_GUARD_OPERATOR;_TRANSFER_ONLY_WITH_FRESH_OPENTTD_SETTLE_AND_INDEPENDENT_SCORE",
        "scope": "six settle-aligned archived OpenTTD visual checks and one fresh scripted Inkscape three-way integration after retained failures; boxes are human-authored; no fresh OpenTTD input, model authorship, semantic success, speed, token or generalization claim",
        "audit_sha256": sha(Path(__file__)),
    }
    (root / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
