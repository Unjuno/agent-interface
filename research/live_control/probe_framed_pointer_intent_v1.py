"""Probe framed pointer and target/guard resolution without application input."""
import json

from framed_pointer_intent_v1 import resolve_program


SOURCE = [129, 40, 1024, 720]
TARGET = {"focus": 11, "surface": 22, "geometry": [65, 40, 1152, 720]}


def refuses(call):
    try:
        call()
    except ValueError as error:
        return str(error)
    raise AssertionError("invalid framed program was accepted")


def main():
    program = [
        {"op": "pointer_click_in_frame", "coordinate_frame": "screen_chrome",
         "source_geometry": SOURCE, "x": 820, "y": 51},
        {"op": "pointer_drag_in_frame", "coordinate_frame": "window_content",
         "source_geometry": SOURCE,
         "points": [{"x": 705, "y": 239}, {"x": 641, "y": 271}],
         "duration_ms": 600},
        {"op": "local_target_guard_postcondition_in_frame",
         "coordinate_frame": "window_content", "source_geometry": SOURCE,
         "postcondition_id": "probe", "source_sequence": 3,
         "target_boxes": [[699, 235, 12, 8]], "guard_boxes": [[699, 306, 12, 8]],
         "pixel_delta_threshold": 24, "minimum_target_changed_pixels": 40,
         "maximum_guard_changed_pixels": 20, "required_samples": 2,
         "sample_interval_ms": 50, "timeout_ms": 500, "on_unmet": "needs_decision"},
        {"op": "observe"},
    ]
    prepared, records = resolve_program(program, TARGET)
    assert prepared[0] == {"op": "pointer_click", "x": 820, "y": 51}
    assert prepared[1]["points"] == [{"x": 641, "y": 239}, {"x": 577, "y": 271}]
    assert prepared[2]["target_boxes"] == [[635, 235, 12, 8]]
    assert prepared[2]["guard_boxes"] == [[635, 306, 12, 8]]
    assert [record["translation"] for record in records] == [[0, 0], [-64, 0], [-64, 0]]
    assert program[0]["op"] == "pointer_click_in_frame"
    report = {"probe_passed": True, "prepared": prepared,
        "resolution_records": records,
        "refusals": {
            "missing_binding": refuses(lambda: resolve_program(program, None)),
            "unknown_frame": refuses(lambda: resolve_program([
                {**program[0], "coordinate_frame": "map"}], TARGET)),
            "bad_source_geometry": refuses(lambda: resolve_program([
                {**program[0], "source_geometry": [0, 0, 0, 1]}], TARGET)),
            "extra_click_field": refuses(lambda: resolve_program([
                {**program[0], "unexpected": True}], TARGET)),
            "bad_box": refuses(lambda: resolve_program([
                {**program[2], "target_boxes": [[1, 2, 0, 4]]}], TARGET)),
        },
        "scope": "pure admission-time resolution only; no X11 input or automatic frame selection"}
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
