"""Pure positive, translation and refusal probes for path-derived boxes."""
import json

from target_guard_from_paths_v1 import derive


FIRST = [{"x": 705, "y": 239}, {"x": 673, "y": 255}, {"x": 641, "y": 271}]
SECOND = [{"x": 641, "y": 278}, {"x": 673, "y": 294}, {"x": 705, "y": 310}]


def refused(first=FIRST, second=SECOND, **kwargs):
    try:
        derive(first, second, **kwargs)
    except ValueError as error:
        return str(error)
    raise AssertionError("refusal expected")


def main():
    base = derive(FIRST, SECOND)
    assert base["target_boxes"] == [
        [699, 235, 12, 8], [667, 251, 12, 8], [635, 267, 12, 8]]
    assert base["guard_boxes"] == [[667, 290, 12, 8], [699, 306, 12, 8]]
    assert base["derivation"]["shared_corner_offset"] == [0, 7]
    shifted_first = [{"x": point["x"] + 41, "y": point["y"] - 23} for point in FIRST]
    shifted_second = [{"x": point["x"] + 41, "y": point["y"] - 23} for point in SECOND]
    shifted = derive(shifted_first, shifted_second)
    assert shifted["target_boxes"] == [
        [box[0] + 41, box[1] - 23, box[2], box[3]] for box in base["target_boxes"]]
    assert shifted["guard_boxes"] == [
        [box[0] + 41, box[1] - 23, box[2], box[3]] for box in base["guard_boxes"]]
    report = {
        "probe_passed": True,
        "base": base,
        "translation_equivariant": True,
        "refusals": {
            "distant_corner": refused(second=[{"x": 641, "y": 280}, *SECOND[1:]]),
            "duplicate_first": refused(first=[FIRST[0], FIRST[0]]),
            "missing_coordinate": refused(first=[{"x": 1}, {"x": 2, "y": 2}]),
            "noninteger": refused(first=[{"x": 1.5, "y": 1}, {"x": 2, "y": 2}]),
            "oversized_box": refused(box_width=129),
            "overlap": refused(
                first=[{"x": 10, "y": 10}, {"x": 14, "y": 10}],
                second=[{"x": 14, "y": 10}, {"x": 18, "y": 10}],
                shared_corner_tolerance=0),
        },
        "scope": "pure pointer-plan geometry only; no pixels, application input, semantic success or generalization claim",
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
