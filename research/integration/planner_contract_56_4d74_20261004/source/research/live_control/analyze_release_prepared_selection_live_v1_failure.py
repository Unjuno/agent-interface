"""Classify the first prepared-selection allocation without rerunning it."""
import hashlib
import json
from pathlib import Path

from PIL import Image
from inkscape_red_target_planner_v1 import prepare
from inkscape_selection_scorer_v1 import score

HERE = Path(__file__).resolve().parent; REPO = HERE.parents[1]
ROOT = REPO / "results-local/live_control/release-prepared-selection-live-01"
PREREG = HERE / "release_prepared_selection_live_v1_prereg.json"
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))


def red_support(path, roi):
    with Image.open(path) as source:
        image = source.convert("RGB"); points = []
        for y in range(roi[1], roi[3]):
            for x in range(roi[0], roi[2]):
                color = image.getpixel((x, y))
                if color[0] >= 240 and color[1] <= 20 and color[2] <= 20:
                    points.append((x, y))
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    return {"red_pixels": len(points),
            "bbox": [min(xs), min(ys), max(xs) + 1, max(ys) + 1]}


def dark_sides(path, box, expansion=18):
    with Image.open(path) as source:
        image = source.convert("RGB"); left, top, right, bottom = box
        zones = {"left": [left-expansion, top-expansion, left, bottom+expansion],
                 "right": [right, top-expansion, right+expansion, bottom+expansion],
                 "top": [left, top-expansion, right, top],
                 "bottom": [left, bottom, right, bottom+expansion]}
        return {name: sum(1 for y in range(area[1], area[3])
                          for x in range(area[0], area[2])
                          if max(image.getpixel((x, y))) <= 50)
                for name, area in zones.items()}


def main():
    plan, report, events = read(PREREG), read(ROOT / "report.json"), read(ROOT / "events.json")
    source_plan = prepare(ROOT / "001.png", plan["planner_roi"])
    before = score(source_plan, ROOT / "003.png")
    error = None
    try: score(source_plan, ROOT / "004.png")
    except ValueError as exc: error = {"type": type(exc).__name__, "detail": str(exc)}
    selection_events = [row for row in events if row.get("id") == "prepared-red-selection-01"]
    terminal = next(row for row in selection_events if row.get("event") == "terminal")
    failure = {"allocation_passed": False,
        "failure_class": "selected_precondition_and_strict_overlay_identity_rejection",
        "frozen_sources_match": all(sha(REPO / name) == digest
                                    for name, digest in plan["source_sha256"].items()),
        "runner_error": error, "report_incomplete": "passed" not in report,
        "pre_click_v1_score": before,
        "visual_posthoc": {
            "source": red_support(ROOT / "001.png", plan["planner_roi"]),
            "pre_admission": red_support(ROOT / "003.png", plan["planner_roi"]),
            "first_feedback": red_support(ROOT / "004.png", plan["planner_roi"]),
            "pre_admission_dark_sides": dark_sides(ROOT / "003.png", source_plan["target"]["bbox"]),
            "first_feedback_dark_sides": dark_sides(ROOT / "004.png", source_plan["target"]["bbox"]),
        },
        "execution": {"acceptances": len([row for row in events if row.get("event") == "accepted"]),
            "candidate_click_completed": any(row.get("event") == "step_completed" and
                row.get("step") == 0 for row in selection_events),
            "observe_started": any(row.get("event") == "step_started" and
                row.get("step") == 1 for row in selection_events),
            "terminal": terminal},
        "interpretation": "fault click had already selected the target before candidate admission; selection overlays change exact red support; frozen scorer raised, then harness cleanup cancelled the running observe",
        "next_condition": "fault on neutral canvas; tolerant target-support identity plus selection handles; preserve v1 and freeze a new allocation",
        "retry_count": 0, "model_calls": 0}
    (ROOT / "failure.json").write_text(json.dumps(failure, indent=2) + "\n")
    print(json.dumps(failure, indent=2)); return 0

if __name__ == "__main__": raise SystemExit(main())
