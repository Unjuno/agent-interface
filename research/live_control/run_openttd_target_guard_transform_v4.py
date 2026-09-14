"""Replicate frame-specific transforms at a second held-out resolution."""
from pathlib import Path

import run_openttd_target_guard_transform_v1 as implementation


HERE = Path(__file__).resolve().parent
implementation.OUT = HERE / "results/openttd-target-guard-transform-04"
implementation.DX = 0
implementation.DY = 0
content_dx, content_dy = -64, 0
implementation.FIRST = [
    {"x": point["x"] + content_dx, "y": point["y"] + content_dy}
    for point in implementation.BASE_FIRST]
implementation.CONTINUATION = [
    {"x": point["x"] + content_dx, "y": point["y"] + content_dy}
    for point in implementation.BASE_CONTINUATION]
original_popen = implementation.subprocess.Popen
original_run_case = implementation.run_case


def popen(args, **kwargs):
    rewritten = list(args)
    for index, value in enumerate(rewritten):
        if str(value).endswith("pointer_socket_entry_v12.py"):
            rewritten[index] = str(HERE / "pointer_socket_entry_v13.py")
            break
    else:
        raise ValueError("missing transformed pointer entry")
    return original_popen(rewritten, **kwargs)


def run_case(allocation):
    result = original_run_case(allocation)
    result["resolution"] = "1152x720"
    result["coordinate_frames"] = {
        "screen_chrome_translation": [0, 0],
        "viewport_content_translation": [content_dx, content_dy],
    }
    result.pop("translation", None)
    implementation.dump(implementation.OUT / allocation["name"] / "result.json", result)
    return result


implementation.subprocess.Popen = popen
implementation.run_case = run_case
implementation.main()
