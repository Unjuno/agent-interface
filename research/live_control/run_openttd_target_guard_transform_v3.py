"""Use separate screen-chrome and viewport-content transforms."""
import json
from pathlib import Path

import run_openttd_target_guard_transform_v1 as implementation


HERE = Path(__file__).resolve().parent
implementation.OUT = HERE / "results/openttd-target-guard-transform-03"
implementation.DX = 0
implementation.DY = 0
content_dx, content_dy = -128, 0
implementation.FIRST = [
    {"x": point["x"] + content_dx, "y": point["y"] + content_dy}
    for point in implementation.BASE_FIRST]
implementation.CONTINUATION = [
    {"x": point["x"] + content_dx, "y": point["y"] + content_dy}
    for point in implementation.BASE_CONTINUATION]
original_run_case = implementation.run_case


def run_case(allocation):
    result = original_run_case(allocation)
    result["coordinate_frames"] = {
        "screen_chrome_translation": [0, 0],
        "viewport_content_translation": [content_dx, content_dy],
    }
    result.pop("translation", None)
    implementation.dump(implementation.OUT / allocation["name"] / "result.json", result)
    return result


implementation.run_case = run_case
implementation.main()
